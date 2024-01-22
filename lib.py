from typing import List
import re
import os
import uuid
import json

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
            "outlay_msat": self.outlay,
            "fees_incurred_by": self.fees_incurred_by,
            "threshold": self.threshold
        })
    
    def to_dict(self):
        return {
            "name": self.name,
            "destination": self.destination,
            "split": self.split,
            "type": self.type,
            "outlay_msat": self.outlay,
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

        # next, let's ensure the Member definition has the default fields.
        member['outlay_msat'] = member.get('outlay_msat', 0)

        # TODO fees_incurred_by should be used in outlay calculations; valid are local/remote
        member['fees_incurred_by'] = member.get('fees_incurred_by', "remote")

        # TODO 
        member['threshold'] = member.get('threshold', 0)


        # TODO also check to see if the user provided MORE fields than is allowed.

class Prism:
    def __init__(self, members: list[Member], prism_id=""):
        self.validate(members)
        self.members = members
        self.version = prism_plugin_version
        self.sdf = "relative"
        if not prism_id:
            self.id = f'{str(uuid.uuid4())}'
        else:
            self.id = prism_id
        self._datastore_key = ["prism", "prism", self.id]

    @property
    def datastore_key(self):
        return self._datastore_key
    
    def to_json(self):
        return json.dumps({
            "prism_id": self.id,
            "version": self.version,
            "sdf": self.sdf,
            "members": [m.to_json() for m in self.members]
        })
    
    def to_dict(self):
        return {
            "prism_id": self.id,
            "version": self.version,
            "sdf": self.sdf,
            "members": [m.to_dict() for m in self.members]
        }

    @staticmethod
    def validate(members):
        if len(members) < 1:
            raise ValueError("Prism must contain at least one member.")

        if not isinstance(members, list):
            raise ValueError("Members must be a list.")