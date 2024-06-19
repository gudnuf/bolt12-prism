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

- [roygbiv.guide](https://roygbiv.guide) to learn more about prisms.
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
[{"description" : "Guitarist", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqtk39j62x7m9qvkfep23m6euet54xfyp5xsyye7lavp0jmug06zxy", "split": 0.333333, "payout_threshold_msat": "5000000", "fees_incurred_by": "local"},{"description" : "Drums", "destination": "02e4cc35ff6e7d43edc71db8146ae558f5b00a6d1e783e9ab10ad63bd82975502c", "split": 0.333333, "payout_threshold_msat": "10000000", "fees_incurred_by": "remote"},{"description" : "Tuba", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pq0s2x4jx6v7jtwzu4zf3f3nst03z3wcnwdjamr7mlk8axt70hvkd6", "split": 0.333333, "payout_threshold_msat": "5000000", "fees_incurred_by": "local"}]
```

```bash
lightning-cli prism-create -k description="Band Prism" members="$MEMBERS_JSON" outlay_factor="0.8"
```

```json
{
   "prism_id": "f0ab738d7a7dd92004e8c0f2bd9426d33b22288f2964c5634e019000cfd8353d",
   "description": "Band Prism",
   "timestamp": 1718764199,
   "outlay_factor": 0.8,
   "prism_members": [
      {
         "member_id": "c0772494d0d83318cf47ea1dbabcf3e37df2218090f9f20585867f135c241279",
         "description": "Guitarist",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqtk39j62x7m9qvkfep23m6euet54xfyp5xsyye7lavp0jmug06zxy",
         "split": 0.333333,
         "fees_incurred_by": "local",
         "payout_threshold_msat": 5000000
      },
      {
         "member_id": "d624d9b334b06d84560f1095d153001cb8ae829a8270d6fe29fa6d715efd538d",
         "description": "Drums",
         "destination": "02e4cc35ff6e7d43edc71db8146ae558f5b00a6d1e783e9ab10ad63bd82975502c",
         "split": 0.333333,
         "fees_incurred_by": "remote",
         "payout_threshold_msat": 10000000
      },
      {
         "member_id": "3f921a0dc8b927d8389aed3536e2b4596c4bcfac752bc674ac1025523c25e42b",
         "description": "Tuba",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pq0s2x4jx6v7jtwzu4zf3f3nst03z3wcnwdjamr7mlk8axt70hvkd6",
         "split": 0.333333,
         "fees_incurred_by": "local",
         "payout_threshold_msat": 5000000
      }
   ]
}
```

Setting the `outlay_factor` to `0.8` means that total outlays will be only 80% of the incoming amount. This is an implicit "pay-to-self" of 20%. This feature allows a Prism member to host the prism. Note that if `destination` is a pubkey, then [keysend](https://docs.corelightning.org/reference/lightning-keysend) is used for payouts.

### Delete a prism

Need to delete a prism from the database? Use `prism-delete prism_id`. Be sure to remove any bindings first (see below)!

### List prisms

Run the following command to view a prism policy. (Note that you can add a `prism_id` and specific prism will be returned.)

`lightning-cli prism-list`

```json
{
   "prisms": [
      {
         "prism_id": "f0ab738d7a7dd92004e8c0f2bd9426d33b22288f2964c5634e019000cfd8353d",
         "description": "prism1",
         "timestamp": 1718722200,
         "outlay_factor": 0.8,
         "prism_members": [
            {
               "member_id": "b2dd7d8a70567a0e23308a6a77b38d603eaf2baca5da320082184a9951063a95",
               "description": "Carol",
               "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pq0d9gxlr2q2c9rp0lkqjyztvwcl8g7gzjgu2trnwll8lraquy35vq",
               "split": 1.0,
               "fees_incurred_by": "local",
               "payout_threshold_msat": 5000000
            },
            {
               "member_id": "809a721743350c0c49a7b444ad3aeaf1341fdd48d1bf510e08b008edab72dc70",
               "description": "Dave",
               "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqwv5lnjcufs7jmsh2r7wmj45mp35z822tz69n2j07gy64qn475j2c",
               "split": 1.0,
               "fees_incurred_by": "remote",
               "payout_threshold_msat": 10000000
            },
            {
               "member_id": "849dc45741d52a071b0ed4ca14b7a182e82fcad6a60cf9b0025c903411263085",
               "description": "Erin",
               "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqwfg6tm3xapdfr0q0lqr3q5sujzznv3f9ff6wfvhl36m6scf3wzpy",
               "split": 1.0,
               "fees_incurred_by": "local",
               "payout_threshold_msat": 5000000
            }
         ]
      }
   ]
}
```

## Prism-Pay - Executes a Payout

`lightning-cli prism-pay -k prism_id=f0ab738d7a7dd92004e8c0f2bd9426d33b22288f2964c5634e019000cfd8353d amount_msat=10000000`

When run, this RPC command will execute (i.e., pay-out) a prism. 

> WARNING! prism-pay DOES NOT have an associated income event to account for payouts! Consider adding a binding so that fees can be tracked by maintaing a member outlay. Also, Prism payouts via `prism-pay` DO NOT respect the `payment_threshold` since this is only relevant to bindings. 

```json
{
   "prism_member_payouts": {
      "c0772494d0d83318cf47ea1dbabcf3e37df2218090f9f20585867f135c241279": {
         "destination": "02ed12cb4a37b65032c9c8551deb3ccae9532481a1a04267dfeb02f96f887e8462",
         "payment_hash": "556de902e890674edc26af197e95f5e7b9281f8d104381d7c03cacf8cbcca5ea",
         "created_at": 1718764199.7347724,
         "parts": 1,
         "amount_msat": 2666666,
         "amount_sent_msat": 2666666,
         "payment_preimage": "70253f59527db2191d45d95be86ca47e593684f7e426710f24529612216b1172",
         "status": "complete"
      },
      "d624d9b334b06d84560f1095d153001cb8ae829a8270d6fe29fa6d715efd538d": {
         "destination": "02e4cc35ff6e7d43edc71db8146ae558f5b00a6d1e783e9ab10ad63bd82975502c",
         "payment_hash": "61c58e680b30751b8b5435280d435639ae6feef67d3b7c38aa2d0ebc6ab359a2",
         "created_at": 1718764200.7018805,
         "parts": 1,
         "amount_msat": 2666666,
         "amount_sent_msat": 2666666,
         "payment_preimage": "3ac15217d8f62c4c5d301b0f3a22794f9bfcaad496a20488fbc64318da893091",
         "status": "complete"
      },
      "3f921a0dc8b927d8389aed3536e2b4596c4bcfac752bc674ac1025523c25e42b": {
         "destination": "03e0a35646d33d25b85ca89314c6705be228bb137365dd8fdbfd8fd32fcfbb2cdd",
         "payment_hash": "97f31109bc0fcb07491a4b73b6d63d0a5d8ccdc3234123d70dd2cfd651825168",
         "created_at": 1718764201.6202407,
         "parts": 1,
         "amount_msat": 2666666,
         "amount_sent_msat": 2666666,
         "payment_preimage": "11ccae76acd177b40ebc324de0a1fb29c79b97e0d6ad3adc61883d8a4c6ee5bb",
         "status": "complete"
      }
   }
}
```

The output above shows the result of paying to each BOLT12 offer specified in `prism1`. Notice they get equal splits in accordance with the prism policy.

## Bindings

Often you will want your prisms to be paid out whenever you have an incoming payment. This is what a binding is for. Note that ONE and ONLY ONE prism can be bound to any given offer.

### Create a binding

`lightning-cli prism-bindingadd -k offer_id=c618514017a44b7bcce8edd842ad057bfde4fe0fdef0b00cec840c7264c8e08d prism_id=f0ab738d7a7dd92004e8c0f2bd9426d33b22288f2964c5634e019000cfd8353d`

The above command binds a prism (`prism_id`) to a bolt12 offer with the specified `offer_id`.

```json
{
   "status": "must-create",
   "timestamp": 1718764200,
   "offer_id": "c618514017a44b7bcce8edd842ad057bfde4fe0fdef0b00cec840c7264c8e08d",
   "prism_id": "f0ab738d7a7dd92004e8c0f2bd9426d33b22288f2964c5634e019000cfd8353d",
   "prism_binding_key": [
      "prism",
      "v2",
      "bind",
      "bolt12",
      "c618514017a44b7bcce8edd842ad057bfde4fe0fdef0b00cec840c7264c8e08d"
   ],
   "prism_members": [
      {
         "member_id": "c0772494d0d83318cf47ea1dbabcf3e37df2218090f9f20585867f135c241279",
         "description": "Guitarist",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqtk39j62x7m9qvkfep23m6euet54xfyp5xsyye7lavp0jmug06zxy",
         "split": 0.333333,
         "fees_incurred_by": "local",
         "payout_threshold_msat": 5000000
      },
      {
         "member_id": "d624d9b334b06d84560f1095d153001cb8ae829a8270d6fe29fa6d715efd538d",
         "description": "Drums",
         "destination": "02e4cc35ff6e7d43edc71db8146ae558f5b00a6d1e783e9ab10ad63bd82975502c",
         "split": 0.333333,
         "fees_incurred_by": "remote",
         "payout_threshold_msat": 10000000
      },
      {
         "member_id": "3f921a0dc8b927d8389aed3536e2b4596c4bcfac752bc674ac1025523c25e42b",
         "description": "Tuba",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pq0s2x4jx6v7jtwzu4zf3f3nst03z3wcnwdjamr7mlk8axt70hvkd6",
         "split": 0.333333,
         "fees_incurred_by": "local",
         "payout_threshold_msat": 5000000
      }
   ]
}
```

### List Prism Bindings

Want to see your bindings? Run `prism-bindinglist`. Add an `offer_id` to view a specific binding.

`lightning-cli -k prism-bindinglist -k offer_id=c618514017a44b7bcce8edd842ad057bfde4fe0fdef0b00cec840c7264c8e08d`

```json
{
   "bolt12_prism_bindings": [
      {
         "offer_id": "c618514017a44b7bcce8edd842ad057bfde4fe0fdef0b00cec840c7264c8e08d",
         "prism_id": "f0ab738d7a7dd92004e8c0f2bd9426d33b22288f2964c5634e019000cfd8353d",
         "timestamp": 1718764200,
         "member_outlays": [
            {
               "member_id": "c0772494d0d83318cf47ea1dbabcf3e37df2218090f9f20585867f135c241279",
               "outlay_msat": 0
            },
            {
               "member_id": "d624d9b334b06d84560f1095d153001cb8ae829a8270d6fe29fa6d715efd538d",
               "outlay_msat": 5333330
            },
            {
               "member_id": "3f921a0dc8b927d8389aed3536e2b4596c4bcfac752bc674ac1025523c25e42b",
               "outlay_msat": -1866669
            }
         ]
      }
   ]
}
```

The `outlay_msat` property is how the prism plugin deals with failed payments and to account for payout fees. When a prism binding has an incoming payment, prism member outlays in the binding are increased according the prism policy and incoming amount. When `fees_incurred_by=remote` and a payment to a prism member succeeds, the outlay is decremented by the total amount of the payment including fees paid. When `fees_incurred_by=local`, fees are paid by the node operator hosting the prism.

Prism member payouts occur when outlays exceed the `payout_threshold_msat` in the respective prism policy. Until then, outlays accumulate and eventually get paid-out.

If a payment to a prism member fails for whatever reason, the outlay remains unchanged and payout is deferred.

### Set a Binding Member Outlay

Say you have outstanding outlays that aren't clearing for whatever reason (e.g., unreachable node in offer). If you know the individual, you can always remit the sats with another wallet. In those cases, you will want to first zeroize the outlays for that member in the binding:

`lightning-cli prism-bindingmemberoutlayreset -k offer_id=c618514017a44b7bcce8edd842ad057bfde4fe0fdef0b00cec840c7264c8e08d member_id=3f921a0dc8b927d8389aed3536e2b4596c4bcfac752bc674ac1025523c25e42b new_outlay_msat="-2500000"`

```json
{
   "bolt12_prism_bindings": {
      "offer_id": "c618514017a44b7bcce8edd842ad057bfde4fe0fdef0b00cec840c7264c8e08d",
      "prism_id": "f0ab738d7a7dd92004e8c0f2bd9426d33b22288f2964c5634e019000cfd8353d",
      "timestamp": 1718764200,
      "member_outlays": [
         {
            "member_id": "c0772494d0d83318cf47ea1dbabcf3e37df2218090f9f20585867f135c241279",
            "outlay_msat": 1066666
         },
         {
            "member_id": "d624d9b334b06d84560f1095d153001cb8ae829a8270d6fe29fa6d715efd538d",
            "outlay_msat": 6399996
         },
         {
            "member_id": "3f921a0dc8b927d8389aed3536e2b4596c4bcfac752bc674ac1025523c25e42b",
            "outlay_msat": -2500000
         }
      ]
   }
}
```

Note that since we're tracking outlays, if they actually owe us money, we can set the outlay value to a negative number. As income events flow in, the outlay will eventually turn positive again, accounting for what they owe us.

### Remove a binding

You can remove a binding by running `prism-bindingremove offer_id`.

## How to contribute

There is a copy of the [startup_regtest](https://github.com/ElementsProject/lightning/blob/master/contrib/startup_regtest.sh) script from the c-lightning repo [contrib dir](./contrib/) for local development. Consider joining our Telegram group at [roygbiv.guide/contact](https://www.roygbiv.guide/contact).