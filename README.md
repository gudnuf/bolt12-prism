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

### Delete a prism

Need to delete a prism from the database? Use `prism-delete prism_id`. Be sure to remove any bindings first (see below)!

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
   "prism_members": [
      {
         "member_id": "0922ff11-15fb-428f-9607-fd3ad9096964",
         "label": "Carol",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqdtj0zz3uhtcys42fnkhmvn96spym62l25xa69knd6kp3jncaf3py",
         "split": 1,
         "fees_incurred_by": "remote",
         "payout_threshold": "0msat"
      },
      {
         "member_id": "394c41d9-a9a6-4c5d-916f-083105ec35b7",
         "label": "Dave",
         "destination": "0258dc215bef8eca15ceb424aea162519cbc40d0b9b0eb107339bc7432de51c0e1",
         "split": 1,
         "fees_incurred_by": "remote",
         "payout_threshold": "0msat"
      },
      {
         "member_id": "02eceb88-b64d-4129-b861-cb5c3d231a46",
         "label": "Erin",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pq0f0y265urvvj5sp2wqdr0m2w53ec56elpanvd6x5zk6mw0awcl85",
         "split": 1,
         "fees_incurred_by": "remote",
         "payout_threshold": "0msat"
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
      "0922ff11-15fb-428f-9607-fd3ad9096964": {
         "destination": "0357278851e5d78242aa4ced7db265d4024de95f550ddd16d36eac18ca78ea6212",
         "payment_hash": "871aa78ad8b30dc95bb24a50dc76de33f17e2ebb17b1689970fd1bc17e826751",
         "created_at": 1714147772.989214,
         "parts": 1,
         "amount_msat": 33333,
         "amount_sent_msat": 33333,
         "payment_preimage": "17de2266ce2cce92b1523593b46ffe18b582542f6d3e6135884ff57a89247413",
         "status": "complete"
      },
      "394c41d9-a9a6-4c5d-916f-083105ec35b7": {
         "destination": "0258dc215bef8eca15ceb424aea162519cbc40d0b9b0eb107339bc7432de51c0e1",
         "payment_hash": "356a7fcc43ad4c329553cfe925688f6148b933396094e6fcbac0310dd29c04c9",
         "created_at": 1714147773.9578664,
         "parts": 1,
         "amount_msat": 33333,
         "amount_sent_msat": 33333,
         "payment_preimage": "146e5eee75d84f5d779ca3e0ab8538dc04940b8026fd5d54a4cb60651139c353",
         "status": "complete"
      },
      "02eceb88-b64d-4129-b861-cb5c3d231a46": {
         "destination": "03d2f22b54e0d8c952015380d1bf6a75239c5359f87b363746a0adadb9fd763e7a",
         "payment_hash": "e586f808e8381cfc8750ffed8c32dbd0d7c25040caae983cb20b59ee9ebed99b",
         "created_at": 1714147774.9850466,
         "parts": 1,
         "amount_msat": 33333,
         "amount_sent_msat": 33333,
         "payment_preimage": "fa6071450e296e80d0de9ae5bc1f54e25891b8650955353bda3a45a57320ed5d",
         "status": "complete"
      }
   }
}
```

The output above shows the result of paying to each BOLT12 offer specified in `prism1`. Notice they get equal splits in accordance with the prism policy.

## Bindings

Often you will want your prisms to be paid out whenever you have an incoming payment. This is what a binding is for. Note that ONE and ONLY ONE prism can be bound to any given offer.

### Create a binding

`lightning-cli -k prism-bindingadd -k offer_id=64b2eaba3882444833eda9bab3535d836f1976753613729427c374bcbba04913 prism_id=prism1`

Binds a prism to either a bolt12 offer such that the prism will be executed upon incoming payment.

```json
{
   "status": "must-create",
   "bind_to": "64b2eaba3882444833eda9bab3535d836f1976753613729427c374bcbba04913",
   "prism_id": "prism1",
   "prism_binding_key": [
      "prism",
      "v2",
      "bind",
      "bolt12",
      "64b2eaba3882444833eda9bab3535d836f1976753613729427c374bcbba04913"
   ],
   "prism_members": [
      {
         "member_id": "0922ff11-15fb-428f-9607-fd3ad9096964",
         "label": "Carol",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqdtj0zz3uhtcys42fnkhmvn96spym62l25xa69knd6kp3jncaf3py",
         "split": 1,
         "fees_incurred_by": "remote",
         "payout_threshold": "0msat"
      },
      {
         "member_id": "394c41d9-a9a6-4c5d-916f-083105ec35b7",
         "label": "Dave",
         "destination": "0258dc215bef8eca15ceb424aea162519cbc40d0b9b0eb107339bc7432de51c0e1",
         "split": 1,
         "fees_incurred_by": "remote",
         "payout_threshold": "0msat"
      },
      {
         "member_id": "02eceb88-b64d-4129-b861-cb5c3d231a46",
         "label": "Erin",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pq0f0y265urvvj5sp2wqdr0m2w53ec56elpanvd6x5zk6mw0awcl85",
         "split": 1,
         "fees_incurred_by": "remote",
         "payout_threshold": "0msat"
      }
   ]
}
```

### List Prism Bindings

Want to see all your bindings? Run `prism-bindinglist`. Add an `offer_id` to view a specific binding.

`lightning-cli -k prism-bindinglist`

```json
{
   "bolt12_prism_bindings": [
      {
         "offer_id": "64b2eaba3882444833eda9bab3535d836f1976753613729427c374bcbba04913",
         "prism_id": "prism1",
         "member_outlays": {
            "0922ff11-15fb-428f-9607-fd3ad9096964": "0msat",
            "394c41d9-a9a6-4c5d-916f-083105ec35b7": "0msat",
            "02eceb88-b64d-4129-b861-cb5c3d231a46": "0msat"
         }
      }
   ]
}
```

Notice that outlay property? That's how the prism plugin deals with failed payments AND Lightning Network fees. When a prism binding has an incoming payment, prism member outlays in the binding are increased according the prism policy and incoming amount.

When `fees_incurred_by=remote` and a payment to a prism member succeeds, the outlay is decremented by the total amount of the payment including fees paid. When `fees_incurred_by=local`, fees are paid by the node operator hosting the prism. Prism member payouts occur when outlays exceed the `payout_threshold` in the respective prism policy. Until then, outlays accumulate and eventually get paid-out. 

If a payment to a prism member fails for whatever reason, the outlay remains unchanged.

### Remove a binding

You can remove a binding by running `prism-bindingremove offer_id`.

## How to contribute

There is a copy of the [startup_regtest](https://github.com/ElementsProject/lightning/blob/master/contrib/startup_regtest.sh) script from the c-lightning repo [contrib dir](./contrib/) for local development. Consider joining our Telegram group at [roygbiv.guide/contact](roygbiv.guide/contact).