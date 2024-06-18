try:
    from typing import List
    from pyln.client import Plugin, RpcError
    import re
    import os
    import uuid
    import json
    import math
    import time
    import hashlib
except ModuleNotFoundError as err:
    # OK, something is not installed?
    import json
    import sys
    getmanifest = json.loads(sys.stdin.readline())
    print(json.dumps({'jsonrpc': "2.0",
                      'id': getmanifest['id'],
                      'result': {'disable': str(err)}}))
    sys.exit(1)

# TODO: find a way to define this dynamically or decide that doesn't make sense to do
prism_db_version = "v2"

pubkeyRegex = re.compile(r'^0[2-3][0-9a-fA-F]{64}$')
bolt12Regex = re.compile(
    r'^ln([a-zA-Z0-9]{1,90})[0-9]+[munp]?[a-zA-Z0-9]+[0-9]+[munp]?[a-zA-Z0-9]*$')

plugin_out = "/tmp/plugin_out"
if os.path.isfile(plugin_out):
    os.remove(plugin_out)


class Member:
    @staticmethod
    def validate(member):
        if not isinstance(member, dict):
            raise ValueError("Each member in the list must be a dictionary.")

        if not isinstance(member["description"], str):
            raise ValueError("Member 'description' must be a string.")

        if not isinstance(member["destination"], str):
            raise ValueError("Member 'destination' must be a string")

        if not bolt12Regex.match(member["destination"]) and not pubkeyRegex.match(member["destination"]):
            raise Exception(
                "Destination must be a valid lightning node pubkey or bolt12 offer.")

        if not isinstance(member["split"], float):
            raise ValueError("Member 'split' must be an float (e.g., 2.0)")

        member['fees_incurred_by'] = member.get('fees_incurred_by', "remote")

        # TODO
        member['payout_threshold_msat'] = member.get('payout_threshold_msat', 0)

        # TODO also check to see if the user provided MORE fields than is allowed.

    @staticmethod
    def get(plugin: Plugin, member_id: str):
        member_record = plugin.rpc.listdatastore(
            key=["prism", prism_db_version, "member", member_id])["datastore"]

        if not member_record:
            return None

        member_dict = json.loads(member_record[0]["string"])
        return Member(plugin, member_dict)

    @staticmethod
    def find_many(plugin: Plugin, member_ids: List[str]):
        members = []
        for member_id in member_ids:
            member = Member.get(plugin, member_id)
            if member:
                members.append(member)
            else:
                raise Exception(f"Could not find member: {member_id}")
        return members

    @property
    def datastore_key(self):
        return self._datastore_key

    def __init__(self, plugin: Plugin, member_dict=None):
        self.validate(member_dict)
        self.description: str = member_dict.get("description")
        self.destination: str = member_dict.get("destination")
        self.split: float = member_dict.get("split")
        if self.split <= 0:
            raise Exception("The split MUST be a positive number (e.g., 2.0)")
        self.fees_incurred_by: str = member_dict.get(
            "fees_incurred_by") if member_dict.get("fees_incurred_by") else "remote"
        self.payout_threshold_msat: int = int(member_dict.get(
            "payout_threshold_msat")) if member_dict.get("payout_threshold_msat") else int(0)

        self._plugin = plugin

        self._datastore_key = ["prism", prism_db_version, "member", self.id]

    def save(self):
        self._plugin.log(f"Saving member: {self.id}")
        self._plugin.rpc.datastore(
            key=self._datastore_key, string=self.to_json(), mode="create-or-replace")

    def delete(self):
        self._plugin.log(f"Deleting member: {self.id}")
        self._plugin.rpc.deldatastore(key=self._datastore_key)

    def to_json(self):
        return json.dumps({
            "member_id": self.id,
            "description": self.description,
            "destination": self.destination,
            "split": self.split,
            # TODO: shold this be at the prism level instead?
            "fees_incurred_by": self.fees_incurred_by,
            "payout_threshold_msat": self.payout_threshold_msat
        })

    def to_dict(self):
        return {
            "member_id": self.id,
            "description": self.description,
            "destination": self.destination,
            "split": self.split,
            "fees_incurred_by": self.fees_incurred_by,
            "payout_threshold_msat": self.payout_threshold_msat
        }

