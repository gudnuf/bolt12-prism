#!/usr/bin/env python3
from pyln.client import Plugin, RpcError
from lib import Prism, Member, PrismBinding
import re

plugin = Plugin()

@plugin.init()  # Decorator to define a callback once the `init` method call has successfully completed
def init(options, configuration, plugin, **kwargs):

    getinfoResult = plugin.rpc.getinfo()
    clnVersion = getinfoResult["version"]
    #searchString = 'v24.03'
    numbers = re.findall(r'v(\d+)\.', clnVersion)
    major_cln_version = int(numbers[0]) if numbers else None
    #plugin.log(f"major_cln_version: {major_cln_version}")
    if major_cln_version is not None:
        if major_cln_version < 24:
            raise Exception("The BOLT12 Prism plugin is only compatible with CLN v24 and above.")

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

    plugin.log(f"prism-bindingsbindinghow executed for {bolt_version} offer '{bind_to}'", "info")

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

@plugin.method("prism-bindingremove")
def remove_prism_binding(plugin, offer_id, prism_id, bolt_version="bolt12"):
    '''Removes a prism binding.'''

    try:
        binding = PrismBinding.get(plugin, offer_id, bolt_version)

        if not binding:
            raise Exception("ERROR: could not find a binding for this offer.")

        plugin.log(f"Attempting to delete a prism binding for {offer_id}.", "info")

        recordDeleted = False
        recordDeleted = PrismBinding.delete(plugin, bind_to=offer_id)

        return { "binding_removed": recordDeleted }

    except:
        raise Exception(f"ERROR: Could not find a binding for offer {offer_id}.")


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


@plugin.method("prism-pay")
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

    return {
            "prism_member_payouts": pay_results
        }


@plugin.subscribe("invoice_payment")
def on_payment(plugin, invoice_payment, **kwargs):

    #plugin.log(f"Incoming invoice_payment {invoice_payment}", 'info')

    # try:
    payment_label = invoice_payment["label"]
    #plugin.log(f"payment_label: {payment_label}")
    # invoices will always have a unique label
    invoice = plugin.rpc.listinvoices(payment_label)["invoices"][0]

    if invoice is None:
        return

    bind_to = None
    bind_type = None

    # invoices will likely be generated from BOLT 12
    if "local_offer_id" in invoice:
        bind_to = invoice["local_offer_id"]
        bind_type = "bolt12"
    else:
        bind_to = payment_label
        bind_type = "bolt11"

    # TODO: return PrismBinding.get as class member rather than json
    binding = None
    binding = PrismBinding.get(plugin, bind_to, bind_type)

    plugin.log(f"test1")

    #plugin.log(f"binding: {binding.id}")

    if not binding:
        plugin.log("Incoming payment not associated with prism binding. Nothing to do.", "info")
        return

    plugin.log(f"test2")

    # try:
    amount_msat = invoice_payment['msat']
    plugin.log(f"amount_msat: {amount_msat}")
    binding.pay(amount_msat=int(amount_msat))
    plugin.log(f"test3")
    # except Exception as e:
    #     plugin.log(
    #         f"ERROR: something went wrong with binding payout {binding.prism.id}. {e}")
    

    # invoices can only be paid once, so we delete the bolt11 binding
    if bind_type == "bolt11":
        PrismBinding.delete(plugin, bind_to, bolt_version=bind_type)

    # except Exception as e:
    #     plugin.log(f"invoice_payment has no prism bindings.", "info")

plugin.run()  # Run our plugin
