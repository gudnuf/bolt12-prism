#!/usr/bin/env python3
import json
import os
import re
from math import floor
from pyln.client import Plugin, RpcError, LightningRpc, Millisatoshi

plugin = Plugin()

pubkeyRegex = re.compile(r'^0[2-3][0-9a-fA-F]{64}$')
bolt12Regex = re.compile(
    r'^ln([a-zA-Z0-9]{1,90})[0-9]+[munp]?[a-zA-Z0-9]+[0-9]+[munp]?[a-zA-Z0-9]*$')


@plugin.init()  # Decorator to define a callback once the `init` method call has successfully completed
def init(options, configuration, plugin, **kwargs):
    plugin.log("prism plugin initialized")


@plugin.method("createprism")
def createprism(plugin, label, members):
    try:
        validate_members(members)

        plugin.log(f"Members: {members}")

        path = os.path.join(plugin.lightning_dir, plugin.rpc_filename)
        lrpc = LightningRpc(path)

        # returns object containing bolt12 offer
        offer = lrpc.offer("any", label)
        offer_id = offer["offer_id"]
        plugin.log(f"Offer: {offer}")

        datastore = lrpc.listdatastore(offer_id)["datastore"]
        if any(offer_id in d['key'] for d in datastore):
            raise Exception('Existing offer already exists')

        # add the prism info to datastore with the offer_id as the key
        lrpc.datastore(offer["offer_id"],
                       string=json.dumps({"label": label, "bolt12": offer["bolt12"], "offer_id":offer_id, "members": members}))

        return offer
    except RpcError as e:
        plugin.log(e)
        return e


@plugin.method("listprisms")
def listprisms(plugin):
    try:
        path = os.path.join(plugin.lightning_dir, plugin.rpc_filename)
        lrpc = LightningRpc(path)

        offers = lrpc.listoffers()["offers"]
        offer_ids = [offer["offer_id"] for offer in offers]

        datastore = lrpc.listdatastore()["datastore"]

        # extract all datastore entries with a key that matches our offer_ids
        prisms = [i for i in datastore if any(
            offer_id in i["key"] for offer_id in offer_ids)]

        prism_data_string = list(
            map(lambda prism: prism['string'].replace('\\"', '"'), prisms))

        prism_data_json = list(
            map(lambda prism: json.loads(prism), prism_data_string))

        return {"prisms": prism_data_json}
    except RpcError as e:
        plugin.log(e)
        return e
    
@plugin.method("deleteprism")
def deleteprism(plugin, offer_id):
    try:
        path = os.path.join(plugin.lightning_dir, plugin.rpc_filename)
        lrpc = LightningRpc(path)

        prisms = get_prism_json(lrpc)["prisms"]

        if any(offer_id in d['offer_id'] for d in prisms):
            lrpc.deldatastore(offer_id)
            lrpc.disableoffer(offer_id)

        else:
            raise Exception(f'Offer {offer_id} not found')

        return {"message":"Successfully removed prism and disabled the bolt12 offer"}

    except RpcError as e:
        plugin.log(e)
        return e


plugin.add_option('destination', 'destination', 'default_destination')


@plugin.subscribe("invoice_payment")
def on_payment(plugin, invoice_payment, **kwargs):
    try:
        offer_id = invoice_payment["label"].split("-")[0]

        path = os.path.join(plugin.lightning_dir, plugin.rpc_filename)
        lrpc = LightningRpc(path)

        datastore = lrpc.listdatastore(offer_id)
        data_string = datastore['datastore'][0]['string'].replace('\\"', '"')
        data_json = json.loads(data_string)

        # returns list of members or empty list
        members = data_json.get("members", [])

        # determine how many satoshis to send each member
        total_split = sum(map(lambda member: member['split'], members))

        payment_results = []
        for member in members:
            # iterate over each prism member and send them their split
            # msat comes as "5000msat"
            deserved_msats = floor((member['split'] / total_split) *
                                   int(invoice_payment['msat'][:-4]))

            if member.get("type") == "keysend":
                try:
                    payment = lrpc.keysend(destination=member["destination"], amount_msat=Millisatoshi(
                        deserved_msats))

                    result = create_payment_result(member, payment)

                    payment_results.append(result)

                except RpcError as e:
                    result = create_payment_result(member, {}, e)
                    payment_results.append(result)

            else:
                try:
                    invoice_obj = lrpc.fetchinvoice(offer=member["destination"], amount_msat=Millisatoshi(
                        deserved_msats))

                    payment = lrpc.pay(bolt11=invoice_obj["invoice"])

                    result = create_payment_result(member, payment)
                    payment_results.append(result)

                except RpcError as e:
                    result = create_payment_result(member, {}, e)
                    payment_results.append(result)

        plugin.log(f"{payment_results}")

    except RpcError as e:
        plugin.log(e)
        return e


def get_prism_json(lrpc):
    try:
        offers = lrpc.listoffers()["offers"]
        offer_ids = [offer["offer_id"] for offer in offers]

        datastore = lrpc.listdatastore()["datastore"]

        # extract all datastore entries with a key that matches our offer_ids
        prisms = [i for i in datastore if any(
            offer_id in i["key"] for offer_id in offer_ids)]

        prism_data_string = list(
            map(lambda prism: prism['string'].replace('\\"', '"'), prisms))

        prism_data_json = list(
            map(lambda prism: json.loads(prism), prism_data_string))

        return {"prisms": prism_data_json}
    except RpcError as e:
        plugin.log(e)
        return e


def validate_members(members):
    if len(members) < 2:
        raise ValueError("Prism must contain at least two members")

    if not isinstance(members, list):
        raise ValueError("Members must be a list.")

    for member in members:
        if not isinstance(member, dict):
            raise ValueError("Each member in the list must be a dictionary.")

        required_keys = ["name", "destination", "split"]
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
            plugin.log("bolt12 destination")
            valid_destination = member["destination"] if bolt12Regex.match(
                member["destination"]) else None

        if "type" in member and member["type"] == "keysend":
            plugin.log("keysend destination")
            valid_destination = member["destination"] if pubkeyRegex.match(
                member["destination"]) else None

        if valid_destination is None:
            raise Exception(
                "Destination must be a valid lightning node pubkey or bolt12 offer")


def create_payment_result(member, payment, error=None):
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
            "created_at": payment["created_at"],
            "error_message": ""
        }
    return result


plugin.run()  # Run our plugin
