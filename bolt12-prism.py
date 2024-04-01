#!/usr/bin/env python3
from pyln.client import Plugin, RpcError
from lib import Prism, Member, PrismBinding

plugin = Plugin()


@plugin.init()  # Decorator to define a callback once the `init` method call has successfully completed
def init(options, configuration, plugin, **kwargs):

    # TODO add minimum version check; ie ensure CLN is the correct version for this plugin version.
    # TODO migrate legacy prisms and bring them up-to-date with this version if necessary

    plugin.log("prism-api initialized")


@plugin.method("prism-create")
def createprism(plugin, members, prism_id=""):
    '''Create a prism.'''

    prism_members = [Member(plugin=plugin, member_dict=m) for m in members]

    # create a new prism object (this is used for our return object only)
    prism = Prism(plugin, prism_id, prism_members)

    # save all the record to the database
    prism.save()

    # return the prism json
    return prism.to_dict()


@plugin.method("prism-show")
def showprism(plugin, prism_id):
    '''Show the details of a single prism.'''

    prism = Prism.get(plugin=plugin, prism_id=prism_id)

    if prism is None:
        raise Exception(f"Prism with id {prism_id} not found.")

    return prism.to_dict()


@plugin.method("prism-list")
def listprisms(plugin):
    '''List all prisms.'''
    try:
        return {
            "prism_ids": Prism.find_all(plugin)
        }

    except RpcError as e:
        plugin.log(e)
        return e


@plugin.method("prism-update")
def updateprism(plugin, prism_id, members):
    '''Update an existing prism.'''
    try:

        prism = Prism.get(plugin=plugin, prism_id=prism_id)

        if not prism:
            raise ValueError(f"A prism with with ID {prism_id} does not exist")

        # TODO just make an update method for the first prism instance
        updated_members = [
            Member(plugin=plugin, member_dict=member) for member in members]

        updated_prism_object = Prism(
            plugin, prism_id=prism_id, members=updated_members)

        updated_prism_object.save()

        # return prism as a dict
        return updated_prism_object.to_dict()

    except RpcError as e:
        plugin.log(e)
        return e


@plugin.method("prism-bindinglist")
def list_bindings(plugin, bolt_version="bolt12"):
    '''Lists all prism bindings.'''

    binding_offers = PrismBinding.list_binding_offers(
        plugin, bolt_version=bolt_version)
    response = {
        f"{bolt_version}_prism_bindings": [binding.to_dict() for binding in binding_offers]
    }

    return response


@plugin.method("prism-bindingshow")
def get_binding(plugin, bind_to, bolt_version="bolt12"):
    '''Show the bindings of a specific prism.'''

    binding = PrismBinding.get(plugin, bind_to, bolt_version)

    if not binding:
        raise Exception("ERROR: could not find a binding for this offer.")

    plugin.log(
        f"INFO: prism-bindingsbindinghow executed for {bolt_version} offer '{bind_to}'")

    return binding.to_dict()

# adds a binding to the database.


@plugin.method("prism-bindingadd")
def bindprism(plugin: Plugin, prism_id, bind_to, bolt_version="bolt12"):
    '''Binds a prism to a BOLT12 Offer or a BOLT11 invoice.'''

    bolt_versions = ["bolt11", "bolt12"]
    if bolt_version not in bolt_versions:
        raise Exception("ERROR: 'type' MUST be either 'bolt12' or 'bolt11'.")

    trigger = None

    # ensure the offer/invoice exists
    if bolt_version == "bolt12":
        trigger = plugin.rpc.listoffers(offer_id=bind_to)["offers"]

        if [trigger] == []:
            raise Exception("ERROR: the bolt12 offer does not exist!")

    elif bolt_version == "bolt11":
        trigger = plugin.rpc.listinvoices(label=bind_to)["invoices"]

        if trigger == []:
            raise Exception("ERROR: the bolt11 invoice does not exist.")

    add_binding_result = PrismBinding.add_binding(
        plugin=plugin, bind_to=bind_to, prism_id=prism_id, bolt_version=bolt_version)

    return add_binding_result

