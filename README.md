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

### Create a prism

Syntax: `prism-create -k members=members_json prism_id=prism-xxx`. The `prism_id` is optional. If left unspecified, a unique prism id starting with `prism-` will be assigned. Note that if you specify a `prism_id`, it MUST start with `prism-`. [Here's an example script](https://github.com/farscapian/lnplay/blob/incus/channel_templates/create_bolt12_prism.sh).

```bash
lightning-cli prism-create -k 'members=[{"label" : "Lead-Singer", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqtyh3ua3crhn6me89spfupgp40nxkdfkhp0j2zjk63qgsdxp230ss", "split": 1, "type":"bolt12"},{"label" : "Drummer", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqw2ugunkxkzckdwkme9wkzfmjf4f2hm3852906gwsk05lxm0s29fu", "split": 1, "type":"bolt12"},{"label" : "Guitarist", "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qajx2enpw4k8g93pqvqlu8pa98q4wqrvdvyg0svtunw8pa5vj0j9r5mnpzcrjyx8tm7jw", "split": 1, "type":"bolt12"}]'
```


### List Prism IDs

Let's say you have three prisms defined, one of which you specified and ID for. `prism-list` might look something like this:

```json
{
   "prisms": [
      "1ae57a94-1a57-4d9c-aabe-5da1dd340edd",
      "88a743d1-da8c-4cbe-afdc-9db58e154dc5",
      "prism-demo1"
   ]
}
```

## `prism-show prism_id` show a Prism Definition

Ok cool, you have some prism_ids. Now use `prism-show` to view the prism definition.

`prism-show prism-demo1`

```json
{
   "prism_id": "prism-demo1",
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
<!-- 
### Update an existing prism

This command has a similar sytax as `prism-create`. It takes a new `members[]` json object and updates `prism_id` to have the new members defintion.

### Deletes a prism

Running `prism-delete prism_id` will delete a prism object from the data store. Note that any prism bindings related to `prism_id` will also be deleted.

### Executes a prism pay-out

`prism-executepayout prism_id amount_msat [label]` 

When run, this RPC command will execute (i.e., pay-out) a prism. This is useful if you need to manually execute a prism OUTSIDE of some binding. e.g., from [another core lightning plugin](https://github.com/farscapian/lnplay/tree/tabconf/lnplay/clightning/cln-plugins/lnplaylive). You can specify the `label` paramemter to associate this payout to some external `id`.

## Bindings

By creating bindings, you can have a prism payout execute whenever a payment is received by your node. With the prism plugin, you can bind a prism to a BOLT12 offer or a BOLT11 invoice. Note that for BOLT11 invoices and single-use BOLT12 offers, bindings are REMOVED after the prism executes.

`prism-bindingadd prism_id invoice_type invoice_label`
    Binds a prism to either a bolt11 invoice or a bolt12 offer such that the prism will be executed upon incoming payment.

`prism-bindinglist` 
    Lists all prism bindings.

```

```

`prism-bindingremove prism_id invoice_type invoice_label`
    Removes a prism binding. -->

## Contribing

There is a copy of the [startup_regtest](https://github.com/ElementsProject/lightning/blob/master/contrib/startup_regtest.sh) script from the c-lightning repo [contrib dir](./contrib/) for local development.

## Future Development

- generalize the testing scripts

- create unit tests using [`pyln-testing`](https://github.com/ElementsProject/lightning/tree/master/contrib/pyln-testing)

- manage fees via the outlay prop

- Create a threshold prop to set restrictions on payouts


# TODO

* Remove the "type" field from the members JSON and INFER (from regex) whether the destination is a keysend or BOLT12.