class Prism:
    @staticmethod
    def datastore_key(id):
        return ["prism", prism_db_version, "prism", id]

    @staticmethod
    def from_db_string(plugin: Plugin, prism_string: str):
        prism_dict = json.loads(prism_string)

        prism_id = prism_dict.get("prism_id")

        description = prism_dict.get("description")

        members = Member.find_many(plugin, prism_dict.get("prism_members"))

        timestamp = prism_dict.get("timestamp")

        outlay_factor = prism_dict.get("outlay_factor")

        return Prism(plugin, outlay_factor=outlay_factor, description=description, timestamp=timestamp, members=members)
    
    @staticmethod
    def get(plugin: Plugin, prism_id: str):
        prism_record = plugin.rpc.listdatastore(
            key=Prism.datastore_key(id=prism_id))["datastore"]

        if not prism_record:
            return None

        return Prism.from_db_string(plugin, prism_record[0]["string"])

    @staticmethod
    def find_all(plugin: Plugin):
        key = ["prism", prism_db_version, "prism"]
        prism_records = plugin.rpc.listdatastore(key=key).get("datastore", [])

        prism_ids = []
        for prism in prism_records:
            prism_id = prism["key"][3]
            prism_ids.append(prism_id)

        return prism_ids
    
    @staticmethod
    def create(plugin: Plugin, outlay_factor, description: str = None, members: List[Member] = None):
        timestamp = round(time.time())
        prism = Prism(plugin, timestamp=timestamp, description=description, members=members, outlay_factor=outlay_factor)
        prism.save()
        return prism


    @staticmethod
    def validate(members):
        if len(members) < 1:
            raise ValueError("Prism must contain at least one member.")

        if not isinstance(members, list):
            raise ValueError("Members must be a list.")

    @property
    def total_splits(self) -> int:
        """sum each members split"""
        return sum([m.split for m in self.members])
    
    @property
    def bindings(self):
        all_bindings = PrismBinding.list_binding_offers(plugin=self._plugin)

        our_bindings = [b for b in all_bindings if b.prism.id == self.id]

        self._plugin.log(f"This prism's bindings: {our_bindings}")

        return our_bindings

    def __init__(self, plugin: Plugin, outlay_factor: float, timestamp: str, description: str = "", members: List[Member] = None):

        self.validate(members)
        self.members = members
        self.description = description
        self.timestamp = timestamp
        self.outlay_factor = outlay_factor
        self._plugin = plugin

    def to_json(self, member_ids_only=False):
        members = []
        if member_ids_only:
            members = [member.id for member in self.members]
        else:
            members = [member.to_dict() for member in self.members]
        return json.dumps({
            "prism_id": self.id,
            "description": self.description,
            "timestamp": self.timestamp,
            "outlay_factor": self.outlay_factor,
            "prism_members": members
        })

    def to_dict(self):
        return {
            "prism_id": self.id,
            "description": self.description,
            "timestamp": self.timestamp,
            "outlay_factor": self.outlay_factor,
            "prism_members": [member.to_dict() for member in self.members]
        }

    # save a Prism object and members to the database.
    # these records are stored under prism,prism_version,prism,prism_id_a

    def save(self):
        self._plugin.log(f"Saving prism: {self.id}")

        # TODO add a 'last_updated_timestamp' to prism data

        # save each prism member
        for member in self.members:
            member.save()

        # save the prism
        self._plugin.rpc.datastore(key=self.datastore_key(id=self.id),
                                   string=self.to_json(member_ids_only=True), mode="create-or-replace")
        
    def update(self, members: List[Member]):
        self._plugin.log(f"Updating prism: {self.id}")

        self.members = members

        self.save() 


    def delete(self):
        self._plugin.log(f"Deleting prism: {self.id}", "debug")

        # delete each prism member
        for member in self.members:
            self._plugin.log(f"About to call prism.member.delete() on member {member.id}", "debug")
            member.delete()

        # delete the prism
        rtnVal = self._plugin.rpc.deldatastore(key=self.datastore_key(id=self.id))

        return rtnVal

    def pay(self, amount_msat: int, binding = None):
        """
        Pay each member in the prism their respective share of `amount_msat`
        """

        results = {}

        for m in self.members:
            member_msat = 0

            if binding is None:
                # when a binding is not provided (when we're using prism.pay, for example)
                # the member_msat is set to the proportional share of defined in the split defintion
                member_msat = int(math.floor(amount_msat * (m.split / self.total_splits)))
                self._plugin.log(f"In Prism.pay, but no binding was provided, thus setting member_msat to a {member_msat}.")

            else:
                # but if the user provids a binding object, then we set the member_msat to the
                # outlay for the respective prism member.
                member_msat = int(binding.outlays[m.id])
                self._plugin.log(f"In Prism.pay, and a binding was provided. Setting member_msat to the member's outlay: {member_msat}")

                # we stop processing if the 
                if member_msat <= m.payout_threshold_msat:
                    self._plugin.log("Member outlay is less than the payout threshold. Skipping.")
                    continue

            payment = None
            if bolt12Regex.match(m.destination):
                try:
                    self._plugin.log(f"in prism.pay_bolt12regex", 'debug')
                    bolt12_invoice = self._plugin.rpc.fetchinvoice(offer=m.destination, amount_msat=member_msat)

                    invoice = bolt12_invoice.get("invoice")

                    if invoice is not None:
                        payment = self._plugin.rpc.pay(bolt11=invoice)
                        self._plugin.log(f"bolt12_payment:  {payment}")
                    else:
                        self._plugin.log(f"Could not fetch an invoice from the remote peer.", "warn")
                except RpcError as e:
                    self._plugin.log(f"Prism member bolt12 payment did not complete.:  {e}", 'warn')
                    continue
                except Exception as e:
                    self._plugin.log(f"Prism member bolt12 payment did not complete.:  {e}", 'warn')
                    continue

            elif pubkeyRegex.match(m.destination):
                try:
                    self._plugin.log(f"Attempting keysend payment for {member_msat}msats to node with pubkey {m.destination}", 'debug')
                    payment = self._plugin.rpc.keysend(destination=m.destination, amount_msat=member_msat)
                    self._plugin.log(f"keysend_payment:  {payment}")
                except RpcError as e:
                    self._plugin.log(f"Prism member bolt12 payment did not complete.:  {e}", 'warn')
                    continue
                except Exception as e:
                    self._plugin.log(f"Prism member keysend payment did not complete:  {e}", 'warn')
                    continue
            else:
                raise Exception("ERROR: The destination was an invalid format. This should never happen!")

            results[m.id] = None
            if payment is not None:
                results[m.id] = payment

                # if there's a binding, we update the outlay.
                if binding is not None:

                    status = payment["status"]
                    if status != "complete":
                        self._plugin.log(f"Failed to pay member {member_id}")
                        continue

                    # update the member outlay with the payment amount (respecting fee accounting)
                    total_amount_sent = payment["amount_sent_msat"]
                    total_amount_sent_minus_fees = payment["amount_msat"]

                    self._plugin.log(f"total_amount_sent: {total_amount_sent}", 'debug')
                    self._plugin.log(f"total_amount_sent_minus_fees: {total_amount_sent_minus_fees}", 'debug')

                    new_outlay = None
                    if m.fees_incurred_by == "remote":
                        new_outlay = member_msat - total_amount_sent
                        self._plugin.log(f"fees_incurred_by is set to remote. New outlay: {member_msat}-{total_amount_sent}={new_outlay}")
                    elif m.fees_incurred_by == "local":
                        new_outlay = member_msat - total_amount_sent_minus_fees
                        self._plugin.log(f"fees_incurred_by is set to local. New outlay is {new_outlay}")
                    else:
                        raise Exception("If this happens then we have some input validation issues.")

                    # now that we have the new outlay value, we need to persist it to the db
                    self._plugin.log(f"new_outlay: {new_outlay}", "debug")

                    binding.outlays[m.id] = new_outlay

                    # TODO this saves the entire prism bindings; we probably need something more
                    # precise that saves only the binding-member. But this works for now
                    binding.save()

        self._plugin.log(
            f"PRISM-PAY: ID={self.id}: {len(self.members)} members; {amount_msat} msat total", 'debug')

        return results

