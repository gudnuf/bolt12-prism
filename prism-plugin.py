#!/usr/bin/env python3
import json
import os
import re
from math import floor
from pyln.client import Plugin, RpcError, Millisatoshi
import uuid
from datetime import datetime

prism_plugin_version = "v0.0.2"

plugin_out = "/tmp/plugin_out"
if os.path.isfile(plugin_out):
    os.remove(plugin_out)

# use this for debugging
def printout(s):
    with open(plugin_out, "a") as output:
        output.write(s)

plugin = Plugin()

pubkeyRegex = re.compile(r'^0[2-3][0-9a-fA-F]{64}$')
bolt12Regex = re.compile(r'^ln([a-zA-Z0-9]{1,90})[0-9]+[munp]?[a-zA-Z0-9]+[0-9]+[munp]?[a-zA-Z0-9]*$')

@plugin.init()  # Decorator to define a callback once the `init` method call has successfully completed
def init(options, configuration, plugin, **kwargs):
    plugin.log("CLN Prism Plugin initialized")

@plugin.method("prism-create")
def createprism(plugin, members):
    '''Create a prism.'''
    try:
        # first, let's validate the members JSON. Better be correct before we continue.
        validate_members(members)

    except Exception as e:
        return e

    else:
        # generate an ID for this prism, we namespace the records with "prism-"
        prism_id = f"prism-{str(uuid.uuid4())}"

        # Create the prism json object
        prism = {
            "prism_id": prism_id,
            "prism_version": prism_plugin_version,
            "split_distribution_function": "relative",
            "prism_members": members
        }

        # add the prism info to datastore with the prism_id
        plugin.rpc.datastore(key=prism_id, string=json.dumps(prism))

        # convert the prism object to JSON for return.
        json_data = json.dumps(prism)
        json_dict = json.loads(json_data)

        # return the prism json
        return json_dict


@plugin.method("prism-listall")
def listprisms(plugin):
    '''List all prisms.'''
    try:

        datastore = plugin.rpc.listdatastore()["datastore"]
        prism_records = [record for record in datastore if record['key'][0].startswith('prism-')]

        # Extract the 'string' property and parse it as JSON
        prism_strings = [json.loads(record['string']) for record in prism_records]

        # convert the prism object to JSON for return.
        json_data = json.dumps(prism_strings)
        json_dict = json.loads(json_data)

        return json_dict

    except RpcError as e:
        plugin.log(e)
        return e


@plugin.method("prism-bind")
def deleteprism(plugin, prism_id):
    '''Binds a prism to either a BOLT11 invoice or BOLT12 offer such that when an invoice is paid, the prism will be executed.'''

    return_value = prism_id
    try:

        # TODO; before we delete, we should ensure it's not referenced anywhere (i.e., bindings)

        plugin.rpc.deldatastore(prism_id)
    except RpcError as e:
        raise Exception(f"Prism with ID {prism_id} does not exist.")

    return return_value



# note this method simply executes the
@plugin.method("prism-execute")
def deleteprism(plugin, prism_id):
    '''Executes a prism.'''

    return_value = prism_id
    try:

        # TODO; before we delete, we should ensure it's not referenced anywhere (i.e., bindings)

        plugin.rpc.deldatastore(prism_id)
    except RpcError as e:
        raise Exception(f"Prism with ID {prism_id} does not exist.")

    return return_value





@plugin.method("prism-delete")
def deleteprism(plugin, prism_id):
    '''Deletes a BOLT12 prism.'''

    return_value = prism_id
    try:

        # TODO; before we delete, we should ensure it's not referenced anywhere (i.e., bindings)

        plugin.rpc.deldatastore(prism_id)
    except RpcError as e:
        raise Exception(f"Prism with ID {prism_id} does not exist.")

    return return_value




# # TODO check the prism bind table to determine if a particular invoice_payment is 
# # subject to the prism payment
# @plugin.subscribe("invoice_payment")
# def on_payment(plugin, invoice_payment, **kwargs):
#     try:
#         offer_id = invoice_payment["label"].split("-")[0]

#         members = get_prism_json()["prisms"][offer_id]["members"]

#         # determine how many satoshis to send each member
#         total_split = sum(map(lambda member: member['split'], members))

#         for member in members:
#             # iterate over each prism member and send them their split
#             # msat comes as "5000msat"
#             deserved_msats = Millisatoshi(floor((member['split'] / total_split) *
#                                                 int(invoice_payment['msat'][:-4])))

#             outlay_msats = deserved_msats + \
#                 Millisatoshi(member["outlay_msats"])

#             try:
#                 payment = pay(
#                     member["type"], member["destination"], outlay_msats)

#                 outlay_msats -= payment["amount_sent_msat"]

#                 update_outlay(
#                     offer_id, member["id"], outlay_msats)

#             except RpcError as e:
#                 update_outlay(offer_id, member["id"], outlay_msats)

#                 error = create_payment_error(
#                     member, member["outlay_msats"], e.error, offer_id)
#                 log_payments(error)

#     except RpcError as e:
#         printout("Payment error: {}".format(e))