# @plugin.method("prism-bindingremove")
# def remove_prism_binding(plugin, offer_id, prism_id, bolt_version="bolt12"):
#     '''Removes a prism binding.'''

#     plugin.log(f"in prism-bindingremove")

#     dbmode = "must-replace"

#     types = [ "bolt11", "bolt12" ]
#     if bolt_version not in types:
#         raise Exception("ERROR: 'type' MUST be either 'bolt12' or 'bolt11'.")

#     # first we need to see if there are any existing binding records for this prism_id/invoice_type
#     prism_binding_key = [ "prism", prism_db_version, "bind", bolt_version, offer_id ]
#     plugin.log(f"binding_key: {prism_binding_key}")

#     binding_record = plugin.rpc.listdatastore(key=prism_binding_key)["datastore"]

#     list_of_prism_ids = []

#     if len(binding_record) > 0:
#         # oh, the record already exists. If if s
#         list_of_prism_ids = json.loads(binding_record[0]["string"])
#         list_of_prism_ids.remove(prism_id)
#         dbmode = "must-replace"
#         plugin.log(f"binding_record: {binding_record[0]['string']}")
#         list_of_prism_ids = json.loads(binding_record[0]["string"])
#         plugin.log(f"list_of_prism_ids: {list_of_prism_ids}")

#         if prism_id in list_of_prism_ids:
#             list_of_prism_ids.remove(prism_id)
#     else:
#         raise Exception(f"Could not find any binding records for {bolt_version} {offer_id}")

#     status_indicator = None

#     # we delete the entire database entry if there are no prisms associated with it.
#     if len(list_of_prism_ids) == 0:
#         status_indicator = "deleted-key"
#         plugin.rpc.deldatastore(key=prism_binding_key)

#     else:
#         status_indicator = "updated-key"
#         # we need to update the record now.
#         plugin.rpc.datastore(key=prism_binding_key, string=json.dumps(list_of_prism_ids), mode=dbmode)

#     response = {
#         "status": status_indicator,
#         "offer_id": offer_id,
#         "prism_id": prism_id,
#         "prism_binding_key": prism_binding_key }