class PrismBinding:
    prism: Prism

    @staticmethod
    def delete(plugin: Plugin, bind_to: str, bolt_version="bolt12"):
        # TODO: below code is repeated from PrismBinding.get()
        types = ["bolt11", "bolt12"]
        if bolt_version not in types:
            raise Exception(
                "ERROR: 'type' MUST be either 'bolt12' or 'bolt11'.")

        bindings_key = ["prism", prism_db_version,
                        "bind", bolt_version, bind_to]

        binding_records = {}
        try:
            binding_records = plugin.rpc.deldatastore(
                key=bindings_key)
        except RpcError as e:
            plugin.log(f"ERROR DELETING: {e}", 'error')

        if not binding_records:
            raise Exception(
                f"Could not find a prism binding for offer {bind_to}")


        return binding_records

    @staticmethod
    def from_db_string(plugin: Plugin, string: str, bind_to: str, bolt_version: str):
        parsed = json.loads(string)

        prism_id = parsed.get('prism_id', None)
        member_outlays = parsed.get('member_outlays', None)
        timestamp = parsed.get('timestamp', 0)

        if not prism_id:
            raise Exception("Invalid binding. Missing prism_id")

        if not member_outlays:
            raise Exception("Invalid binding. Missing member_outlays")

        return PrismBinding(plugin, timestamp=timestamp, outlays=member_outlays, offer_id=bind_to, prism_id=prism_id, bolt_version=bolt_version)

    @staticmethod
    def get(plugin: Plugin, bind_to: str, bolt_version="bolt12"):

        types = ["bolt11", "bolt12"]
        if bolt_version not in types:
            raise Exception(
                "ERROR: 'type' MUST be either 'bolt12' or 'bolt11'.")

        bindings_key = ["prism", prism_db_version,
                        "bind", bolt_version, bind_to]

        binding_records = plugin.rpc.listdatastore(
            key=bindings_key).get("datastore", [])

        if not binding_records:
            raise Exception(
                f"Could not find: {bindings_key}")

        return PrismBinding.from_db_string(plugin, string=binding_records[0].get('string'), bind_to=bind_to, bolt_version=bolt_version)

    @staticmethod
    def set_member_outlay(binding: None, member_id: str, new_outlay_value=0):

        binding.outlays[member_id] = int(new_outlay_value)

        # TODO this saves the entire prism bindings; we probably need something more
        # precise that saves only the binding-member. But this works for now
        binding.save()

    # is is the revers of the method above. It return all prism-bindings,
    # but keyed on offer_id, as stored in the database.

    @staticmethod
    def add_binding(plugin: Plugin, bind_to: str, prism_id: str,  bolt_version="bolt12"):

        prism_binding_key = ["prism", prism_db_version,
                             "bind", bolt_version, bind_to]

        # first we need to see if there are any existing binding records for this prism_id/invoice_type
        # plugin.log(f"prism_binding_key: {prism_binding_key}")

        binding_record = plugin.rpc.listdatastore(
            key=prism_binding_key)["datastore"]
        dbmode = "must-create"

        # if the record already exists, we adjust the dbmode.
        if len(binding_record) > 0:
            # oh, the record already exists. switch to must-replace
            dbmode = "must-replace"

        prism = Prism.get(plugin=plugin, prism_id=prism_id)

        plugin.log(f"prism: {prism}")

        if not prism:
            raise Exception(f"Could not find prism: {prism_id}")
        members = prism.members

        if not prism:
            raise Exception(f"Could not find prism: {prism_id}")
        timestamp = round(time.time())

        binding_value = {
            "prism_id": prism_id,
            "timestamp": timestamp,
            "member_outlays": {member.id: 0 for member in members}
        }

        # save the record
        plugin.rpc.datastore(key=prism_binding_key, string=json.dumps(
            binding_value), mode=f"{dbmode}")

        response = {
            "status": dbmode,
            "timestamp": timestamp,
            "offer_id": bind_to,
            "prism_id": prism_id,
            "prism_binding_key": prism_binding_key,
            "prism_members": [member.to_dict() for member in members]
        }

        return response

    @staticmethod
    def list_binding_offers(plugin, bolt_version="bolt12"):
        types = ["bolt11", "bolt12"]
        if bolt_version not in types:
            raise Exception(
                "ERROR: 'type' MUST be either 'bolt12' or 'bolt11'.")

        bindings_key = ["prism", prism_db_version, "bind", bolt_version]

        binding_records = plugin.rpc.listdatastore(
            key=bindings_key).get("datastore", [])

        bindings = []

        for binding_record in binding_records:
            offer_id = binding_record["key"][4]
            #plugin.log(f"offer_id: {offer_id}")
            binding_record_str = binding_record['string']
            binding = PrismBinding.from_db_string(plugin, string=binding_record_str, bind_to=offer_id, bolt_version=bolt_version) 
            bindings.append(binding)

        return bindings

    @property
    def datastore_key(self):
        return self._datastore_key

    def __init__(self, plugin: Plugin, timestamp: int, outlays, offer_id, prism_id, bolt_version="bolt12", binding_dict=None):

        self._plugin = plugin
        self.offer_id = offer_id
        self.timestamp = timestamp
        self.bolt_version = bolt_version
        self.members = None

        self.prism = Prism.get(plugin, prism_id)
        self.outlays = outlays

        if binding_dict:
            self.offer_id = binding_dict.get("offer_id")
            self.timestamp = binding_dict.get("timestamp")
            self.members = binding_dict

        self._datastore_key = ["prism", prism_db_version,
                               "bind", bolt_version, offer_id]

    def to_dict(self):
        sha256 = hashlib.sha256()
        sha256.update(self.offer_id.encode('utf-8'))

        return {
            "offer_id": self.offer_id,
            "prism_id": self.prism.id,
            "timestamp": self.timestamp,
            "member_outlays": [
                {
                    "member_id": member_id, 
                    "outlay_msat": outlay
                } 
                for member_id, outlay in self.outlays.items() 
            ]
        }

    def to_json(self):
        return {
            "offer_id": self.offer_id,
            "prism_id": self.prism.id,
            "timestamp": self.timestamp
        }

    def save(self):
        string = json.dumps({
            "prism_id": self.prism.id,
            "timestamp": self.timestamp,
            "member_outlays": self.outlays
        })

        self._plugin.rpc.datastore(
            key=self._datastore_key, string=string, mode="must-replace")

    def increment_outlays(self, amount_msat):

        self._plugin.log(f"Incrementing outlays for binding '{self.offer_id}' with total income of {amount_msat}msats.")
        new_outlays = {}
        for member_id, outlay in self.outlays.items():
            # find member in the Prism by the member id in the outlays
            m = [m for m in self.prism.members if m.id == member_id][0]

            if not m:
                raise Exception(
                    f"Binding and prism in different states. Expected to find member {member_id} in prism {self.prism.id}")

            member_msat = math.floor(
                amount_msat * (m.split / self.prism.total_splits))

            new_amount = int(outlay) + int(member_msat)

            self._plugin.log(
                f"Updating member {member_id} outlay to {new_amount}")

            new_outlays[member_id] = new_amount

        self.outlays = new_outlays

        self.save()

    def pay(self, amount_msat):

        payment_results = None
        self._plugin.log(f"Calculating total outlays...")
        total_outlays = amount_msat * self.prism.outlay_factor
        self._plugin.log(f"Total outlays will be {total_outlays} after applying an outlay factor of {self.prism.outlay_factor} to the income amount {amount_msat}.")
        self.increment_outlays(amount_msat=total_outlays)
        payment_results = self.prism.pay(amount_msat, binding=self)
        self._plugin.log(f"PAYMENT RESULTS: {payment_results}", 'debug')

        return True
