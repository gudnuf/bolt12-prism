from typing import List
from pyln.client import Plugin, Millisatoshi
import re
import os
import uuid
import json

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

    def to_json(self):
        return json.dumps({
            "member_id": self.id,
            "label": self.label,
            "destination": self.destination,
            "split": self.split,
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

    @property
    def datastore_key(self):
        return self._datastore_key

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

    # this static method returns a list of Members for a given prism_id
    # the result of which can be used in the Prism Constructor.

    @staticmethod
    def get_prism_members(plugin: Plugin, prism_id):
        prism_key = ["prism", prism_db_version, "prism", prism_id]
        member_records = plugin.rpc.listdatastore(
            key=prism_key).get("datastore")

        members = []

        for member_record in member_records:
            member_dict = json.loads(member_record['string'])
            member = Member(prism_id=prism_id, member_dict=member_dict)
            members.append(member)

        return members

# TODO: init Prism with the plugin instance, or maybe just plugin.rpc?


class Prism:
    def __init__(self, prism_id: str = None, members: List[Member] = None):
        self.validate(members)
        self.members = members
        self.id = prism_id if prism_id else str(uuid.uuid4())

    @staticmethod
    def datastore_key(id):
        return ["prism", prism_db_version, "prism", id]

    def to_json(self, member_ids_only=False):
        members = []
        if member_ids_only:
            members = [member.id for member in self.members]
        else:
            members = [member.to_dict() for member in self.members]
        return json.dumps({
            "prism_id": self.id,
            "prism_members": members
        })

    def to_dict(self):
        return {
            "prism_id": self.id,
            "prism_members": [member.to_dict() for member in self.members]
        }

    # save a Prism object and members to the database.
    # these records are stored under prism,prism_version,prism,prism_id_a

    def save(self, plugin):
        plugin.log(f"Saving prism: {self.id}")

        # save each prism member
        for member in self.members:
            member.save()

        # save the prism
        plugin.rpc.datastore(key=self.datastore_key(id=self.id),
                             string=self.to_json(member_ids_only=True), mode="create-or-replace")

    @staticmethod
    def from_db_string(plugin: Plugin, prism_string: str):
        prism_dict = json.loads(prism_string)

        prism_id = prism_dict.get("prism_id")

        members = Member.find_many(plugin, prism_dict.get("prism_members"))

        return Prism(prism_id=prism_id, members=members)

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
    def validate(members):
        if len(members) < 1:
            raise ValueError("Prism must contain at least one member.")

        if not isinstance(members, list):
            raise ValueError("Members must be a list.")


class PrismBinding:
    def __init__(self, offer_id, prism_id, bolt_version="bolt12", binding_dict=None):

        self.offer_id = offer_id
        self.bolt_version = bolt_version
        self.prism_id = prism_id
        self.members = None

        if binding_dict:
            self.offer_id = binding_dict.get("offer_id")
            self.members = binding_dict

        self._datastore_key = ["prism", prism_db_version,
                               "bind", bolt_version, offer_id]

    @property
    def datastore_key(self):
        return self._datastore_key

    def to_dict(self):
        return {
            "offer_id": self.offer_id,
            "prism_id": self.prism_id,
        }

    def to_json(self):
        return {
            "offer_id": self.offer_id,
            "prism_id": self.prism_id
        }

    # # this method finds any prismbindings in the db then returns one and only
    # # one PrismBinding object. Note this function isn't super efficient due to the
    # # prism_bindings in the db being keyed on offer_id rather than prism_id.
    # # this function takes a prism ID and returns the assocaited PrismBinding object
    # @staticmethod
    # def get_prism_offer_binding(plugin: Plugin, prism_id: str, bolt_version="bolt12"):

    #     prism_binding = None

    #     # so, need to pull all prism binding records and iterate over each one
    #     # to see if it contains the current prism_id is the content of the record.
    #     # this seems odd; but required since invoice_payment
    #     prism_records_key = [ "prism", prism_db_version, "bind", bolt_version ]

    #     plugin.log(f"prism_records_key: {prism_records_key}")

    #     prism_binding_records = plugin.rpc.listdatastore(key=prism_records_key)["datastore"]

    #     plugin.log(f"prism_binding_records: {prism_binding_records}")

    #     relevant_offer_ids_for_prism = []
    #     prism_binding = None
    #     offer_id = None

    #     for binding_record in prism_binding_records:
    #         list_of_prisms_in_binding_record = json.dumps(binding_record['string'])
    #         plugin.log(f"list_of_prisms_in_binding_record: {list_of_prisms_in_binding_record}")

    #         if prism_id in list_of_prisms_in_binding_record:
    #             offer_id = binding_record["key"][3]
    #             relevant_offer_ids_for_prism.append(offer_id)

    #     plugin.log(f"get_binding->offer_id: {offer_id}")
    #     plugin.log(f"get_binding->relevant_offer_ids_for_prism: {relevant_offer_ids_for_prism}")
    #     plugin.log(f"get_binding->bolt_version: {bolt_version}")

    #     prism_binding = PrismBinding(offer_id=offer_id, prism_ids=relevant_offer_ids_for_prism, bolt_version=bolt_version)

    #     plugin.log(f"get_binding->prism_binding: {prism_binding.to_dict()}")

    #     return prism_binding

    # this method shows the current state of  a specific binding.
    # bindings are

    @staticmethod
    def get(plugin: Plugin, bind_to: str, bolt_version="bolt12"):

        plugin.log(f"got into get_binding_state.")
        plugin.log(f"bind_to: {bind_to}'")

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
                f"Could not find a prism binding for offer {bind_to}")

        # load the JSON string from the db.
        binding_state = json.loads(binding_records[0]['string'])

        return binding_state

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
            # oh, the record already exists. If if s
            dbmode = "must-replace"

        prism = Prism.get(plugin=plugin, prism_id=prism_id)
        if not prism:
            raise Exception(f"Could not find prism: {prism_id}")
        members = prism.members

        if not prism:
            raise Exception(f"Could not find prism: {prism_id}")

        binding_value = {
            "prism_id": prism_id,
            "member_outlays": {member.id: "0msat" for member in members}
        }

        # save the record
        plugin.rpc.datastore(key=prism_binding_key, string=json.dumps(
            binding_value), mode=f"{dbmode}")

        response = {
            "status": dbmode,
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
            plugin.log(f"offer_id: {offer_id}")
            binding_record_value_dict = json.loads(binding_record['string'])
            prism_id = binding_record_value_dict["prism_id"]
            binding = PrismBinding(
                offer_id=offer_id, prism_id=prism_id, bolt_version=bolt_version)
            bindings.append(binding)

        return bindings
