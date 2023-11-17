#!/usr/bin/env python3
import json
import os
import re
from enum import Enum
from math import floor, ceil
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
        output.write('\n\n')

plugin = Plugin()

pubkeyRegex = re.compile(r'^0[2-3][0-9a-fA-F]{64}$')
bolt12Regex = re.compile(r'^ln([a-zA-Z0-9]{1,90})[0-9]+[munp]?[a-zA-Z0-9]+[0-9]+[munp]?[a-zA-Z0-9]*$')


class PrismBinding:
    def __init__(self, key):
        parts = key.split(':')
        if len(parts) != 4 or not key.startswith('prismbind:'):
            raise ValueError("Invalid PrismBinding key format")

        self.bind_type = parts[1]
        self.invoice_label = parts[2]
        self.prism_id = parts[3]

    def to_json(self):
        return {
            'bind_type': self.bind_type,
            'invoice_label': self.invoice_label,
            'prism_id': self.prism_id
        }

@plugin.init()  # Decorator to define a callback once the `init` method call has successfully completed
def init(options, configuration, plugin, **kwargs):
    plugin.log("prism-api initialized")

@plugin.method("prism-create")
def createprism(plugin, members, prism_id=""):
    '''Create a prism.'''

    if not prism_id:
        # generate an ID for this prism, we namespace the records with "prism-"
        prism_id = f"prism-{str(uuid.uuid4())}"
    
    if not prism_id.startswith("prism-"):
        raise Exception("ERROR: the prism ID MUST start with 'prism-'.")

    # create a new prism object.
    prism = createprism(prism_id, members)

    # add the prism info to datastore with the prism_id
    plugin.rpc.datastore(key=prism_id, string=json.dumps(prism))

    # convert the prism object to JSON for return.
    json_data = json.dumps(prism)
    json_dict = json.loads(json_data)

    # return the prism json
    return json_dict

def createprism(prism_id, members):
    '''Returns a prism object.'''

    validate_members(members)

    # Create the prism json object
    prism = {
        "prism_id": prism_id,
        "version": prism_plugin_version,
        "sdf": "relative",
        "members": members
    }

    return prism

@plugin.method("prism-show")
def showprism(plugin, prism_id):
    '''Show the details of a single prism.'''
    return showprism(prism_id)

def showprism(prism_id):
    try:
        prism_datastore_record = None
        prism_datastore = plugin.rpc.listdatastore(prism_id)

        for record in prism_datastore["datastore"]:
            if record.get("key")[0] == prism_id:
                prism_datastore_record = record
                break

        if prism_datastore_record is not None:

            # Extract the 'string' property and parse it as JSON
            prism_string = json.loads(prism_datastore_record['string'])

            # convert the prism object to JSON for return.
            json_data = json.dumps(prism_string)
            json_dict = json.loads(json_data)
        else:
            raise Exception(f"Prism with id {prism_id} not found.")

    except RpcError as e:
        plugin.log(e)
        return e

    return json_dict

@plugin.method("prism-list")
def listprisms(plugin):
    '''List all prisms.'''
    try:

        datastore = plugin.rpc.listdatastore()["datastore"]
        prism_records = [record for record in datastore if record['key'][0].startswith('prism-')]

        # Extract the 'string' property and parse it as JSON
        prism_strings = [json.loads(record['string']) for record in prism_records]

        # convert the prism object to JSON and return.
        json_data = json.dumps(prism_strings)
        json_dict = json.loads(json_data)

        return json_dict

    except RpcError as e:
        plugin.log(e)
        return e

@plugin.method("prism-update")
def updateprism(plugin, prism_id, members):
    '''Update an existing prism.'''
    try:

        prism = createprism(prism_id, members)

        # convert the prism object to JSON for return.
        json_data = json.dumps(prism)
        json_dict = json.loads(json_data)

        if len(plugin.rpc.listdatastore(prism_id)["datastore"]) == 0:
            raise ValueError(f"A prism with with ID of {prism_id} does not exist")

        plugin.rpc.datastore(key=prism_id, string=json.dumps(json_dict), mode="must-replace")

        return json_dict

    except RpcError as e:
        plugin.log(e)
        return e



