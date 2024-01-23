#!/usr/bin/env python3
import json
import os
from math import floor
from pyln.client import Plugin, RpcError, Millisatoshi
from datetime import datetime
from lib import Prism, Member, pubkeyRegex, bolt12Regex

plugin = Plugin()

# TODO: remove this, there are two instances of the class
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

    # TODO add minimum version check.
    # TODO migrate legacy prisms and bring them up-to-date with this version if necessary

    plugin.log("prism-api initialized")

@plugin.method("prism-create")
def createprism(plugin, members, prism_id=""):
    '''Create a prism.'''
    prism_members = [Member(m) for m in members]
    # create a new prism object.
    prism = Prism(prism_members, prism_id)

    prism_json = prism.to_json()

    # TODO: this method should only be able to create new prisms and prism-update should be used for updating prisms
    # TODO: decide if database operations should be moved to the Prism classes?
    # add the prism info to datastore with the prism_id
    plugin.rpc.datastore(key=prism.datastore_key, string=prism_json, mode="create-or-replace")

    # return the prism json
    return prism.to_dict()

@plugin.method("prism-show")
def showprism(plugin, prism_id):
    '''Show the details of a single prism.'''
    return showprism(prism_id)

# TODO: I think only plugin methods should be defined in this file, and any utility functions defined elsewhere
#       `showprism` is used in two places, maybe we just get rid of this or move to the prism class
def showprism(prism_id):
    prism = Prism.find_unique(plugin, id=prism_id)   

    if prism is None:
        raise Exception(f"Prism with id {prism_id} not found.")

    return prism.to_dict()

@plugin.method("prism-list")
def listprisms(plugin):
    '''List all prisms.'''
    try:
        # TODO: match cln return syntax of {"prisms": []}
        return Prism.find_all(plugin)

    except RpcError as e:
        plugin.log(e)
        return e

@plugin.method("prism-update")
def updateprism(plugin, prism_id, members):
    '''Update an existing prism.'''
    try:

        prism = Prism.find_unique(plugin, id=prism_id)

        if not prism:
            raise ValueError(f"A prism with with ID {prism_id} does not exist")
        
        # TODO just make an update method for the first prism instance
        updated_members = [Member(m) for m in members]
        updated_prism = Prism(updated_members, prism_id=prism_id)
        
        # update prism in datastore
        plugin.rpc.datastore(
            key=updated_prism.datastore_key, 
            string=updated_prism.to_json(), 
            mode="create-or-replace"
            )

        # return prism as a dict
        return updated_prism.to_dict()

    except RpcError as e:
        plugin.log(e)
        return e


class PrismBinding:
    def __init__(self, offer_id, prism_ids):
        self.offer_id = offer_id
        self.prism_ids = prism_ids

    def to_dict(self):
        return {"offer_id": self.offer_id, "prism_ids": self.prism_ids}

    def to_json(self):
        rtnVal = {
            "offer_id": self.offer_id,
            "prisms": self.prism_ids
        }

        return rtnVal



@plugin.method("prism-bindinglist")
def list_bindings(plugin, bolt_version="bolt12"):
    '''Lists all prism bindings.'''

    types = [ "bolt11", "bolt12" ]
    if bolt_version not in types:
        raise Exception("ERROR: 'type' MUST be either 'bolt12' or 'bolt11'.")

    prism_binding_key = [ "prism", "bind", bolt_version ]
    prism_bindings = plugin.rpc.listdatastore(key=prism_binding_key)["datastore"]

    #plugin.log(f"prism_bindings: {prism_bindings}")

    # Extract the 'string' property and parse it as JSONa
    prism_binding_objects = []

    for binding in prism_bindings:
        prism_binding = PrismBinding(binding['key'][3], list(json.loads(binding['string'])))
        prism_binding_objects.append(prism_binding)

    #plugin.log(f"prism_binding_objects: {prism_binding_objects}")

    return_object = {
        "bolt12_bindings": prism_binding_objects }

    return return_object

