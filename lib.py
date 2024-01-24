from typing import List
from pyln.client import Plugin
import re
import os
import uuid
import json

# TODO: find a way to define this dynamically or decide that doesn't make sense to do
prism_plugin_version = "v0.0.2"

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
        self.name: str = member.get("name")
        self.destination: str = member.get("destination") #bolt12 or pubkey
        self.type = member.get("type")
        self.split: int = member.get("split")
        self.outlay: int = member.get("outlay")
        self.fees_incurred_by: str = member.get("fees_incurred_by")
        self.threshold: int = member.get("threshold")

    def to_json(self):
        return json.dumps({
            "name": self.name,
            "destination": self.destination,
            "split": self.split,
            "type": self.type,
            "fees_incurred_by": self.fees_incurred_by,
            "threshold": self.threshold
        })
    
    def to_dict(self):
        return {
            "name": self.name,
            "destination": self.destination,
            "split": self.split,
            "type": self.type,
            "fees_incurred_by": self.fees_incurred_by,
            "threshold": self.threshold
        }

    @staticmethod
    def validate(member):
        if not isinstance(member, dict):
            raise ValueError("Each member in the list must be a dictionary.")

        if not isinstance(member["name"], str):
            raise ValueError("Member 'name' must be a string.")

        if not isinstance(member["destination"], str):
            raise ValueError("Member 'destination' must be a string")

        # make sure destination is valid bolt12 or node pubkey
        valid_destination = None

        if bolt12Regex.match(member["destination"]):
            member["type"] = "bolt12"
        elif pubkeyRegex.match(member["destination"]):
            member["type"] = "keysend"
        else:
            raise Exception("Destination must be a valid lightning node pubkey or bolt12 offer")

        if not isinstance(member["split"], int):
            raise ValueError("Member 'split' must be an integer")

        if member["split"] < 1 or member["split"] > 1000:
            raise ValueError(
                "Member 'split' must be an integer between 1 and 1000")

        # TODO fees_incurred_by should be used in outlay calculations; valid are local/remote
        member['fees_incurred_by'] = member.get('fees_incurred_by', "remote")

        # TODO 
        member['threshold'] = member.get('threshold', 0)


        # TODO also check to see if the user provided MORE fields than is allowed.

# TODO: init Prism with the plugin instance, or maybe just plugin.rpc?
class Prism:
    def __init__(self, members: List[Member] = None, prism_id: str = None, prism_dict=None):
        if prism_dict:
            # TODO: validate the prism_dict
            self.id = prism_dict.get('prism_id')  
            self.version = prism_dict.get('version')  
            self.sdf = prism_dict.get('sdf')  
            member_dicts = prism_dict.get('members')
            self.members = [Member(m) for m in member_dicts]
        else:
            self.validate(members)
            self.members = members
            self.version = prism_plugin_version
            self.sdf = 'relative' 
            self.id = prism_id if prism_id else str(uuid.uuid4())

        self._datastore_key = ["prism", "prism", self.id]

    @property
    def datastore_key(self):
        return self._datastore_key
    
    def to_json(self):
        return json.dumps({
            "prism_id": self.id,
            "version": self.version,
            "sdf": self.sdf,
            "members": [m.to_dict() for m in self.members]
        })
    
    def to_dict(self):
        return {
            "prism_id": self.id,
            "version": self.version,
            "sdf": self.sdf,
            "members": [m.to_dict() for m in self.members]
        }
    
    @staticmethod
    def find_unique(plugin: Plugin, id: str):
        # TODO: make this "base" key a variable
        key = ["prism", "prism", id]

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
        key = ["prism", "prism"]
        prism_records = plugin.rpc.listdatastore(key=key).get("datastore", [])

        # parse and return all prisms as dicts
        return [json.loads(record['string']) for record in prism_records]

    @staticmethod
    def validate(members):
        if len(members) < 1:
            raise ValueError("Prism must contain at least one member.")

        if not isinstance(members, list):
            raise ValueError("Members must be a list.")



class PrismBinding:
    def __init__(self, offer_id, prism_ids):
        self.id = offer_id
        self.prism_ids = prism_ids
        self._datastore_key = ["prism", "bind", self.id]

    @property
    def datastore_key(self):
        return self._datastore_key
    

    def to_dict(self):
        return {
            "offer_id": self.offer_id, 
            "prism_ids": self.prism_ids
        }

    def to_json(self):
    # this method finds any prismbindings in the db then returns one and only
    # one PrismBinding object. Note this function isn't super efficient due to the
    # prism_bindings in the db being keyed on offer_id rather than prism_id. 
    # this function takes a prism ID and returns the assocaited PrismBinding object
    @staticmethod
    def get_prism_offer_binding(plugin: Plugin, prism_id: str, bolt_version="bolt12"):

        #prism_binding = None

        # so, need to pull all prism binding records and iterate over each one
        # to see if it contains the current prism_id is the content of the record.
        # this seems odd; but required since invoice_payment
        prism_records_key = [ "prism", "bind", bolt_version ]

        #plugin.log(f"prism_records_key: {prism_records_key}")

        prism_binding_records = plugin.rpc.listdatastore(key=prism_records_key)["datastore"]

        #plugin.log(f"prism_binding_records: {prism_binding_records}")

        relevant_offer_ids_for_prism = []
        prism_binding = None
        offer_id = None

        for binding_record in prism_binding_records:
            list_of_prisms_in_binding_record = json.dumps(binding_record["string"])
            #plugin.log(f"list_of_prisms_in_binding_record: {list_of_prisms_in_binding_record}")
            
            if prism_id in list_of_prisms_in_binding_record:
                offer_id = binding_record["key"][3]
                relevant_offer_ids_for_prism.append(offer_id)

        plugin.log(f"get_binding->offer_id: {offer_id}")
        plugin.log(f"get_binding->relevant_offer_ids_for_prism: {relevant_offer_ids_for_prism}")
        plugin.log(f"get_binding->bolt_version: {bolt_version}")

        prism_binding = PrismBinding(offer_id=offer_id, prism_ids=relevant_offer_ids_for_prism, bolt_version=bolt_version)

        plugin.log(f"get_binding->prism_binding: {prism_binding.to_dict()}")
            
        return prism_binding