@plugin.method("prism-listbindings")
def list_bindings(plugin):
    '''Lists all prism bindings.'''

    datastore = plugin.rpc.listdatastore()["datastore"]
    prism_bindings = [PrismBinding(binding['key'][0]) for binding in datastore if binding['key'][0].startswith('prismbind:')]

    json_data = json.dumps(prism_bindings)
    json_dict = json.loads(json_data)

    return prism_bindings


@plugin.method("prism-addbinding")
def bindprism(plugin, prism_id, invoice_type, invoice_label):
    '''Binds a prism to a BOLT12 Offer or a BOLT11 invoice.'''

    # the purpose of this method is to record in the database an association between 
    # a prism, and either a BOLT11 invoice (invoice_ID) or BOLT12 Offer (offer_ID).
    prism = showprism(prism_id)

    if prism is None:
        raise Exception(f"ERROR: the provided prism_id of '{prism_id}' was not found.")

    types = [ "bolt11", "bolt12" ]
    if invoice_type not in types:
        raise Exception("ERROR: 'type' MUST be either 'bolt12' or 'bolt11'.")

    key = f"prismbind:{invoice_type}:{invoice_label}:{prism_id}"

    # TODO ensure the offer_id or invoice_id exists.

    # add the binding to the data store. All the info is in the key; no payload needed.
    plugin.rpc.datastore(key=key, string="", mode="must-create")
    return key

@plugin.method("prism-removebinding")
def remove_prism_binding(plugin, prism_id, invoice_type, invoice_label):
    '''Removes a prism binding.'''

    existing_bindings = list_bindings(plugin)

    key = f"prismbind:{invoice_type}:{invoice_label}:{prism_id}"

    plugin.rpc.deldatastore(key)
    existing_bindings = list_bindings(plugin)
    return existing_bindings


@plugin.method("prism-delete")
def delete_prism(plugin, prism_id):
    '''Deletes a prism.'''

    return_value = prism_id
    try:

        # TODO; we can also delete all prism bindings.

        # TODO; before we delete, we should ensure it's not referenced in any bindings.

        plugin.rpc.deldatastore(prism_id)
    except RpcError as e:
        raise Exception(f"Prism with ID {prism_id} does not exist.")

    return return_value


def validate_members(members):
    if len(members) < 1:
        raise ValueError("Prism must contain at least one member.")

    if not isinstance(members, list):
        raise ValueError("Members must be a list.")

    
    for member in members:
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
        member['outlay_msats'] = member.get('outlay_msats', 0)
        member['threshold'] = member.get('threshold', 0)


        # TODO also check to see if the user provided MORE fields than is allowed.


@plugin.method("prism-pay")
def prism_pay(prism_id, amount_msat, label=""):
    '''Executes (pays-out) a prism.'''

    # TODO; first thing we should do here probably is update the Prism with new outlay values.
    # that way we can immediately record/persist 


    # note, running 'prism-pay' with amount_msat=0 will result in outlays being paid out (assuming the threshold has been met)
    if amount_msat < 0:
        raise Exception("ERROR: amount_msat MUST BE greater than or equal to zero.")

    prism = showprism(prism_id)
    prism_members = None

    if prism is not None:
        prism_members = prism["members"]

        if prism_members is None:
            raise Exception(f"Error: Could not extract prism_members for prism {prism_id}")

        # sum all the member split variables.
        total_split = sum(map(lambda member: member['split'], prism_members))

        for member in prism_members:
            # iterate over each prism member and send them their split
            # msat comes as "5000msat"
            deserved_msats = Millisatoshi(floor((member['split'] / total_split) * amount_msat))

            outlay_msats = deserved_msats + Millisatoshi(member["outlay_msats"])
        
            plugin.log(f"outlay_msats: {outlay_msats}")

            try:
                payment = pay(member["type"], member["destination"], outlay_msats)
                outlay_msats -= payment["amount_sent_msat"]

                # TODO update the OUTLAY!

                #update_outlay(prism_id, member["name"], outlay_msats)

            except RpcError as e:
                update_outlay(offer_id, member["id"], outlay_msats)

                error = create_payment_error(member, member["outlay_msats"], e.error, offer_id)
                log_payments(error)