@plugin.method("prism-bindingshow")
def get_binding(plugin, prism_id, bolt_version="bolt12"):
    '''Show the bindings of a specific prism.'''

    plugin.log(f"running get_binding")

    prism_binding = None

    # so, need to pull all prism binding records and iterate over each one
    # to see if it contains the current prism_id is the content of the record.
    prism_records_key = [ "prism", "bind", bolt_version ]
    plugin.log(f"prism_records_key: {prism_records_key}")

    prism_binding_records = plugin.rpc.listdatastore(key=prism_records_key)["datastore"]

    relevant_offer_ids_for_prism = []
    relevant_offer_ids_for_prism_bolt11 = []

    for binding_record in prism_binding_records:
        list_of_prisms_in_binding_record = json.dumps(binding_record["string"])
        #plugin.log(f"list_of_prisms_in_binding_record: {list_of_prisms_in_binding_record}")
        
        if prism_id in list_of_prisms_in_binding_record:
            offer_id = binding_record["key"][3]
            relevant_offer_ids_for_prism.append(offer_id)

    return_object = {
        "prism_id": prism_id,
        "bolt": bolt_version,
        "offer_ids": relevant_offer_ids_for_prism }

    return return_object


# in this method, we maintain two sets of records, fbind and rbind. 
# fbind records are a one-to-many that maps a particular bolt12 offer or bolt11 invoice
# to a list of prism ids. This is used when an invoice/offer is paid; the code
# can go look up all the prism_ids that should be executed when a particular offer/invoice is paid

# the rbind maps maintains a list of offer/invoice ids for a specific prism_id.
# this allows for the bindingshow method, which will show you a list of offer/invoice IDs that are
# currently bound to a specific prism_id.
@plugin.method("prism-bindingadd")
def bindprism(plugin, prism_id, offer_id, bolt_version="bolt12"):
    '''Binds a prism to a BOLT12 Offer or a BOLT11 invoice.'''

    dbmode="must-create"

    types = [ "bolt11", "bolt12" ]
    if bolt_version not in types:
        raise Exception("ERROR: 'type' MUST be either 'bolt12' or 'bolt11'.")

    # ensure the offer/invoice exists
    if bolt_version == "bolt12":
        offer = plugin.rpc.listoffers(offer_id)

        if len(offer) == 0:
            raise Exception("ERROR: the bolt12 offer does not exist!")

    elif bolt_version == "bolt11":
        invoice = plugin.rpc.listinvoices(offer_id)

        if invoice is None:
            raise Exception("ERROR: the bolt11 invoice does not exist.")

    # first we need to see if there are any existing binding records for this prism_id/invoice_type
    prism_binding_key = [ "prism", "bind", bolt_version, offer_id ]
    plugin.log(f"binding_key: {prism_binding_key}")

    forward_binding_record = plugin.rpc.listdatastore(key=prism_binding_key)["datastore"]
    list_of_prism_ids = []

    if len(forward_binding_record) > 0:
        # oh, the record already exists. If if s
        dbmode = "must-replace"
        plugin.log(f"forward_binding_record: {forward_binding_record[0]['string']}")
        list_of_prism_ids = json.loads(forward_binding_record[0]["string"])
        plugin.log(f"list_of_prism_ids: {list_of_prism_ids}")
      
    # add the new prism too. 
    list_of_prism_ids.append(prism_id)

    # save the record
    val = plugin.rpc.datastore(key=prism_binding_key, string=json.dumps(list_of_prism_ids), mode=dbmode)


    response = {
        "status": dbmode,
        "offer_id": offer_id,
        "prism_id": prism_id,
        "prism_binding_key": prism_binding_key }


    return response

