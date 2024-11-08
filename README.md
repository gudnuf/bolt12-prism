[![main on CLN v24.02.2](https://github.com/gudnuf/bolt12-prism/actions/workflows/main_v24.02.yml/badge.svg?branch=main)](https://github.com/gudnuf/bolt12-prism/actions/workflows/main_v24.02.yml)

# BOLT12 Prism Plugin

A CLN plugin for creating and interacting with prisms based on [BOLT12](https://bolt12.org). Prism payouts may be executed interactively (e.g., manually or via another CLN plugin), or bound to a BOLT12 offer.

![roygbiv](https://github.com/daGoodenough/bolt12-prism/assets/108303703/2c4ba75d-b0ab-4c3f-a5c4-2202716a04a0)

> _BOLT12 is currently experimental and you will need to add the **--experimental-offers** flag when starting lightningd_

## WARNING

> This software should be considered for Testing and Evaluation purposes only!

## Background

This started as the winning hackathon project at [bitcoin++](https://btcpp.dev/) 2023 in Austin, Tx.

Other projects that compliment this one include:

- [roygbiv.guide](https://roygbiv.guide), a BOLT12-prism native [Value4Value](https://value4value.info/) website.
- [lnplay](https://github.com/farscapian/lnplay) which integrates the prism plugin

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

MEMBERS_JSON=
```json
[{"description" : "Drummer", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqwtzkujnk4t5hteur6cn8aqyt3v38u300ldryz6z2fw7zwr4gjxcq", "split": 1.0, "payout_threshold_msat": "0", "fees_incurred_by": "local"},{"description" : "Guitarist", "destination": "02dbfb1d0a6fbc717ae3f28e4dc185d812e399ee33055587eeb06469c94e4326e5", "split": 1.0, "payout_threshold_msat": "0", "fees_incurred_by": "remote"},{"description" : "Tuba", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqvzk2archeau0slmv7dlsvwlrcra6pxml6mdwxetsml0hhcp9w4cu", "split": 1.0, "payout_threshold_msat": "0", "fees_incurred_by": "local"}]'
```

```bash
lightning-cli prism-create -k description="Band Prism" members="$MEMBERS_JSON" outlay_factor="0.75"
```

```json
{
   "prism_id": "a59afe3927e6cdce218fb82415574204df4f762bb9c2c535a420488b3fa5fbf5",
   "description": "Band Prism",
   "timestamp": 1720044718,
   "outlay_factor": 0.75,
   "prism_members": [
      {
         "member_id": "95256245897c5423f9c319afbcd224dba9902cb829991a2435e2902631810389",
         "description": "Drummer",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqwtzkujnk4t5hteur6cn8aqyt3v38u300ldryz6z2fw7zwr4gjxcq",
         "split": 1.0,
         "fees_incurred_by": "local",
         "payout_threshold_msat": 0
      },
      {
         "member_id": "412c79d6feafdf907a348ddb15627ba057d2c3ac3615f8f41680acd176d8bc2d",
         "description": "Guitarist",
         "destination": "02dbfb1d0a6fbc717ae3f28e4dc185d812e399ee33055587eeb06469c94e4326e5",
         "split": 1.0,
         "fees_incurred_by": "remote",
         "payout_threshold_msat": 0
      },
      {
         "member_id": "ebc13b1be16346e8e08571cbde85f5eb604cd76233181b5edbd559e3f35858ab",
         "description": "Tuba",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqvzk2archeau0slmv7dlsvwlrcra6pxml6mdwxetsml0hhcp9w4cu",
         "split": 1.0,
         "fees_incurred_by": "local",
         "payout_threshold_msat": 0
      }
   ]
}
```

Setting the `outlay_factor` to `0.75` means that total outlays will be only 75% of the incoming amount. This is an implicit "pay-to-self" of 25%. This feature allows a Prism member to host the prism.

> An `outlay_factor` of `1.1` means total outlays will be 110% of incoming events. The extra 10% is paid by the prism host. This can be used for [matching funds](https://en.wikipedia.org/wiki/Matching_funds).

Split percentages are normalized over all members of the prism. So, in the case above, each prism member will receive an equal split (i.e., 33.33%) of the total outlays.


### Update a Prism

There's a command called `prism-update` that takes a MEMBERS_JSON similar to `prism-create`. Note your members JSON MUST include `member_id` elements, which are provided when creating the prism for the first time.

### Delete a prism

Need to delete a prism from the database? Use `prism-delete prism_id`. Be sure to remove any bindings first (see below)!

### List prisms

Run the following command to view a prism policy. (Note that you can add a `prism_id` and specific prism will be returned.)

`lightning-cli prism-list`

```json
{
   "prisms": [
      {
         "prism_id": "4cf1e1b3e7bea1d0b8f9612ed138f164a03abe4541b1e82c8cde16af050b4f53",
         "description": "Band Prism",
         "timestamp": 1720042032,
         "outlay_factor": 0.75,
         "prism_members": [
            {
               "member_id": "547d51d513aec15dc2229047d6d912b63d39416e3682b6dee4d6ae686f88b9b4",
               "description": "Drummer",
               "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqwt5tgjxynmyjjx0zjcssjx9z5h377kewwa4k2zqtu0k8k47sscvv",
               "split": 1.0,
               "fees_incurred_by": "local",
               "payout_threshold_msat": 0
            },
            {
               "member_id": "1fdda73dbdd4d3dda4057cf302ec10dedfc55466163133fd236e313a60a52204",
               "description": "Guitarist",
               "destination": "030e7553729959098adc3b63df389be92fbe0ca756a5469ba71364fc44c1338ac7",
               "split": 1.0,
               "fees_incurred_by": "remote",
               "payout_threshold_msat": 0
            },
            {
               "member_id": "22dad0bd9cfcf4adfa367d2627e80a7a92e531b60a3d7c006495258c57b9db5e",
               "description": "Tuba",
               "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pq2zlvjv9s9she2fpj0msp6jz0sgrl7wgm425fc6rhdkhcqtqlggks",
               "split": 1.0,
               "fees_incurred_by": "local",
               "payout_threshold_msat": 0
            }
         ]
      }
   ]
}
```

## Prism-Pay - Executes a Payout

`lightning-cli prism-pay -k prism_id=a59afe3927e6cdce218fb82415574204df4f762bb9c2c535a420488b3fa5fbf5 amount_msat=10000000`

When run, this RPC command will execute (i.e., pay-out) a prism. 

> WARNING! prism-pay DOES NOT have an associated income event to account for payouts! Consider adding a binding so that fees can be tracked by maintaing a member outlay. Also, Prism payouts via `prism-pay` DOES NOT respect the `payout_threshold_msat` value  which is only relevant to bindings. 

```json
{
   "prism_member_payouts": {
      "547d51d513aec15dc2229047d6d912b63d39416e3682b6dee4d6ae686f88b9b4": {
         "destination": "03a43dce86b0c2bd0b18d97e28f045be5866c94bff3ca8a96e5a4a370f469e26b9",
         "payment_hash": "89ea468a04f5747882b21d4f50d13e353b3d346a50d5ba80f8f94000d0596cc1",
         "created_at": 1721069260.3575482,
         "parts": 1,
         "amount_msat": 2500000,
         "amount_sent_msat": 2500000,
         "payment_preimage": "11eaaa9cc7e0e8a27038130ecad56bb766d0ed5e09d202e313ea06620344abec",
         "status": "complete"
      },
      "1fdda73dbdd4d3dda4057cf302ec10dedfc55466163133fd236e313a60a52204": {
         "destination": "0273d97fd40ac7c17fd9bd6476316edf44aafcf25a41ef9c36b941b2fe4396c4de",
         "payment_hash": "c773cb2cdb6c1fc5478c972effa75588f2b6e63f11005a475dc052f5c48f82ce",
         "created_at": 1721069261.4327104,
         "parts": 1,
         "amount_msat": 2500000,
         "amount_sent_msat": 2500000,
         "payment_preimage": "0ba602d4ebd33bead0947c244360963dedead47c2a79eb35ca2afebdfa0bf37d",
         "status": "complete"
      },
      "22dad0bd9cfcf4adfa367d2627e80a7a92e531b60a3d7c006495258c57b9db5e": {
         "destination": "02e36cf99a16ac84446bcd60258ce2a0a6e334346b07ee647b88fce18c6d4fe3a0",
         "payment_hash": "325de28046cc828644169be6a03e1dceef1896cf30822ccb32ed10ff88eb5ef2",
         "created_at": 1721069262.5050325,
         "parts": 1,
         "amount_msat": 2500000,
         "amount_sent_msat": 2500000,
         "payment_preimage": "730e0b6ab952cb681ccb5c7b84bc7b507790bb70bbb88156bbbec0d2c7f84f45",
         "status": "complete"
      }
   }
}
```

The output above shows the result of paying to each BOLT12 offer specified in `prism1`. Notice they get equal splits in accordance with the prism policy.

## Bindings

Often you will want your prisms to be paid out whenever you have an incoming payment. This is what a binding is for. Note that ONE and ONLY ONE prism can be bound to any given offer.

### Create a binding

`lightning-cli prism-addbinding -k offer_id=70761889e73c049ce243b3ac73e06533830e4cdf8dbc3a5717b05bab93c7af64 prism_id=a59afe3927e6cdce218fb82415574204df4f762bb9c2c535a420488b3fa5fbf5`

The above command binds a prism (`prism_id`) to a bolt12 offer with the specified `offer_id`.

```json
{
   "status": "must-create",
   "timestamp": 1720044718,
   "offer_id": "70761889e73c049ce243b3ac73e06533830e4cdf8dbc3a5717b05bab93c7af64",
   "prism_id": "a59afe3927e6cdce218fb82415574204df4f762bb9c2c535a420488b3fa5fbf5",
   "prism_binding_key": [
      "prism",
      "v2.1",
      "bind",
      "bolt12",
      "70761889e73c049ce243b3ac73e06533830e4cdf8dbc3a5717b05bab93c7af64"
   ],
   "prism_members": [
      {
         "member_id": "95256245897c5423f9c319afbcd224dba9902cb829991a2435e2902631810389",
         "description": "Drummer",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqwtzkujnk4t5hteur6cn8aqyt3v38u300ldryz6z2fw7zwr4gjxcq",
         "split": 1.0,
         "fees_incurred_by": "local",
         "payout_threshold_msat": 0
      },
      {
         "member_id": "412c79d6feafdf907a348ddb15627ba057d2c3ac3615f8f41680acd176d8bc2d",
         "description": "Guitarist",
         "destination": "02dbfb1d0a6fbc717ae3f28e4dc185d812e399ee33055587eeb06469c94e4326e5",
         "split": 1.0,
         "fees_incurred_by": "remote",
         "payout_threshold_msat": 0
      },
      {
         "member_id": "ebc13b1be16346e8e08571cbde85f5eb604cd76233181b5edbd559e3f35858ab",
         "description": "Tuba",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqvzk2archeau0slmv7dlsvwlrcra6pxml6mdwxetsml0hhcp9w4cu",
         "split": 1.0,
         "fees_incurred_by": "local",
         "payout_threshold_msat": 0
      }
   ]
}
```

### List Prism Bindings

Want to see your bindings? Run `prism-listbindings`. Add an `offer_id` to view a specific binding.

`lightning-cli -k prism-listbindings -k offer_id=dfa361b51238e8ffc4c5db74105d618090e1c7fd48442d3e735dcaaf35347b6f`

```json
{
   "bolt12_prism_bindings": [
      {
         "offer_id": "dfa361b51238e8ffc4c5db74105d618090e1c7fd48442d3e735dcaaf35347b6f",
         "prism_id": "4cf1e1b3e7bea1d0b8f9612ed138f164a03abe4541b1e82c8cde16af050b4f53",
         "timestamp": 1720042032,
         "member_outlays": [
            {
               "member_id": "547d51d513aec15dc2229047d6d912b63d39416e3682b6dee4d6ae686f88b9b4",
               "outlay_msat": 50000000
            },
            {
               "member_id": "1fdda73dbdd4d3dda4057cf302ec10dedfc55466163133fd236e313a60a52204",
               "outlay_msat": 0
            },
            {
               "member_id": "22dad0bd9cfcf4adfa367d2627e80a7a92e531b60a3d7c006495258c57b9db5e",
               "outlay_msat": 0
            }
         ]
      }
   ]
}
```

The `outlay_msat` property is how the prism plugin deals with failed payments and to account for payout fees. When a prism binding has an incoming payment, prism member outlays in the binding are increased according the prism policy and incoming amount. When `fees_incurred_by=remote` and a payment to a prism member succeeds, the outlay is decremented by the total amount of the payment including fees paid. When `fees_incurred_by=local`, fees are paid by the node operator hosting the prism.

Prism member payouts occur when outlays exceed the `payout_threshold_msat` in the respective prism policy. Until then, outlays accumulate. Similarly, if a payout to a prism member fails for whatever reason, the outlay remains unchanged and payout is deferred.

### Set a Binding Member Outlay

Say you have outstanding outlays that aren't clearing for whatever reason (e.g., unreachable node in offer). If you know the individual, you can always remit the sats with another wallet. In those cases, you will want to first zeroize the outlays for that member in the binding using the `prism-setoutlay` method.

`lightning-cli prism-setoutlay -k offer_id=dfa361b51238e8ffc4c5db74105d618090e1c7fd48442d3e735dcaaf35347b6f member_id=547d51d513aec15dc2229047d6d912b63d39416e3682b6dee4d6ae686f88b9b4 new_outlay_msat=0`

```json
{
   "bolt12_prism_bindings": {
      "offer_id": "dfa361b51238e8ffc4c5db74105d618090e1c7fd48442d3e735dcaaf35347b6f",
      "prism_id": "4cf1e1b3e7bea1d0b8f9612ed138f164a03abe4541b1e82c8cde16af050b4f53",
      "timestamp": 1720042032,
      "member_outlays": [
         {
            "member_id": "547d51d513aec15dc2229047d6d912b63d39416e3682b6dee4d6ae686f88b9b4",
            "outlay_msat": 0
         },
         {
            "member_id": "1fdda73dbdd4d3dda4057cf302ec10dedfc55466163133fd236e313a60a52204",
            "outlay_msat": 0
         },
         {
            "member_id": "22dad0bd9cfcf4adfa367d2627e80a7a92e531b60a3d7c006495258c57b9db5e",
            "outlay_msat": 0
         }
      ]
   }
}
```

Note that since we're tracking outlays, if they actually owe us money, we can set the outlay value to a negative number. As income events flow in, the outlay will eventually turn positive again, accounting for what they owe us.

### Remove a binding

You can remove a binding by running `prism-deletebinding offer_id`.



## How to contribute

There is a copy of the [startup_regtest](https://github.com/ElementsProject/lightning/blob/master/contrib/startup_regtest.sh) script from the c-lightning repo [contrib dir](./contrib/) for local development. Consider joining our Telegram group at [roygbiv.guide/contribute](https://www.roygbiv.guide/contribute).