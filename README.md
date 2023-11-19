# BOLT 12 Prism Plugin

A CLN plugin for creating and interacting with prisms. This plugin supports receiving to BOLT12 offers or BOLT11 invoices, and paying prism out to either BOLT12 or keysend destinations. In addition, prism payouts may be executed manually (e.g., via another CLN plugin).

![roygbiv](https://github.com/daGoodenough/bolt12-prism/assets/108303703/2c4ba75d-b0ab-4c3f-a5c4-2202716a04a0)

> _BOLT12 is currently experimental and you will need to add the **--experimental-offers** flag when starting lightningd_

## Background

This started as the winning hackathon project at [bitcoin++](https://btcpp.dev/) 2023 in Austin, Tx.

Some other projects that compliment this one are

- [roygbiv.guide](https://roygbiv.guide) to learn more about prisms.
- [lnplay](https://github.com/farscapian/lnplay) which integrates the prism plugin
- [roygbiv-frontend](https://github.com/johngribbin/ROYGBIV-frontend) helps you manage BOLT12 prisms. TODO hackathon idea: needs UI update to v2 Prisms.

## Getting Started

### Verify your node can create offers.

1. `lightning-cli offer any label`
2. You should get a response like this:

   ```
   {
      "offer_id": "75a463ad38b27e83be53c802d3419592e005e130d29d5ea09b788d68816a46ff",
      "active": true,
      "single_use": false,
      "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2q5mngwpnxstzzql8sxrnaaq8secwrcsw5wmdxtfqgj9kamaslpvgxk08g0tdmqzmav",
      "used": false,
      "created": true
   }
   ```

### Starting the Plugin

There are 3 ways to start a CLN plugin...

### Add to Your Config

Find your c-lightning config file and add

`plugin=/path/to/prism.py`

### Manually start the plugin

`lightning-cli plugin start /path/to/prism.py`

### Run on startup

`lightningd --experimental-offers --plugin=/path/to/prism.py`

## Using the plugin

`prism-create members [prism_id]` - Create a prism

Syntax: `prism-create -k members=members_json prism_id=prism-xxx`. The `prism_id` is optional. If left unspecified, a unique prism id starting with `prism-` will be assigned. Note that if you specify a `prism_id`, it MUST start with `prism-`. [Here's an example script](https://github.com/farscapian/lnplay/blob/tabconf/channel_templates/create_prism.sh).

```bash
lightning-cli prism-create -k 'members=[{"name" : "Lead-Singer", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqtyh3ua3crhn6me89spfupgp40nxkdfkhp0j2zjk63qgsdxp230ss", "split": 1, "type":"bolt12"},{"name" : "Drummer", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqw2ugunkxkzckdwkme9wkzfmjf4f2hm3852906gwsk05lxm0s29fu", "split": 1, "type":"bolt12"},{"name" : "Guitarist", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqvqlu8pa98q4wqrvdvyg0svtunw8pa5vj0j9r5mnpzcrjyx8tm7jw", "split": 1, "type":"bolt12"}]'
```

Returns the the following:

```
{
   "prism_id": "prism-127.0.0.1-prism_demo",
   "version": "v0.0.2",
   "sdf": "relative",
   "members": [
      {
         "name": "Lead-Singer",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqtyh3ua3crhn6me89spfupgp40nxkdfkhp0j2zjk63qgsdxp230ss",
         "split": 1,
         "type": "bolt12",
         "outlay_msats": 0,
         "fees_incurred_by": "remote",
         "threshold": 0
      },
      {
         "name": "Drummer",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqw2ugunkxkzckdwkme9wkzfmjf4f2hm3852906gwsk05lxm0s29fu",
         "split": 1,
         "type": "bolt12",
         "outlay_msats": 0,
         "fees_incurred_by": "remote",
         "threshold": 0
      },
      {
         "name": "Guitarist",
         "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqvqlu8pa98q4wqrvdvyg0svtunw8pa5vj0j9r5mnpzcrjyx8tm7jw",
         "split": 1,
         "type": "bolt12",
         "outlay_msats": 0,
         "fees_incurred_by": "remote",
         "threshold": 0
      }
   ]
}
```

`prism-show prism_id` Display a single prism.

Running `prism-show prism-93457a69-7270-40e9-a179-cad80e4669ee` will display a single prism object having the specified ID.

`prism-list` - List all prisms

This command returns a JSON array of all the prism objects that exist.

`prism-update prism_id members` Update an existing prism

This command has a similar sytax as `prism-create`. It takes a new `members[]` json object and updates `prism_id` to have the new members defintion.

`prism-delete prism_id` Deletes a prism

Running this command will delete a prism object from the data store. Note that any prism bindings related to `prism_id` will also be deleted.

`prism-executepayout prism_id amount_msat [label]` Executes a prism pays-out.

When run, this RPC command will execute (i.e., pay-out) a prism. This is useful if you need to manually execute a prism OUTSIDE of some binding. e.g., from [another core lightning plugin](https://github.com/farscapian/lnplay/tree/tabconf/lnplay/clightning/cln-plugins/lnplaylive).

## Bindings

By creating bindings, you can have a prism payout execute whenever a payment is received by your node. With the prism plugin, you can bind a prism to a BOLT12 offer or a BOLT11 invoice. Note that for BOLT11 invoices and single-use BOLT12 offers, bindings are REMOVED after the prism executes.

`prism-bindingadd prism_id invoice_type invoice_label`
    Binds a prism to either a bolt11 invoice or a bolt12 offer such that the prism will be executed upon incoming payment.

`prism-bindinglist` 
    Lists all prism bindings.

```
[
   {
      "bind_type": "bolt12",
      "invoice_label": "1bfc9d585f186e0479a0648bd2983eab95c7c2a0b86c2f1564295a3067e1cf09",
      "prism_id": "prism-127.0.0.1-prism_demo"
   }
]
```

`prism-bindingremove prism_id invoice_type invoice_label`
    Removes a prism binding.

## Testing and Experimenting

Check out [startup_regtest](https://github.com/ElementsProject/lightning/blob/master/contrib/startup_regtest.sh) script from the c-lightning repo or the copy in the [testing dir](https://github.com/daGoodenough/bolt12-prism/blob/main/testing/README.md) for local development.

## Future Development

- generalize the testing scripts

- create unit tests using [`pyln-testing`](https://github.com/ElementsProject/lightning/tree/master/contrib/pyln-testing)

- manage fees via the outlay prop

- Create a threshold prop to set restrictions on payouts
