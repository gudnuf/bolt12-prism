try:
    from typing import List
    from pyln.client import Plugin, Millisatoshi, RpcError
    import re
    import os
    import uuid
    import json
    import math
    import time
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

        if not isinstance(member["label"], str):
            raise ValueError("Member 'label' must be a string.")

        if not isinstance(member["destination"], str):
            raise ValueError("Member 'destination' must be a string")

        if not bolt12Regex.match(member["destination"]) and not pubkeyRegex.match(member["destination"]):
            raise Exception(
                "Destination must be a valid lightning node pubkey or bolt12 offer.")

        if not isinstance(member["split"], int):
            raise ValueError("Member 'split' must be an integer")

        if member["split"] < 1 or member["split"] > 1000:
            raise ValueError(
                "Member 'split' must be an integer between 1 and 1000")

        # TODO fees_incurred_by should be used in outlay calculations; valid are local/remote
        member['fees_incurred_by'] = member.get('fees_incurred_by', "remote")

        # TODO
        member['payout_threshold'] = member.get('payout_threshold', 0)

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

        self.id = member_dict.get("member_id") if member_dict.get(
            "member_id") else str(uuid.uuid4())
        self.label: str = member_dict.get("label")
        self.destination: str = member_dict.get("destination")
        self.split: str = member_dict.get("split")
        self.fees_incurred_by: str = member_dict.get(
            "fees_incurred_by") if member_dict.get("fees_incurred_by") else "remote"
        self.payout_threshold: Millisatoshi = Millisatoshi(member_dict.get(
            "payout_threshold")) if member_dict.get("payout_threshold") else Millisatoshi(0)

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
            "label": self.label,
            "destination": self.destination,
            "split": self.split,
            # TODO: shold this be at the prism level instead?
            "fees_incurred_by": self.fees_incurred_by,
            "payout_threshold": self.payout_threshold
        })

    def to_dict(self):
        return {
            "member_id": self.id,
            "label": self.label,
            "destination": self.destination,
            "split": self.split,
            "fees_incurred_by": self.fees_incurred_by,
            "payout_threshold": self.payout_threshold
        }

class Prism:
    @staticmethod
    def datastore_key(id):
        return ["prism", prism_db_version, "prism", id]

    @staticmethod
    def from_db_string(plugin: Plugin, prism_string: str):
        prism_dict = json.loads(prism_string)

        prism_id = prism_dict.get("prism_id")

        members = Member.find_many(plugin, prism_dict.get("prism_members"))

        timestamp = prism_dict.get("timestamp", 0)

        return Prism(plugin, timestamp=timestamp, prism_id=prism_id, members=members)

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
    def create(plugin: Plugin, prism_id: str = None, members: List[Member] = None):
        timestamp = round(time.time())
        prism = Prism(plugin, timestamp=timestamp, prism_id=prism_id, members=members)
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

        self._plugin.log(f'This prism\'s bindings: {our_bindings}')

        return our_bindings

    def __init__(self, plugin: Plugin, timestamp: str, prism_id: str = None, members: List[Member] = None):
        self.validate(members)
        self.members = members
        self.id = prism_id if prism_id else str(uuid.uuid4())
        self.timestamp = timestamp
        self._plugin = plugin

    def to_json(self, member_ids_only=False):
        members = []
        if member_ids_only:
            members = [member.id for member in self.members]
        else:
            members = [member.to_dict() for member in self.members]
        return json.dumps({
            "prism_id": self.id,
            "timestamp": self.timestamp,
            "prism_members": members
        })

    def to_dict(self):
        return {
            "prism_id": self.id,
            "timestamp": self.timestamp,
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
                member_msat = math.floor(amount_msat * (m.split / self.total_splits))
                self._plugin.log(f"In Prism.pay, but no binding was provided. Setting member_msat to {member_msat}")
                #self._plugin.log(f"member_msat {member_msat} ")
            else:
                # but if the user provids a binding object, then we set the member_msat to the
                # outlay for the respective prism member.
                member_msat = binding.outlays[m.id]
                self._plugin.log(f"In Prism.pay, and a binding was provided. Setting member_msat to the member's outlay: {member_msat}")

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
            elif pubkeyRegex.match(m.destination):
                try:
                    self._plugin.log(f"Attempting keysend payment for {member_msat}msats to node with pubkey {m.destination}", 'debug')
                    payment = self._plugin.rpc.keysend(destination=m.destination, amount_msat=member_msat)
                    self._plugin.log(f"keysend_payment:  {payment}")
                except RpcError as e:
                    self._plugin.log(f"Prism member keysend payment did not complete:  {e}", 'warn')

            if payment is not None:
                results[m.id] = payment
            else:
                results[m.id] = None

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
        if not prism:
            raise Exception(f"Could not find prism: {prism_id}")
        members = prism.members

        if not prism:
            raise Exception(f"Could not find prism: {prism_id}")
        timestamp = round(time.time())

        binding_value = {
            "prism_id": prism_id,
            "timestamp": timestamp,
            "member_outlays": {member.id: "0msat" for member in members}
        }

        # save the record
        plugin.rpc.datastore(key=prism_binding_key, string=json.dumps(
            binding_value), mode=f"{dbmode}")

        response = {
            "status": dbmode,
            "timestamp": timestamp,
            "bind_to": bind_to,
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
        return {
            "offer_id": self.offer_id,
            "prism_id": self.prism.id,
            "timestamp": self.timestamp,
            "member_outlays": self.outlays
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

            new_amount = Millisatoshi(outlay) + Millisatoshi(member_msat)

            self._plugin.log(
                f"Updating member {member_id} outlay to {new_amount}")

            new_outlays[member_id] = new_amount

        self.outlays = new_outlays

        self.save()

    def update_outlays(self, payment_results):
        new_outlays = {}
        for member_id, outlay in self.outlays.items():
            payment_amount = 0
            payment_result = payment_results.get(member_id, None)

            if payment_result:
                status = payment_result["status"]
                if status != "complete":
                    self._plugin.log(f"Failed to pay member {member_id}")
                    new_outlays[member_id] = outlay
                    continue
            
                payment_amount = payment_result.get("amount_sent_msat", 0)
            else:
                self._plugin.log(f"No payment_result for member {member_id}. This could indicate a failed payment.", "warn")

            new_outlay = Millisatoshi(outlay) - Millisatoshi(payment_amount)

            new_outlays[member_id] = new_outlay

        self._plugin.log(f"New outlay values after decrementing: {new_outlays}")
        self.outlays = new_outlays

        self.save()

    def pay(self, amount_msat):

        payment_results = None
        self.increment_outlays(amount_msat=amount_msat)

        # TODO we need to narrow the gap between these two functions.
        payment_results = self.prism.pay(amount_msat, binding=self)
        self.update_outlays(payment_results)

        self._plugin.log(f"PAYMENT RESULTS: {payment_results}", 'debug')

        return True