@plugin.method("prism-bindingremove")
def remove_prism_binding(plugin, offer_id, prism_id, bolt_version="bolt12"):
    '''Removes a prism binding.'''

    plugin.log(f"in prism-bindingremove")

    dbmode = "must-replace"

    types = [ "bolt11", "bolt12" ]
    if bolt_version not in types:
        raise Exception("ERROR: 'type' MUST be either 'bolt12' or 'bolt11'.")

    # first we need to see if there are any existing binding records for this prism_id/invoice_type
    prism_binding_key = [ "prism", "bind", bolt_version, offer_id ]
    plugin.log(f"binding_key: {prism_binding_key}")

    binding_record = plugin.rpc.listdatastore(key=prism_binding_key)["datastore"]

    list_of_prism_ids = []

    if len(binding_record) > 0:
        # oh, the record already exists. If if s
        list_of_prism_ids = json.loads(binding_record[0]["string"])
        list_of_prism_ids.remove(prism_id)
        dbmode = "must-replace"
        plugin.log(f"binding_record: {binding_record[0]['string']}")
        list_of_prism_ids = json.loads(binding_record[0]["string"])
        plugin.log(f"list_of_prism_ids: {list_of_prism_ids}")

        if prism_id in list_of_prism_ids:
            list_of_prism_ids.remove(prism_id)
    else:
        raise Exception(f"Could not find any binding records for {bolt_version} {offer_id}")

    status_indicator = None

    # we delete the entire database entry if there are no prisms associated with it.
    if len(list_of_prism_ids) == 0:
        status_indicator = "deleted-key"
        plugin.rpc.deldatastore(key=prism_binding_key)

    else:
        status_indicator = "updated-key"
        # we need to update the record now.
        plugin.rpc.datastore(key=prism_binding_key, string=json.dumps(list_of_prism_ids), mode=dbmode)

    response = {
        "status": status_indicator,
        "offer_id": offer_id,
        "prism_id": prism_id,
        "prism_binding_key": prism_binding_key }

    return response

# @plugin.method("prism-delete")
# def delete_prism(plugin, prism_id):
#     '''Deletes a prism.'''

#     return_value = prism_id
#     try:

#         # TODO; we can also delete all prism bindings.

#         plugin.rpc.deldatastore(prism_id)
#     except RpcError as e:
#         raise Exception(f"Prism with ID {prism_id} does not exist.")

#     return return_value


@plugin.method("prism-executepayout")
def prism_execute(prism_id, amount_msat=0, label=""):
    '''Executes (pays-out) a prism.'''

    if not isinstance(amount_msat, int):
        plugin.log(f"ERROR: amount_msat is the incorrect type.")
        raise Exception("ERROR: amount_msat is the incorrect type.")

    # TODO; first thing we should do here probably is update the Prism with new outlay values.
    # that way we can immediately record/persist 
    plugin.log(f"{amount_msat}")
    plugin.log(f"Starting prism_execute for prism_id: {prism_id} for {amount_msat}msats.")

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
            outlay_msat = deserved_msats + Millisatoshi(member["outlay_msat"])

            try:
                payment = pay(member["type"], member["destination"], outlay_msat)
                
                # TODO if payment successful, then subtract the outlay, depending on who incurs fees.
                outlay_msat -= payment["amount_sent_msat"]

                # TODO update the OUTLAY!
                #update_outlay(prism_id, member["name"], outlay_msat)

            except RpcError as e:
                update_outlay(offer_id, member["id"], outlay_msat)

                error = create_payment_error(member, member["outlay_msat"], e.error, offer_id)
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
    
    plugin.log(f"Got into on_payment for plugin")

    try:
        payment_label = invoice_payment["label"]
        invoice = plugin.rpc.listinvoices(payment_label)
        bind_type = "bolt11"
        offer_id = None

        if "local_offer_id" in invoice:
            offer_id = invoice["local_offer_id"]
            bind_type = "bolt12"

        amount_msat = invoice_payment['msat'][:-4]
        plugin.log(f"payment_label:  {payment_label}")
        plugin.log(f"amount_msat:  {amount_msat}")

        # so the next step is to get the prism bindings and see if this payment
        # should be acted upon (i.e., this incoming payment has one or more prisms bound to it.)
        binding = get_binding(plugin, offer_id, bind_type)

        if binding is not None:
            plugin.log(f"binding from get_binding:  {binding}")
        else:
            plugin.log(f"ERROR: could not find the specific binding.")

        

        #printout(str(json_dict))
        for prism_id in prisms_to_execute:
            prism_execute(prism_id, int(amount_msat), payment_label)

    except Exception as e:
        printout("Payment error: {}".format(e))


plugin.run()  # Run our plugin
