#!/usr/bin/env python3

try:
    from pyln.client import Plugin, RpcError
    from lib import Prism, Member, PrismBinding
    import re
except ModuleNotFoundError as err:
    # OK, something is not installed?
    import json
    import sys
    getmanifest = json.loads(sys.stdin.readline())
    print(json.dumps({'jsonrpc': "2.0",
                      'id': getmanifest['id'],
                      'result': {'disable': str(err)}}))
    sys.exit(1)


plugin = Plugin()

@plugin.init()  # Decorator to define a callback once the `init` method call has successfully completed
def init(options, configuration, plugin, **kwargs):

    getinfoResult = plugin.rpc.getinfo()
    clnVersion = getinfoResult["version"]
    #searchString = 'v24.03'
    numbers = re.findall(r'v(\d+)\.', clnVersion)
    major_cln_version = int(numbers[0]) if numbers else None
    #plugin.log(f"major_cln_version: {major_cln_version}")
    if major_cln_version != None:
        if major_cln_version < 24:
            raise Exception("The BOLT12 Prism plugin is only compatible with CLN v24 and above.")

    plugin.log("prism-api initialized")


@plugin.method("prism-create")
def createprism(plugin, members, prism_id="", outlay_factor: float = 1.0, pay_to_self_enabled: bool = False):
    '''Create a prism.'''

    plugin.log(f"prism-create invoked having an outlay_factor of {outlay_factor}", "info")

    prism_members = [Member(plugin=plugin, member_dict=m) for m in members]

    # create a new prism object (this is used for our return object only)
    prism = Prism.create(plugin=plugin, prism_id=prism_id, members=prism_members, outlay_factor=outlay_factor)

    # now we want to create a unique offer that is associated with this prism
    # this offer facilitates pay-to-self-destination use case.
    if pay_to_self_enabled == True:
        create_offer_response = plugin.rpc.offer(amount="any", description=prism_id, label=f"internal:prism:{prism_id}")
        ptsd_offer_id = create_offer_response["offer_id"]
        plugin.log(f"In prism-create. Trying to create a PTSD offer binding. here's the ptsd_offer_bolt12 {ptsd_offer_id}")
        bind_prism_response = bindprism(plugin=plugin, prism_id=prism.id, offer_id=ptsd_offer_id)

    # return the prism json
    return prism.to_dict()

@plugin.method("prism-list")
def listprisms(plugin, prism_id=None):
    '''List prisms.'''
    # if a prism_id is not supplied, we return all prism policy objects (like in listoffers)
    if prism_id == None:
        try:
            prism_ids = Prism.find_all(plugin)
            prisms = []
            for prism_id in prism_ids:
                prism = Prism.get(plugin=plugin, prism_id=prism_id)
                prisms.append(prism)

            return {
                "prisms": [prism.to_dict() for prism in prisms]
            }

        except RpcError as e:
            plugin.log(e)
            return e
    else:
        # otherwise we return a single document.
        prism = Prism.get(plugin=plugin, prism_id=prism_id)

        if prism is None:
            raise Exception(f"Prism with id {prism_id} not found.")

        return {
                "prisms": prism.to_dict()
            }



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

        prism.update(members=updated_members)

        # return prism as a dict
        return prism.to_dict()

    except RpcError as e:
        plugin.log(e)
        return e


@plugin.method("prism-bindinglist")
def list_bindings(plugin, offer_id=None, invoice_label=""):
    '''Lists all prism bindings.'''

    bolt12_prism_response = None
    
    # if an offer_id is not supplied and also an invoice_label, then we return all bindings.
    if offer_id == None and invoice_label == "":

        binding_offers = PrismBinding.list_binding_offers(plugin)
        prism_response = {
            f"bolt12_prism_bindings": [binding.to_dict() for binding in binding_offers]
        }

    if offer_id != None:

        # then we're going to return a single binding.
        binding = PrismBinding.get(plugin, offer_id)

        if not binding:
            raise Exception("ERROR: could not find a binding for this offer.")

        plugin.log(f"prism-bindingslist executed for '{offer_id}'", "info")

        prism_response = {
            f"bolt12_prism_bindings": binding.to_dict()
        }

    if offer_id == None and invoice_label != "":

        # then we're going to return a single binding.
        binding = PrismBinding.get(plugin, bind_to=invoice_label, bolt_version="bolt11")

        if not binding:
            raise Exception("ERROR: could not find a binding for this offer.")

        plugin.log(f"prism-bindingslist executed for '{offer_id}'", "info")

        prism_response = {
            f"bolt11_prism_bindings": binding.to_dict()
        }

    return prism_response



