from typing import List
from pyln.client import Plugin
import re
import os
import uuid
import json

# TODO: find a way to define this dynamically or decide that doesn't make sense to do
prism_plugin_version = "v2"

pubkeyRegex = re.compile(r'^0[2-3][0-9a-fA-F]{64}$')
bolt12Regex = re.compile(r'^ln([a-zA-Z0-9]{1,90})[0-9]+[munp]?[a-zA-Z0-9]+[0-9]+[munp]?[a-zA-Z0-9]*$')

plugin_out = "/tmp/plugin_out"
if os.path.isfile(plugin_out):
    os.remove(plugin_out)

# use this for debugging
def printout(s):
    with open(plugin_out, "a") as output:
        output.write(s)
        output.write('\n\n')

class Member:
    def __init__(self, member):
        self.validate(member)
        self.id: str = str(uuid.uuid4())
        self.label: str = member.get("label")
        self.destination: str = member.get("destination") #bolt12 or pubkey
        self.split: int = member.get("split")
        self.fees_incurred_by: str = member.get("fees_incurred_by")
        self.payout_threshold: int = member.get("payout_threshold")

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

    @staticmethod
    def validate(member):
        if not isinstance(member, dict):
            raise ValueError("Each member in the list must be a dictionary.")

        if not isinstance(member["label"], str):
            raise ValueError("Member 'label' must be a string.")

        if not isinstance(member["destination"], str):
            raise ValueError("Member 'destination' must be a string")

        if not bolt12Regex.match(member["destination"]) and not pubkeyRegex.match(member["destination"]):
            raise Exception("Destination must be a valid lightning node pubkey or bolt12 offer.")

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

# TODO: init Prism with the plugin instance, or maybe just plugin.rpc?
class Prism:
    def __init__(self, prism_id: str = None, members: List[Member] = None):
        self.validate(members)
        self.members = members
        self.id = prism_id if prism_id else str(uuid.uuid4())
        self._datastore_key = ["prism", prism_plugin_version, "prism", self.id]

    @property
    def datastore_key(self):
        return self._datastore_key
    
    def to_json(self):
        return json.dumps({
            "prism_id": self.id,
            "members": [m.to_dict() for m in self.members]
        })
    
    def to_dict(self):
        return {
            "prism_id": self.id,
            "members": [m.to_dict() for m in self.members]
        }
    
    # this record save a Prism object to the database.
    # these records are stored under prism,prism_version,prism,prism_id_a,member_id_a_ii
    def save(self, plugin):
        plugin.log(f"got into save()")

        for member in self.members:
            member_key = ["prism", prism_plugin_version, "prism", self.id, member.id]
            plugin.log(f"member_key: {member_key}")
            plugin.log(f"member.to_json(): {member.to_json()}")
            plugin.rpc.datastore(key=member_key, string=member.to_json(), mode="create-or-replace")

    @staticmethod
    def find_unique(plugin: Plugin, id: str):
        # TODO: make this "base" key a variable
        key = ["prism", prism_plugin_version, "prism", id]

        #find prism in datastore by ID
        try:
            prism_json = plugin.rpc.listdatastore(key=key).get("datastore", [])[0]["string"]
        except:
            return None
        
        # convert prism to json
        prism_dict = json.loads(prism_json)

        return Prism(prism_dict=prism_dict)

    @staticmethod
    def find_all(plugin: Plugin):
        key = ["prism", prism_plugin_version, "prism"]
        prism_records = plugin.rpc.listdatastore(key=key).get("datastore", [])

        # parse and return all prisms as dicts
        return [json.loads(record['string']) for record in prism_records] 

    @staticmethod
    def validate(members):
        if len(members) < 1:
            raise ValueError("Prism must contain at least one member.")

        if not isinstance(members, list):
            raise ValueError("Members must be a list.")



# class PrismBinding:
#     def __init__(self, offer_id, prism_id, bolt_version="bolt12"):
#         self.offer_id = offer_id
#         self.bolt_version = bolt_version
#         self.prism_id = prism_id
#         self._datastore_key = ["prism", prism_plugin_version, "bind", self.offer_id]

