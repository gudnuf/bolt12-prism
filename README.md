# BOLT 12 Prism Plugin

A CLN plugin for creating and interacting with BOLT 12 prisms.

![roygbiv](https://github.com/daGoodenough/bolt12-prism/assets/108303703/2c4ba75d-b0ab-4c3f-a5c4-2202716a04a0)

_BOLT 12 is currently experimental and you will need to add the **--experimental-offers** flag when starting lightningd_

## Background

This started as the winning hackathon project at btc++ 2023 in Austin, Tx.

Some other projects that compliment this one are

- [roygbiv.money](https://roygbiv.money) where you can experiment with prisms in regtest
- [roygbiv.guide](https://roygbiv.guide) to learn more about prisms
- [roygbiv-stack](https://github.com/farscapian/roygbiv-stack) to deploy CLN nodes running prisms on any network
- [roygbiv-frontend](https://github.com/johngribbin/ROYGBIV-frontend)

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

There are currently four methods available for interacting with prisms: `createprism`, `listprisms`, `updateprism` and `deleteprism`

### createprism

**createprism** _label members[]_

_label_ is a string to label prisms and the corresponding offer

_members_ is an array of member objects with the following form:

```
{
  name: string,
  destination: string,
  split: int,
  type?: string
}
```

_name_: identifier for the member

_destination_: bolt12 or node pubkey. bolt12 is default.

_split_: relative payment split for that member. All splits get normalized to a percentage.

_type_: "bolt12" or "keysend". Defaults to "bolt12"

#### 3 member prism example

```
lightning-cli createprism label="band-prism" members="[{\"name\": \"lead-singer\", \"destination\": \"lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2q5mngwpnxstzzql8sxrnaaq8secwrcsw5wmdxtfqgj9kamaslpvgxk08g0tdmqzmav\", \"split\":5}, {\"name\": \"drummer\", \"destination\": \"lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2q5mngwpnxstzzql8sxrnaaq8secwrcsw5wmdxtfqgj9kamaslpvgxk08g0tdmqzmav\", \"split\":2}, {\"name\": \"guitarist\", \"destination\": \"lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2q5mngwpnxstzzql8sxrnaaq8secwrcsw5wmdxtfqgj9kamaslpvgxk08g0tdmqzmav\", \"split\":3}]"

```

Returns the BOLT 12 offer:

```
{
   "offer_id": "facedc24ee4587f42b75cec81863a63727acea9961d2bdd170d70b90bd28f7b7",
   "active": true,
   "single_use": false,
   "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2pf3xzmny94c8y6tnd5tzzql8sxrnaaq8secwrcsw5wmdxtfqgj9kamaslpvgxk08g0tdmqzmav",
   "used": false,
   "created": true
}
```

_see testing/create_prism.sh_

### listprisms

**listprisms**

Returns array of prism metadata:

```
{
   "prisms": [
      {
         "label": "band-prism",
         "version": "v0.0.1",
         "members": [
            {
               "name": "lead-singer",
               "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2q5mngwpnxstzzql8sxrnaaq8secwrcsw5wmdxtfqgj9kamaslpvgxk08g0tdmqzmav",
               "split": 5,
               "outlay_msat": 0,
               "id": 1
            },
            {
               "name": "drummer",
               "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2q5mngwpnxstzzql8sxrnaaq8secwrcsw5wmdxtfqgj9kamaslpvgxk08g0tdmqzmav",
               "split": 2,
               "outlay_msat": 3000,
               "id": 2
            },
            {
               "name": "guitarist",
               "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2q5mngwpnxstzzql8sxrnaaq8secwrcsw5wmdxtfqgj9kamaslpvgxk08g0tdmqzmav",
               "split": 3,
               "outlay_msat": 2300,
               "id": 3
            }
         ],
         "offer": {
            "offer_id": "facedc24ee4587f42b75cec81863a63727acea9961d2bdd170d70b90bd28f7b7",
            "active": true,
            "single_use": false,
            "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2pf3xzmny94c8y6tnd5tzzql8sxrnaaq8secwrcsw5wmdxtfqgj9kamaslpvgxk08g0tdmqzmav",
            "used": false
         }
      }
   ]
}
```

### deleteprism

**deleteprism** _offer_id_

When prisms are created, they get stored in the node's datastore with the offer id as the key.

_see `datastore`, `listdatastore`, and `deldatastore` from the [CLN docs](https://lightning.readthedocs.io/)._

### updateprism

**updateprism** *offer_id members[]*

Replaces the array of members in a preexisting prism with the members array that gets passed.

## Testing and Experimenting

The two ways I would recommend playing around with this plugin are the [roygbiv-stack](https://github.com/) and the [startup_regtest](https://github.com/ElementsProject/lightning/blob/master/contrib/startup_regtest.sh) script from the c-lightning repo.

### roygbiv-stack

This project is a docker stack capable of deploying a bitcoin node along with any number of CLN nodes running on any network.

With the right flags and running on regtest you can spin up a lightning network of CLN nodes running the prism plugin.

See the [docs](https://github.com/farscapian/roygbiv-stack/blob/main/README.md) for more info.

### startup_regtest

There is a copy of this script in the [testing dir](https://github.com/daGoodenough/bolt12-prism/blob/main/testing/README.md) and some docs on the other scripts.

## Future Development

- generalize the testing scripts

- create unit tests using [`pyln-testing`](https://github.com/ElementsProject/lightning/tree/master/contrib/pyln-testing)

- manage fees via the outlay prop

- Create a threshold prop to set restrictions on payouts