# def pay(payment_type, destination, amount_msat):
#     payment_result = {}
#     if payment_type == "keysend":
#         payment_result = plugin.rpc.keysend(
#             destination=destination, amount_msat=amount_msat)

#     if payment_type == "bolt12":
#         invoice_obj = plugin.rpc.fetchinvoice(
#             offer=destination, amount_msat=amount_msat)

#         bolt11 = invoice_obj["invoice"]

#         payment_result = plugin.rpc.pay(bolt11=bolt11)

#     return payment_result





# def update_member(offer_id, member_id, member):
#     try:
#         prism = get_prism_json()["prisms"][offer_id]

#         members = prism["members"]

#         for i, old_member in enumerate(members):
#             if old_member["id"] == member_id:
#                 members[i] = member

#         prism["members"] = members

#         prism_string = json.dumps(prism)

#         plugin.rpc.datastore(
#             key=offer_id, string=prism_string, mode="must-replace")
#     except RpcError as e:
#         plugin.log(e)


# def get_prism_json(offer_id=None):
#     try:
#         offers = plugin.rpc.listoffers()["offers"]
#         offer_ids = [offer["offer_id"] for offer in offers]

#         datastore = plugin.rpc.listdatastore()["datastore"]

#         # extract all datastore entries with a key that matches our offer_ids
#         prisms = [i for i in datastore if any(
#             offer_id in i["key"] for offer_id in offer_ids)]

#         prism_data = {}

#         for prism in prisms:
#             prism_json = json.loads(prism['string'].replace('\\"', '"'))
#             prism_id = prism_json["offer_id"]
#             prism_data[prism_id] = prism_json

#         return {"prisms": prism_data}
#     except RpcError as e:
#         plugin.log(e)
#         return e


# def get_member_json(offer_id, member_id):
#     prism = get_prism_json()["prisms"][offer_id]

#     members = prism["members"]

#     for member in members:
#         if member["id"] == member_id:
#             member = member
#             break

#     return member


# def update_outlay(offer_id, member_id, amount_msat):
#     member = get_member_json(offer_id, member_id)
#     member["outlay_msats"] = int(amount_msat)

#     update_member(offer_id, member_id, member)


def validate_members(members):
    if len(members) < 1:
        raise ValueError("Prism must contain at least one member.")

    if not isinstance(members, list):
        raise ValueError("Members must be a list.")

    required_keys = ["name", "destination", "split"]
    for member in members:
        if not isinstance(member, dict):
            raise ValueError("Each member in the list must be a dictionary.")

        for key in required_keys:
            if key not in member:
                raise ValueError(f"Member must contain '{key}' key.")

        if not isinstance(member["name"], str):
            raise ValueError("Member 'name' must be a string.")

        if not isinstance(member["destination"], str):
            raise ValueError("Member 'destination' must be a string")

        if not isinstance(member["split"], int):
            raise ValueError("Member 'split' must be an integer")

        if member["split"] < 1 or member["split"] > 1000:
            raise ValueError(
                "Member 'split' must be an integer between 1 and 1000")

        types = ["keysend", "bolt12"]
        if "type" in member and not member["type"] in types:
            raise ValueError(
                "Invalid payment type. Supported types are 'bolt12' and 'keysend'. Default is 'bolt12'.")

        # make sure destination is valid bolt12 or node pubkey
        valid_destination = None

        if "type" not in member or member["type"] == "bolt12":
            valid_destination = member["destination"] if bolt12Regex.match(
                member["destination"]) else None

        if "type" in member and member["type"] == "keysend":
            valid_destination = member["destination"] if pubkeyRegex.match(
                member["destination"]) else None

        if valid_destination is None:
            raise Exception(
                "Destination must be a valid lightning node pubkey or bolt12 offer")


# def log_payments(payment_result):
#     lightning_dir = plugin.rpc.getinfo()["lightning-dir"]
#     log_file = os.path.join("/tmp", lightning_dir, "prism.log")

#     with open(log_file, "a") as log:
#         log.write(str(payment_result))
#         log.write("\n\n")


# def create_payment_error(member, outlay_msats, rpc_error, prism_id):
#     error_message = "Failed to pay {} to {}".format(
#         outlay_msats, member["name"])
#     time = "{}".format(datetime.utcnow())

#     return {
#         "time": time,
#         "message": error_message,
#         "amount": outlay_msats,
#         "member_id": member["id"],
#         "prism_id": prism_id,
#         "rpc_error": rpc_error,
#     }


# def create_payment_result(member, payment, error=None, owe="0"):
#     if error:
#         result = {
#             "destination": member["destination"],
#             "type": member.get("type", "bolt12"),
#             "amount_msat": "",
#             "amount_sent_msat": "",
#             "status": "error",
#             "created_at": "",
#             "error_message": error,
#         }
#     else:
#         result = {
#             "destination": member["destination"],
#             "type": member.get("type", "bolt12"),
#             "amount_msat": payment["amount_msat"],
#             "amount_sent_msat": payment["amount_sent_msat"],
#             "status": payment["status"],
#             "created_at": datetime.fromtimestamp(payment["created_at"]).strftime("%Y-%m-%d %H:%M:%S"),
#             "error_message": ""
#         }
#     return result


plugin.run()  # Run our plugin
