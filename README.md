# BOLT12 Prism Plugin

A CLN plugin for creating and interacting with prisms based on [BOLT12](https://bolt12.org). Prism payouts may be executed interactively (e.g., manually or via another CLN plugin), or bound to a BOLT12 offer.

![roygbiv](https://github.com/daGoodenough/bolt12-prism/assets/108303703/2c4ba75d-b0ab-4c3f-a5c4-2202716a04a0)

> _BOLT12 is currently experimental and you will need to add the **--experimental-offers** flag when starting lightningd_

## Background

This started as the winning hackathon project at [bitcoin++](https://btcpp.dev/) 2023 in Austin, Tx.

Other projects that compliment this one include:

- [roygbiv.guide](https://roygbiv.guide) to learn more about prisms.
- [lnplay](https://github.com/farscapian/lnplay) which integrates the prism plugin
- [roygbiv-frontend](https://github.com/johngribbin/ROYGBIV-frontend) helps you manage BOLT12 prisms. TODO hackathon idea: needs UI update to v2 Prisms.

## Getting Started

### Starting the Plugin

There are 3 ways to start a CLN plugin...

### Add to Your Config

Find your c-lightning config file and add

`plugin=/path/to/bolt12-prism.py`

### Manually start the plugin

`lightning-cli plugin start /path/to/bolt12-prism.py`

### Run on startup

`lightningd --experimental-offers --plugin=/path/to/bolt12-prism.py`

## Using the plugin

### Create a prism

`prism-create -k members=members_json prism_id=prism1`

The `prism_id` is optional. If left unspecified, a unique prism id will be assigned.

MEMBERS_JSON=
```json
[{"label" : "Lead-Singer", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqtyh3ua3crhn6me89spfupgp40nxkdfkhp0j2zjk63qgsdxp230ss", "split": 1},{"label" : "Drummer", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqw2ugunkxkzckdwkme9wkzfmjf4f2hm3852906gwsk05lxm0s29fu", "split": 1},{"label" : "Guitarist", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqvqlu8pa98q4wqrvdvyg0svtunw8pa5vj0j9r5mnpzcrjyx8tm7jw", "split": 1}]
```

```bash
lightning-cli prism-create -k members="$MEMBERS_JSON"
```

### List Prism IDs

Let's say you have three prisms defined, one of which you specified and ID for. `prism-list` might look something like this:

`lightning-cli prism-list`

```json
{
   "prism_ids": [
      "1ae57a94-1a57-4d9c-aabe-5da1dd340edd",
      "88a743d1-da8c-4cbe-afdc-9db58e154dc5",
      "prism1"
   ]
}
```

## Show a Prism

Ok cool, you have some prism_ids. Now use `prism-show` to view the prism definition. This document specifies the POLICY of the prism.

`lightning-cli prism-show -k prism_id="prism1"`

```json
{
   "prism_id": "prism1",
   "members": [
      {
         "member_id": "9ec53ec5-40a8-4b27-88ab-daa5f8bff1be",
         "label": "Carol",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqdcrfn0x2eanrs3tgsn4pzlz5vq6w88z48ln2rceuc6eq8yytavhw",
         "split": 2,
         "fees_incurred_by": "remote",
         "payout_threshold": 0
      },
      {
         "member_id": "b121d834-8791-4977-ad24-39f80dc6d070",
         "label": "Erin",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqdszwe3ckdg4mhde9dc4hexv0mhdv2dx7n4p9xyu60t2yu7f9atgs",
         "split": 4,
         "fees_incurred_by": "remote",
         "payout_threshold": 0
      },
      {
         "member_id": "e0a1ec14-9684-47df-bc96-f50e3e1fdbec",
         "label": "Dave",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqtr4svn9a47gnpcjvf6ddyu94eyakmcf6lymaa6ksr9nd62g6mteu",
         "split": 3,
         "fees_incurred_by": "remote",
         "payout_threshold": 0
      }
   ]
}
```

## Prism-Pay - Executes a Payout

`lighting-cli prism-pay -k prism_id=prism1 amount_msat=1000000`

When run, this RPC command will execute (i.e., pay-out) a prism. This is useful if you need to interactively execute a prism payout [another CLN plugin](https://github.com/farscapian/lnplay/tree/tabconf/lnplay/clightning/cln-plugins/lnplaylive). You can specify the optional `label` paramemter to associate this payout to some external `id`.

```json
{
   "prism_member_payouts": {
      "6b5c4165-f423-4d52-a986-be4aefbea67a": {
         "destination": "0305ec405cd73645a5a1c9e73c29b8fe01469d52be73d87a5b5e57750622dbf134",
         "payment_hash": "4d7ad89ad012486a6186ea38742afce2000dfe259383d315444f9ca1f8ffde3c",
         "created_at": 1712443900.723825,
         "parts": 1,
         "amount_msat": 333333,
         "amount_sent_msat": 333333,
         "payment_preimage": "a325ef99b4a36bdf9afd48c6754ac5b5b507334ad9431967b96f2d5d51b78f45",
         "status": "complete"
      },
      "367fca07-da31-4ac7-9ba6-e057a63c331e": {
         "destination": "022806d7df0c1045039fcd99f5f09676b6586418d619458300bdbeeff2d6f149b0",
         "payment_hash": "63d2435e9103a5d6234b0dcecdee4a543d6584c7d700bb92c0a41af7a6c103af",
         "created_at": 1712443901.6540992,
         "parts": 1,
         "amount_msat": 333333,
         "amount_sent_msat": 333333,
         "payment_preimage": "4976661af0af3716f025fcc26f487b19e5a67d87a5c85fc8f599f9c77460e0be",
         "status": "complete"
      },
      "7e2e6a5d-e020-463e-9b4d-491e4cdd864a": {
         "destination": "03dc8bf13244cda303c7faa5cbf53c9ea2bb517ea4580da3c27293383dc4e5831d",
         "payment_hash": "04bc390780a7bdc1f60a09ddad3939a099d9fa74826c4c7e8eaaa1aeda89046f",
         "created_at": 1712443902.566242,
         "parts": 1,
         "amount_msat": 333333,
         "amount_sent_msat": 333333,
         "payment_preimage": "77e9027c6da547754bf86a7bf9cef3a69e35e635b7d86a835e9a499066093788",
         "status": "complete"
      }
   }
}
```

The output above shows the result of paying to each BOLT12 offer specified in `prism1`. Notice they get equal splits in accordance with the prism policy.

## Bindings

Often you will want your prisms to be paid out whenever you have an incoming payment. This is what a binding is for. Note that ONE and ONLY ONE prism can be bound to any given offer.

### Create a binding

`lightning-cli -k prism-bindingadd bind_to=ca9f3342671c27d80b97d0ff44da0f43a7fc0481fa7a103bbd4b1b3a0ad06bd4 prism_id=prism1`

Binds a prism to either a bolt12 offer such that the prism will be executed upon incoming payment.

```json
{
   "status": "must-replace",
   "offer_id": "ca9f3342671c27d80b97d0ff44da0f43a7fc0481fa7a103bbd4b1b3a0ad06bd4",
   "prism_id": "prism1",
   "prism_binding_key": [
      "prism",
      "v2",
      "bind",
      "bolt12",
      "ca9f3342671c27d80b97d0ff44da0f43a7fc0481fa7a103bbd4b1b3a0ad06bd4"
   ],
   "get_prism_members": {
      "7d109925-b8d9-44dc-b8ee-0c63d36da765": {
         "label": "Dave",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqvhf0t2pwm9qpg6y8vvsw97ufrc97j0u4a2rhyhlng3wee09srcaq",
         "split": 3,
         "fees_incurred_by": "remote",
         "payout_threshold": "0msat"
      },
      "f350e291-8608-44b0-8555-3e0147d70f7c": {
         "label": "Carol",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pq0ck6jfedtmkwuf3c7zlhtngj7n3q6s40mw9zq40xq46j506v6wuc",
         "split": 2,
         "fees_incurred_by": "remote",
         "payout_threshold": "0msat"
      },
      "fa7f43c4-082b-46e3-af03-306b93a0b341": {
         "label": "Erin",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqwz2ztkw2w4a6946kwz4ac0upqfsaqwkassragy3jw5zm9z93ehks",
         "split": 4,
         "fees_incurred_by": "remote",
         "payout_threshold": "0msat"
      }
   }
}
```

### List Prism Bindings

Want to see all your bindings? Run `prism-bindinglist`. (Hint, run `prism-bindingshow` to list a specific binding state.)

`lightning-cli -k prism-bindinglist`

```json
{
   "bolt12_prism_bindings": [
      {
         "offer_id": "1c3b55c24b1da141c96a549b994a8632edf66d7440c59ad27fd2b0caf8dcb95b",
         "prism_id": "prism1",
         "member_outlays": {
            "54ed233f-9f20-4e3d-b8d0-8e0c5f0fe95a": "2133328msat",
            "a070caef-e2ef-4ed0-9a2a-83bda5b32123": "2133328msat",
            "87a0210d-99e6-4b78-b525-9cdb03f3be90": "2133328msat",
            "46d96905-13d4-40d9-8729-3c07007271e5": "2133328msat",
            "d1986725-1cd2-40f3-8a80-9095e66be218": "2133328msat",
            "3bc78887-96a5-4e15-ac8d-e9fc4f8d9c76": "2133328msat"
         }
      }
   ]
}
```

Notice that outlay property? That's how the prism plugin deals with failed payments AND Lightning Network fees. When a prism binding has an incoming payment, prism member outlays in the binding are increased according the prism policy and incoming amount.

When a payment to a prism member succeeds, the outlay is decremented by the total amount of the payment (including fees paid when `fees_incurred_by=remote`). When `fees_incurred_by=local` fees are paid by the node operator hosting the prism. Prism member payouts occur when outlays exceed the `payout_threshold` in the respective prism policy. 

If a payment to a prism member fails for whatever reason, the outlay remains unchanged.

<!-- ### Update an existing prism

This command has a similar sytax as `prism-create`. It takes a new `members[]` json object and updates `prism_id` to have the new members defintion. -->

<!-- ### Deletes a prism

Running `prism-delete prism_id` will delete a prism object from the data store. Note that any prism bindings related to `prism_id` will also be deleted. -->

`prism-bindingremove prism_id invoice_type invoice_label`
    Removes a prism binding. -->

## Contributing

There is a copy of the [startup_regtest](https://github.com/ElementsProject/lightning/blob/master/contrib/startup_regtest.sh) script from the c-lightning repo [contrib dir](./contrib/) for local development. See [roygbiv.guide/contact](roygbiv.guide/contact) to join our Telegram.