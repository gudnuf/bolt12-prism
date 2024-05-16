[![main on CLN v24.02.2](https://github.com/gudnuf/bolt12-prism/actions/workflows/main_v24.02.yml/badge.svg?branch=main)](https://github.com/gudnuf/bolt12-prism/actions/workflows/main_v24.02.yml)

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
[{"label" : "Carol", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqtrvcsycd8dqycyzsqp3nf8kjtjw448ad2sxclmsqe4yv2ry885pw", "split": 1, "payout_threshold_msat": "500000"},{"label" : "Dave", "destination": "02ffefcc4240dd5f339e6e451f0eceadd7e1f2d3c3b74ae256f53b6ae8f575d91a", "split": 1, "payout_threshold_msat": "500000"},{"label" : "Erin", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pq2a9lj8dwfgefqvnl7yc8jyhtcxxhzdzq5memcz7769ja3c0jzvys", "split": 1, "payout_threshold_msat": "500000"}]'
```

```bash
lightning-cli prism-create -k members="$MEMBERS_JSON"
```

```json
{
   "prism_id": "prism1",
   "timestamp": 1715877268,
   "outlay_factor": 0.8,
   "prism_members": [
      {
         "member_id": "1c00f7de-fd5e-4b21-a869-2a79226e8275",
         "label": "Carol",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqvqmtjepktzl0sqz6fhadxphh7mmnrjxc6sjlf0schhjmm86yd57x",
         "split": 1,
         "fees_incurred_by": "remote",
         "payout_threshold_msat": "500000"
      },
      {
         "member_id": "841f869b-1a8b-4153-9a44-1fd50ce53989",
         "label": "Dave",
         "destination": "023fe8d7f9fddf9568cc31c1b0cf339d965a522166f9d1e3185186023d311922cf",
         "split": 1,
         "fees_incurred_by": "remote",
         "payout_threshold_msat": "500000"
      },
      {
         "member_id": "28c5107d-e18b-4b99-8706-dac6ad8017cb",
         "label": "Erin",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pq0nqkyg3z3hh6mhse7naf8njpdyzuw0067zj35vcelp6u8r3zkc3j",
         "split": 1,
         "fees_incurred_by": "remote",
         "payout_threshold_msat": "500000"
      }
   ]
}
```

Setting the `outlay_factor` to `0.8` means that total outlays will be only 80% of the incoming amount. This is an implicit "pay-to-self". This feature allows a Prism member to host a prism.

### Delete a prism

Need to delete a prism from the database? Use `prism-delete prism_id`. Be sure to remove any bindings first (see below)!

### List prisms

Run the following command to view a prism policy. (Note that you can add a `prism_id` and specific prism will be returned.)

`lightning-cli prism-list`

```json
{
   "prisms": {
      "prism_id": "prism1",
      "timestamp": 1715879764,
      "outlay_factor": 0.8,
      "prism_members": [
         {
            "member_id": "088db12c-5bbc-4ecd-bd9f-66553f6dc277",
            "label": "Carol",
            "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqtrvcsycd8dqycyzsqp3nf8kjtjw448ad2sxclmsqe4yv2ry885pw",
            "split": 1,
            "fees_incurred_by": "remote",
            "payout_threshold_msat": "500000"
         },
         {
            "member_id": "1cfa8bf2-f251-4891-ae08-b812d214fa07",
            "label": "Dave",
            "destination": "02ffefcc4240dd5f339e6e451f0eceadd7e1f2d3c3b74ae256f53b6ae8f575d91a",
            "split": 1,
            "fees_incurred_by": "remote",
            "payout_threshold_msat": "500000"
         },
         {
            "member_id": "fb639dd9-8d07-4ca9-9fbc-5ae08505627a",
            "label": "Erin",
            "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pq2a9lj8dwfgefqvnl7yc8jyhtcxxhzdzq5memcz7769ja3c0jzvys",
            "split": 1,
            "fees_incurred_by": "remote",
            "payout_threshold_msat": "500000"
         }
      ]
   }
}
```

## Prism-Pay - Executes a Payout

`lighting-cli prism-pay -k prism_id=prism1 amount_msat=1000000`

When run, this RPC command will execute (i.e., pay-out) a prism. This is useful if you need to interactively execute a prism payout [another CLN plugin](https://github.com/farscapian/lnplay/tree/tabconf/lnplay/clightning/cln-plugins/lnplaylive). You can specify the optional `label` paramemter to associate this payout to some external `id`.

> Note, Prism payouts via `prism-pay` DO NOT respect the payment_threshold. Your node will pay for all member payout fees when using `prism-pay`. Consider adding a binding so that fees can be tracked by maintaing a member outlay.

```json
{
   "prism_member_payouts": {
      "088db12c-5bbc-4ecd-bd9f-66553f6dc277": {
         "destination": "02c6cc409869da026082800319a4f692e4ead4fd6aa06c7f70066a46286439e817",
         "payment_hash": "abb1fcaaaacd541969d1edaebd5f9f01c6da75f333daaab124a813c0c3be55fc",
         "created_at": 1715879764.8129447,
         "parts": 1,
         "amount_msat": 3333333,
         "amount_sent_msat": 3333333,
         "payment_preimage": "b4abf87c99cf6861161083fc35e7483b7d88a685394d8f70fb92324a4afc5fd7",
         "status": "complete"
      },
      "1cfa8bf2-f251-4891-ae08-b812d214fa07": {
         "destination": "02ffefcc4240dd5f339e6e451f0eceadd7e1f2d3c3b74ae256f53b6ae8f575d91a",
         "payment_hash": "ef6c217ce60c2ef048bc308060eb76a39d91c36f4ce36cf579669a056270fe33",
         "created_at": 1715879765.7926252,
         "parts": 1,
         "amount_msat": 3333333,
         "amount_sent_msat": 3333333,
         "payment_preimage": "0f95f40f4ff52ab9b4a22f75f8769e750ac231e142bf1597c449c635f3738610",
         "status": "complete"
      },
      "fb639dd9-8d07-4ca9-9fbc-5ae08505627a": {
         "destination": "02ba5fc8ed7251948193ff8983c8975e0c6b89a205379de05ef68b2ec70f909848",
         "payment_hash": "12f4cf34789dfb73d3162b3f204c97d7a28ee6d8c7ff5689db994ed67da4b207",
         "created_at": 1715879766.762006,
         "parts": 1,
         "amount_msat": 3333333,
         "amount_sent_msat": 3333333,
         "payment_preimage": "9e82e3ff68a84d8937923028a76052898ec9366d9f08ae7ce0b5a26ac4d6a77f",
         "status": "complete"
      }
   }
}
```

The output above shows the result of paying to each BOLT12 offer specified in `prism1`. Notice they get equal splits in accordance with the prism policy.

## Bindings

Often you will want your prisms to be paid out whenever you have an incoming payment. This is what a binding is for. Note that ONE and ONLY ONE prism can be bound to any given offer.

### Create a binding

`lightning-cli -k prism-bindingadd -k offer_id=458f1a21f5d24158dd756c44735f11fe688d4d5d0d97fd8b33235b634a2ca52f prism_id=prism1`

Binds a prism to either a bolt12 offer such that the prism will be executed upon incoming payment.

```json
{
   "status": "must-create",
   "timestamp": 1715879765,
   "bind_to": "2a5afc3132b75e6c30a3ad932507f83c27c57fa96e56a6ff856b67db9e12d9a9",
   "prism_id": "prism3",
   "prism_binding_key": [
      "prism",
      "v2",
      "bind",
      "bolt12",
      "2a5afc3132b75e6c30a3ad932507f83c27c57fa96e56a6ff856b67db9e12d9a9"
   ],
   "prism_members": [
      {
         "member_id": "064e2765-6773-4177-8c83-218e48fce2e4",
         "label": "Carol",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqtrvcsycd8dqycyzsqp3nf8kjtjw448ad2sxclmsqe4yv2ry885pw",
         "split": 1,
         "fees_incurred_by": "remote",
         "payout_threshold_msat": "500000"
      },
      {
         "member_id": "180e2490-c389-4926-8325-819d00d497de",
         "label": "Dave",
         "destination": "02ffefcc4240dd5f339e6e451f0eceadd7e1f2d3c3b74ae256f53b6ae8f575d91a",
         "split": 1,
         "fees_incurred_by": "remote",
         "payout_threshold_msat": "500000"
      },
      {
         "member_id": "ae1aecc2-ff10-487e-9221-271050ce4949",
         "label": "Erin",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pq2a9lj8dwfgefqvnl7yc8jyhtcxxhzdzq5memcz7769ja3c0jzvys",
         "split": 1,
         "fees_incurred_by": "remote",
         "payout_threshold_msat": "500000"
      }
   ]
}
```

### List Prism Bindings

Want to see your bindings? Run `prism-bindinglist`. Add an `offer_id` to view a specific binding.

`lightning-cli -k prism-bindinglist 2a5afc3132b75e6c30a3ad932507f83c27c57fa96e56a6ff856b67db9e12d9a9`

```json
{
   "bolt12_prism_bindings": {
      "binding_id": "09793f96dc7e633423765f1ecd5f4e4acba10d193a56918a92f482eeef104cd7",
      "offer_id": "2a5afc3132b75e6c30a3ad932507f83c27c57fa96e56a6ff856b67db9e12d9a9",
      "prism_id": "prism3",
      "timestamp": 1715879765,
      "member_outlays": [
         {
            "member_id": "064e2765-6773-4177-8c83-218e48fce2e4",
            "outlay_msat": "0"
         },
         {
            "member_id": "180e2490-c389-4926-8325-819d00d497de",
            "outlay_msat": "0"
         },
         {
            "member_id": "ae1aecc2-ff10-487e-9221-271050ce4949",
            "outlay_msat": "0"
         }
      ]
   }
}
```

Notice that outlay property? That's how the prism plugin deals with failed payments AND Lightning Network fees. When a prism binding has an incoming payment, prism member outlays in the binding are increased according the prism policy and incoming amount.

When `fees_incurred_by=remote` and a payment to a prism member succeeds, the outlay is decremented by the total amount of the payment including fees paid. When `fees_incurred_by=local`, fees are paid by the node operator hosting the prism. Prism member payouts occur when outlays exceed the `payout_threshold_msat` in the respective prism policy. Until then, outlays accumulate and eventually get paid-out. 

If a payment to a prism member fails for whatever reason, the outlay remains unchanged.

### Remove a binding

You can remove a binding by running `prism-bindingremove offer_id`.

## How to contribute

There is a copy of the [startup_regtest](https://github.com/ElementsProject/lightning/blob/master/contrib/startup_regtest.sh) script from the c-lightning repo [contrib dir](./contrib/) for local development. Consider joining our Telegram group at [roygbiv.guide/contact](roygbiv.guide/contact).