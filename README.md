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
[{"label" : "Lead-Singer", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqtyh3ua3crhn6me89spfupgp40nxkdfkhp0j2zjk63qgsdxp230ss", "split": 1},{"label" : "Drummer", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqw2ugunkxkzckdwkme9wkzfmjf4f2hm3852906gwsk05lxm0s29fu", "split": 1},{"label" : "Guitarist", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqvqlu8pa98q4wqrvdvyg0svtunw8pa5vj0j9r5mnpzcrjyx8tm7jw", "split": 1}]
```

```bash
lightning-cli prism-create -k members="$MEMBERS_JSON"
```

### Delete a prism

Need to delete a prism from the database? Use `prism-delete prism_id`. Be sure to remove any bindings first (see below)!

### List prisms

Run the following command to view a prism policy. (Note that you can omit the `prism_id` and all prisms will be returned.)

`lightning-cli prism-list prism1`

```json
{
   "prism_id": "prism1",
   "timestamp": 1714759630,
   "prism_members": [
      {
         "member_id": "e2548e67-f0a6-4203-b43d-d0edc0c2964a",
         "label": "Carol",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqvdt6lccaa4fw3dgw4dczt8ae8v69999j0uyrrsfhepg7tqwg2k4z",
         "split": 1,
         "fees_incurred_by": "remote",
         "payout_threshold_msat": "0"
      },
      {
         "member_id": "9a64efaa-3ac8-4b2d-af4b-36ab1846acdd",
         "label": "Dave",
         "destination": "03e5700104d1b6e2602a2dfda5b497d9c6862597865d46e3ded8404bf4067250e2",
         "split": 1,
         "fees_incurred_by": "remote",
         "payout_threshold_msat": "0"
      },
      {
         "member_id": "4faf43bc-5595-4239-90d1-576cbe1caf91",
         "label": "Erin",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqdeza5wk7pdd674uv2nzcgprvlwxjtjxman4ezl6j3ghh0wq65u7v",
         "split": 1,
         "fees_incurred_by": "remote",
         "payout_threshold_msat": "0"
      }
   ]
}
```

## Prism-Pay - Executes a Payout

`lighting-cli prism-pay -k prism_id=prism1 amount_msat=1000000`

When run, this RPC command will execute (i.e., pay-out) a prism. This is useful if you need to interactively execute a prism payout [another CLN plugin](https://github.com/farscapian/lnplay/tree/tabconf/lnplay/clightning/cln-plugins/lnplaylive). You can specify the optional `label` paramemter to associate this payout to some external `id`.

> Note, Prism payouts via `prism-pay` DO NOT respect the payment_threshold. Your node will pay for all member payout fees when using `prism-pay`. Consider adding a binding so that fees can be tracked by maintaing a member outlay.

```json
{
   "prism_member_payouts": {
      "2503e139-760c-48fc-90f0-66e88780ece4": {
         "destination": "03ae4baabcf7e547ff58bad3813e31bca65499fa11016aa24c80d896a510727597",
         "payment_hash": "055ac5c154baac2032c4c2474521c2c410eb9326cc5d0c8d4345bc33cddc3b09",
         "created_at": 1714760131.4795787,
         "parts": 1,
         "amount_msat": 3333333,
         "amount_sent_msat": 3333333,
         "payment_preimage": "c062d69c2ca7f3e1d57de969f992a20880f4a2d01408597dcc386c412bf14450",
         "status": "complete"
      },
      "03d6c054-2593-462d-9f68-4fd81bc0aa28": {
         "destination": "036c6757c0e30eacd0c8188946b437f5adb5dac5afe1cc5b60b63a56e67be382c0",
         "payment_hash": "ae92fe81c2c9d1801c0f27793e3227eeba78a3a11b09732adca0ce2600c7dace",
         "created_at": 1714760132.606286,
         "parts": 1,
         "amount_msat": 3333333,
         "amount_sent_msat": 3333333,
         "payment_preimage": "801c67c5c3d006b3ef94a2e40c77b4b9cb61432b1e60cb6754aaaf5e0d05dec2",
         "status": "complete"
      },
      "091a8fe9-a8bc-48ae-8fba-7ac33ebd961b": {
         "destination": "02872086d7d910374b7b55c203f37fa7137361dc78c2919ea7d2565779c583ded2",
         "payment_hash": "97292fcf635405d33775d55e5362ba591a342b747102ab3dd0414164405be3df",
         "created_at": 1714760133.739254,
         "parts": 1,
         "amount_msat": 3333333,
         "amount_sent_msat": 3333333,
         "payment_preimage": "99b6fb7097a391e2558afc5b8bee377578c92b2691d18ddebbd79b78afe438aa",
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
   "timestamp": 1714760131,
   "bind_to": "ecbb23dd33aeea4ca3c9198bdf459b004b455f13bbe72554be15a5aab4100ce6",
   "prism_id": "prism1",
   "prism_binding_key": [
      "prism",
      "v2",
      "bind",
      "bolt12",
      "ecbb23dd33aeea4ca3c9198bdf459b004b455f13bbe72554be15a5aab4100ce6"
   ],
   "prism_members": [
      {
         "member_id": "2503e139-760c-48fc-90f0-66e88780ece4",
         "label": "Carol",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqwhyh24u7lj50l6chtfcz033hjn9fx06zyqk4gjvsrvfdfgswf6ew",
         "split": 1,
         "fees_incurred_by": "remote",
         "payout_threshold_msat": "0"
      },
      {
         "member_id": "03d6c054-2593-462d-9f68-4fd81bc0aa28",
         "label": "Dave",
         "destination": "036c6757c0e30eacd0c8188946b437f5adb5dac5afe1cc5b60b63a56e67be382c0",
         "split": 1,
         "fees_incurred_by": "remote",
         "payout_threshold_msat": "0"
      },
      {
         "member_id": "091a8fe9-a8bc-48ae-8fba-7ac33ebd961b",
         "label": "Erin",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pq2rjppkhmygrwjmm2hpq8uml5ufhxcwu0rpfr8486ft9w7w9s00dy",
         "split": 1,
         "fees_incurred_by": "remote",
         "payout_threshold_msat": "0"
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
         "offer_id": "ecbb23dd33aeea4ca3c9198bdf459b004b455f13bbe72554be15a5aab4100ce6",
         "prism_id": "prism1",
         "timestamp": 1714760131,
         "member_outlays": {
            "2503e139-760c-48fc-90f0-66e88780ece4": "0msat",
            "03d6c054-2593-462d-9f68-4fd81bc0aa28": "0msat",
            "091a8fe9-a8bc-48ae-8fba-7ac33ebd961b": "0msat"
         }
      }
   ]
}
```

Notice that outlay property? That's how the prism plugin deals with failed payments AND Lightning Network fees. When a prism binding has an incoming payment, prism member outlays in the binding are increased according the prism policy and incoming amount.

When `fees_incurred_by=remote` and a payment to a prism member succeeds, the outlay is decremented by the total amount of the payment including fees paid. When `fees_incurred_by=local`, fees are paid by the node operator hosting the prism. Prism member payouts occur when outlays exceed the `payout_threshold_msat` in the respective prism policy. Until then, outlays accumulate and eventually get paid-out. 

If a payment to a prism member fails for whatever reason, the outlay remains unchanged.

### Remove a binding

You can remove a binding by running `prism-bindingremove offer_id`.

## How to contribute

There is a copy of the [startup_regtest](https://github.com/ElementsProject/lightning/blob/master/contrib/startup_regtest.sh) script from the c-lightning repo [contrib dir](./contrib/) for local development. Consider joining our Telegram group at [roygbiv.guide/contact](roygbiv.guide/contact).