def pay(payment_type, destination, amount_msat):
    payment_result = {}
    if payment_type == "keysend":
        payment_result = plugin.rpc.keysend(destination=destination, amount_msat=amount_msat)
        plugin.log(f"Sent keysend payment for {destination} worth {amount_msat}")
    elif payment_type == "bolt12":
        fetch_invoice_response = plugin.rpc.fetchinvoice(offer=destination, amount_msat=amount_msat)
        bolt12_invoice = fetch_invoice_response["invoice"]
        payment_result = plugin.rpc.pay(bolt12_invoice)
        plugin.log(f"Sent bolt12 payment for {destination} worth {amount_msat}")
    else:
        raise Exception("ERROR: something went wrong. The payment type was not correct.")

    return payment_result

# ABOUT: First, we check the db to see if there are any bindings associated with 
# the invoice payment.
@plugin.subscribe("invoice_payment")
def on_payment(plugin, invoice_payment, **kwargs):
    try:
        payment_label = invoice_payment["label"]
        invoice = plugin.rpc.listinvoices(payment_label)
        offer_id = None
        is_bolt12 = false

        if "local_offer_id" in invoice:
            offer_id = invoice["local_offer_id"]
            is_bolt12 = true
        else:
            is_bolt12 = false

        # since BOLT11 invoices are single-use, after payment, we can delete the prism binding for it.
        if is_bolt12 is false:
            printout(f"TODO need to delete the prism binding for this bolt11 invoice.")

        # TODO if we're using a single-use BOLT12 offer, we can remove the prism binding.
        if is_bolt12 is true:
            printout(f"TODO need to delete the prism binding for this single-use bolt12 offer.")

        preimage = invoice_payment["preimage"]
        amount_msat = invoice_payment['msat'][:-4]

        printout(f"payment_label:  {payment_label}")
        printout(f"preimage:  {preimage}")
        printout(f"amount_msat:  {amount_msat}")
    except Exception as e:
        printout("Payment error: {}".format(e))



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


# def get_member_json(offer_id, member_id):
#     prism = get_prism_json()["prisms"][offer_id]

#     members = prism["members"]

#     for member in members:
#         if member["id"] == member_id:
#             member = member
#             break

#     return member


def update_outlay(offer_id, member_id, amount_msat):
    member = get_member_json(offer_id, member_id)
    member["outlay_msats"] = int(amount_msat)

    update_member(offer_id, member_id, member)

def log_payments(payment_result):
    lightning_dir = plugin.rpc.getinfo()["lightning-dir"]
    log_file = os.path.join("/tmp", lightning_dir, "prism.log")

    with open(log_file, "a") as log:
        log.write(str(payment_result))
        log.write("\n\n")


def create_payment_error(member, outlay_msats, rpc_error, prism_id):
    error_message = "Failed to pay {} to {}".format(
        outlay_msats, member["name"])
    time = "{}".format(datetime.utcnow())

    return {
        "time": time,
        "message": error_message,
        "amount": outlay_msats,
        "member_id": member["id"],
        "prism_id": prism_id,
        "rpc_error": rpc_error,
    }


def create_payment_result(member, payment, error=None, owe="0"):
    if error:
        result = {
            "destination": member["destination"],
            "type": member.get("type", "bolt12"),
            "amount_msat": "",
            "amount_sent_msat": "",
            "status": "error",
            "created_at": "",
            "error_message": error,
        }
    else:
        result = {
            "destination": member["destination"],
            "type": member.get("type", "bolt12"),
            "amount_msat": payment["amount_msat"],
            "amount_sent_msat": payment["amount_sent_msat"],
            "status": payment["status"],
            "created_at": datetime.fromtimestamp(payment["created_at"]).strftime("%Y-%m-%d %H:%M:%S"),
            "error_message": ""
        }
    return result


plugin.run()  # Run our plugin