#     return response

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
def prism_execute(plugin, prism_id, amount_msat=0, label=""):
    '''Executes (pays-out) a prism.'''

    plugin.log(
        f"In prism_execute with prism_ID {prism_id} and amount = {amount_msat}")

    if not isinstance(amount_msat, int):
        raise Exception("ERROR: amount_msat is the incorrect type.")

    if amount_msat <= 0:
        plugin.log(f"ERROR: amount_msat must be greater than 0.")
        raise Exception("ERROR: amount_msat must be greater than 0.")

    # # TODO; first thing we should do here probably is update the Prism with new outlay values.
    # # that way we can immediately record/persist
    plugin.log(f"{amount_msat}")
    plugin.log(
        f"Starting prism_execute for prism_id: {prism_id} for {amount_msat}msats.")

    prism = Prism.get(plugin, prism_id)

    if prism is None:
        raise Exception("ERROR: could not find prism.")

    # if prism.members is None:
    #     raise Exception(f"ERROR: Could not extract prism_members for prism {prism_id}")
    plugin.log("PAYING")
    pay_results = prism.pay(amount_msat=amount_msat)

    return pay_results

    # TODO: move the below code into prism.pay

    # # this for loop basically updates all the prism member outlay database records...
    # # we don't execute payments in this loop.
    # for member in prism.members:

    #     # so, let's first update the outlay in the database
    #     # so if fails, we retain the payout amount. If the payment is successful,
    #     # we will want to deduct the payment fee from the outlay and update record.

    #     # first we need to see if there are any existing binding records for this prism_id/invoice_type
    #     prism_outlay_key = [ "prism", "prism", prism_id, "outlay" ]
    #     plugin.log(f"prism_outlay_key: {prism_outlay_key}")

    #     existing_outlay = 0

    #     # ok let's first pull any existing outlay records from the datastore.
    #     outlay_binding_record = plugin.rpc.listdatastore(key=prism_outlay_key)["datastore"]
    #     plugin.log(f"outlay_binding_record: {outlay_binding_record}")

    #     if len(outlay_binding_record) == 0:
    #         dbmode = "must-create"
    #         existing_outlay = 0
    #         plugin.log(f"Creating a new outlay record for: {prism_outlay_key}")
    #     else:
    #         # ok, the record already exists. Lets add the outlay from the prismexecute
    #         dbmode = "must-replace"
    #         existing_outlay = Millisatoshi(outlay_binding_record[0]["string"])
    #         plugin.log(f"existing_outlay: {existing_outlay}")

    #     new_member_outlay = Millisatoshi(floor(existing_outlay / sum_of_member_splits) * amount_msat)
    #     plugin.log(f"new_member_outlay / member: {new_member_outlay} / {member['name']}")

    #     # save the outlay in the database before we attempt to pay out.
    #     plugin.rpc.datastore(key=prism_outlay_key, string=new_member_outlay, mode=dbmode)

    #     for member in prism_members:

    #         # first we need to see if there are any existing binding records for this prism_id/invoice_type
    #         prism_outlay_key = [ "prism", "prism", prism_id, "outlay" ]
    #         plugin.log(f"prism_outlay_key: {prism_outlay_key}")

    #         existing_outlay = 0

    #         # ok let's first pull any existing outlay records from the datastore.
    #         outlay_binding_record = plugin.rpc.listdatastore(key=prism_outlay_key)["datastore"]
    #         plugin.log(f"outlay_binding_record: {outlay_binding_record}")

    #         outlay_msat = prism_deserved_msats + Millisatoshi(existing_outlay)
    #         payment_type = member["type"]

    #         payment_result = {}
    #         if payment_type == "keysend":
    #             payment_result = plugin.rpc.keysend(destination=destination, amount_msat=amount_msat)
    #             plugin.log(f"Sent keysend payment for {destination} worth {amount_msat}")
    #         elif payment_type == "bolt12":
    #             fetch_invoice_response = plugin.rpc.fetchinvoice(offer=destination, amount_msat=amount_msat)
    #             bolt12_invoice = fetch_invoice_response["invoice"]
    #             payment_result = plugin.rpc.pay(bolt12_invoice)
    #             plugin.log(f"Sent bolt12 payment for {destination} worth {amount_msat}")
    #         else:
    #             raise Exception("ERROR: something went wrong. The payment type was not correct.")

# # ABOUT: First, we check the db to see if there are any bindings associated with
# # the invoice payment.


@plugin.subscribe("invoice_payment")
def on_payment(plugin, invoice_payment, **kwargs):

    plugin.log(f"Executing invoice_payment {invoice_payment}", 'info')

    try:
        payment_label = invoice_payment["label"]

        # invoices will always have a unique label
        invoice = plugin.rpc.listinvoices(payment_label)["invoices"][0]

        bind_to = None
        bind_type = None

        # invoices will likely be generated from BOLT 12
        if "local_offer_id" in invoice:
            bind_to = invoice["local_offer_id"]
            bind_type = "bolt12"
        else:
            bind_to = payment_label
            bind_type = "bolt11"

        plugin.log(f"BIND_TYPE: {bind_type}")

        amount_msat = invoice_payment['msat'][:-4]

        plugin.log(
            f"payment_label:  {payment_label}; amount_msat:  {amount_msat}")

        # TODO: return PrismBinding.get as class member rather than json
        binding = PrismBinding.get(plugin, bind_to, bind_type)

        # try:
        binding.pay(amount_msat=int(amount_msat))
        # except Exception as e:
        #     plugin.log(
        #         f"ERROR: there was a problem paying prism {binding.prism.id}. Outlays may not have been updated properly. throwing...{e}")
    
        # invoices can only be paid once, so we delete the bolt11 binding
        if bind_type == "bolt11":
            PrismBinding.delete(plugin, bind_to, bolt_version=bind_type)

    except Exception as e:
        raise Exception("Payment error: {}".format(e))


plugin.run()  # Run our plugin
