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

## Starting the Plugin

There are 3 ways to start a CLN plugin...

### Add to Your Config

Find your c-lightning config file and add

`plugin=/path/to/prism.py`

### Manually start the plugin

`lightning-cli plugin start /path/to/prism.py`

### Run on startup

`lightningd --experimental-offers --plugin=/path/to/prism.py`

## Using the plugin

`prism-create` - Create a prism

Syntax: `prism-create -k members=members_json prism_id=prism-xxx`. The prism_id is optional. If left unspecified, a unique prism id starting with `prism-` will be assigned. Note that if you specify a `prism_id`, it MUST start with `prism-`.


```bash
lightning-cli prism-create -k 'members=[{"name" : "Lead-Singer", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqdxv522f7e8df9j8n5trwn6a4fmmhu3lmtzh9cesa04uq9u4n9p2x", "split": 1, "type":"bolt12"},{"name" : "Drummer", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqv7cqnv99wjrhml7f3e60ratx3gtzmc94wj4nfgn3pd997ckg2m96", "split": 1, "type":"bolt12"},{"name" : "Guitarist", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pq0fx4u9gr7s0f0xtycjgdesv4ly70s5kq26zf40z5uyak6x553wj5", "split": 1, "type":"bolt12"}]'
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

When run, this RPC command will execute (i.e., pay-out) a prism. This is useful if you need to manually execute a prism OUTSIDE of some incoming payment, e.g., from [another core lightning plugin](https://github.com/farscapian/lnplay/tree/tabconf/lnplay/clightning/cln-plugins/lnplaylive).

## Bindings

By creating bindings, you can have a prism payout execute whenever a payment is received by your node. You can bind a prism to a BOLT12 offer, or a BOLT11 invoice. Note that for BOLT11 invoices and single-use BOLT12 offers, bindings are REMOVED after the prism is paid out.

`prism-bindingadd prism_id invoice_type invoice_label`


`prism-bindinglist` 
    Lists all prism bindings.

`prism-bindingremove prism_id invoice_type invoice_label`
    Removes a prism binding.

## Testing and Experimenting

The two ways I would recommend playing around with this plugin are the [lnplay](https://github.com/farscapian/lnplay) and the [startup_regtest](https://github.com/ElementsProject/lightning/blob/master/contrib/startup_regtest.sh) script from the c-lightning repo.

### lnplay

This project is a docker stack capable of deploying a bitcoin node along with any number of CLN nodes running on any network.

With the right flags and running on regtest you can spin up a lightning network of CLN nodes running the prism plugin.

See the [docs](https://github.com/farscapian/lnplay/blob/main/README.md) for more info.

### startup_regtest

There is a copy of this script in the [testing dir](https://github.com/daGoodenough/bolt12-prism/blob/main/testing/README.md) and some docs on the other scripts.

## Future Development

- generalize the testing scripts

- create unit tests using [`pyln-testing`](https://github.com/ElementsProject/lightning/tree/master/contrib/pyln-testing)

- manage fees via the outlay prop

- Create a threshold prop to set restrictions on payouts