# adds a binding to the database.
@plugin.method("prism-bindingadd")
def bindprism(plugin: Plugin, prism_id, offer_id=None, invoice_label=""):
    '''Binds a prism to a BOLT12 Offer or a BOLT11 invoice.'''

    plugin.log(f"In bindprism with prism_id={prism_id} and offer_id={offer_id}.", "info")

    trigger = None

    bolt_version = None
    bind_to = None
    if  offer_id == None and invoice_label != "":
        bolt_version = "bolt11"
        bind_to = invoice_label
    elif offer_id != None:
        bolt_version = "bolt12"
        bind_to = offer_id
    else:
        raise Exception("bindprism was has some issues.")

    # ensure the offer/invoice exists
    if bolt_version == "bolt12":
        trigger = plugin.rpc.listoffers(offer_id=offer_id)["offers"]

        if [trigger] == []:
            raise Exception("ERROR: the bolt12 offer does not exist!")

    elif bolt_version == "bolt11":
        trigger = plugin.rpc.listinvoices(label=invoice_label)["invoices"]

        if trigger == []:
            raise Exception("ERROR: the bolt11 invoice does not exist.")

    add_binding_result = PrismBinding.add_binding(
        plugin=plugin, bind_to=bind_to, prism_id=prism_id,
        bolt_version=bolt_version
        )

    return add_binding_result

@plugin.method("prism-bindingremove")
def remove_prism_binding(plugin, offer_id=None, invoice_label=""):
    '''Removes a prism binding.'''

    ## TODO implement invoice_label
    bolt_version = "bolt12"
    if invoice_label != "" and offer_id == None:
        bolt_version = "bolt11"

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


@plugin.method("prism-delete")
def delete_prism(plugin, prism_id):
    '''Deletes a prism.'''
    prism_to_delete = Prism.get(plugin=plugin, prism_id=prism_id)

    # prism should exist
    if prism_to_delete is None:
        raise Exception(f"Prism with ID {prism_id} does not exist.")

    # prism should not have bindings
    if len(prism_to_delete.bindings) != 0:
        raise Exception(
            f"This prism has existing bindings! Use prism-bindingremove [offer_id=] before attempting to delete prism '{prism_id}'.")
    
    plugin.log(f"prism_to_delete {prism_to_delete}", "debug")

    try:
        deleted_data = prism_to_delete.delete()
        return {"deleted": deleted_data}

    except RpcError as e:
        raise Exception(f"Prism with ID {prism_id} does not exist.")

@plugin.method("prism-pay")
def prism_execute(plugin, prism_id, amount_msat=0, label=""):
    '''Executes (pays-out) a prism.'''

    plugin.log(
        f"In prism-pay with prism_ID {prism_id} and amount = {amount_msat}")

    if not isinstance(amount_msat, int):
        raise Exception("ERROR: amount_msat is the incorrect type.")

    if amount_msat <= 0:
        raise Exception("ERROR: amount_msat must be greater than 0.")

    prism = Prism.get(plugin, prism_id)

    if prism is None:
        raise Exception("ERROR: could not find prism.")

    pay_results = prism.pay(amount_msat=amount_msat)

    return {
            "prism_member_payouts": pay_results
        }

@plugin.subscribe("invoice_payment")
def on_payment(plugin, invoice_payment, **kwargs):

    # try:
    payment_label = invoice_payment["label"]
    #plugin.log(f"payment_label: {payment_label}")
    # invoices will always have a unique label
    invoice = plugin.rpc.listinvoices(payment_label)["invoices"][0]

    if invoice is None:
        return

    bind_to = None
    bolt_version = None

    # invoices will likely be generated from BOLT 12
    if "local_offer_id" in invoice:
        bind_to = invoice["local_offer_id"]
        bolt_version = "bolt12"
    else:
        bind_to = payment_label
        bolt_version = "bolt11"

    # TODO: return PrismBinding.get as class member rather than json
    binding = None
    binding = PrismBinding.get(plugin, bind_to, bolt_version)

    if not binding:
        plugin.log("Incoming payment not associated with prism binding. Nothing to do.", "info")
        return

    # try:
    amount_msat = invoice_payment['msat']
    plugin.log(f"amount_msat: {amount_msat}")
    binding.pay(amount_msat=int(amount_msat))

    # invoices can only be paid once, so we delete the bolt11 binding
    if bolt_version == "bolt11":
        PrismBinding.delete(plugin, bind_to, bolt_version=bolt_version)

plugin.run()  # Run our plugin