#     @property
#     def datastore_key(self):
#         return self._datastore_key
    
#     def to_dict(self):
#         return {"offer_id": self.offer_id, "prism_id": self.prism_ids}

#     def to_json(self):
#         return {"offer_id": self.offer_id, "prism_id": self.prism_ids}

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
    #     prism_records_key = [ "prism", prism_plugin_version, "bind", bolt_version ]

    #     plugin.log(f"prism_records_key: {prism_records_key}")

    #     prism_binding_records = plugin.rpc.listdatastore(key=prism_records_key)["datastore"]

    #     plugin.log(f"prism_binding_records: {prism_binding_records}")

    #     relevant_offer_ids_for_prism = []
    #     prism_binding = None
    #     offer_id = None

    #     for binding_record in prism_binding_records:
    #         list_of_prisms_in_binding_record = json.dumps(binding_record["string"])
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


    # # is is the revers of the method above. It return all prism-bindings,
    # # but keyed on offer_id, as stored in the database.
    # @staticmethod
    # def get_offer_prismbindings(plugin: Plugin, prism_id: str, bolt_version="bolt12"):
        
    #     types = [ "bolt11", "bolt12" ]
    #     if bolt_version not in types:
    #         raise Exception("ERROR: 'type' MUST be either 'bolt12' or 'bolt11'.")

    #     prism_binding_key = [ "prism", prism_plugin_version, "bind", bolt_version ]
    #     prism_bindings = plugin.rpc.listdatastore(key=prism_binding_key)["datastore"]

    #     #plugin.log(f"prism_bindings: {prism_bindings}")

    #     # Extract the 'string' property and parse it as JSONa
    #     prism_binding_objects = []

    #     for binding in prism_bindings:
    #         prism_binding = PrismBinding(binding['key'][3], list(json.loads(binding['string'])))
    #         prism_binding_objects.append(prism_binding)

    # return prism_binding_objects


    # # is is the revers of the method above. It return all prism-bindings,
    # # but keyed on offer_id, as stored in the database.
    # @staticmethod
    # def add_binding(plugin: Plugin, prism_id: str, offer_id: str, outlay=0, bolt_version="bolt12"):
        
    #     dbmode="must-create"

    #     # first we need to see if there are any existing binding records for this prism_id/invoice_type
    #     prism_binding_key = [ "prism", prism_plugin_version, "bind", bolt_version, offer_id, prism_id ]
    #     plugin.log(f"binding_key: {prism_binding_key}")

    #     binding_record = plugin.rpc.listdatastore(key=prism_binding_key)["datastore"]
 
    #     # if the record already exists, we adjust the dbmode.
    #     if len(binding_record) > 0:
    #         # oh, the record already exists. If if s
    #         dbmode = "must-replace"

    #     # save the record
    #     val = plugin.rpc.datastore(key=prism_binding_key, string=f"{outlay}", mode=dbmode)

    #     response = {
    #         "status": dbmode,
    #         "offer_id": offer_id,
    #         "prism_id": prism_id,
    #         "prism_binding_key": prism_binding_key }

    #     return response

    # # 
    # @staticmethod
    # def list_offer_prism_bindings(plugin, bolt_version="bolt12"):
    #     types = [ "bolt11", "bolt12" ]
    #     if bolt_version not in types:
    #         raise Exception("ERROR: 'type' MUST be either 'bolt12' or 'bolt11'.")

    #     prism_binding_key = [ "prism", prism_plugin_version, "bind", bolt_version ]
    #     prism_bindings = plugin.rpc.listdatastore(key=prism_binding_key)["datastore"]

    #     plugin.log(f"prism_bindings: {prism_bindings}")

    #     prism_binding_objects = []
    #     for binding in prism_bindings:
    #         offer_id = binding['key'][3]
    #         prism_binding = PrismBinding.get_offer_prism_bindings(plugin, offer_id=offer_id, bolt_version=bolt_version)
    #         prism_binding_objects.append(prism_binding)

    #     plugin.log(f"prism_binding_objects: {prism_binding_objects}")

    #     return prism_bindings
