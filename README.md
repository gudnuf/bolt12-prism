# ROYGBIV

A CLN plugin for creating and interacting with BOLT 12 native prisms.

_BOLT 12 is currently experimental and you will need to enable `experimental-offers`_

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

You can either manually start the plugin or add it your startup command.

### Manually start the plugin

lightning-cli plugin start /path/to/prism-plugin.py

### Run on startup

lightningd plugin=/path/to/prism-plugin.py

## Using the plugin

CLN exposes plugins as RPC methods

There are currently three methods available for interacting with prisms: `createprism`, `listprisms`, and `deleteprism`\*

### createprism

**createprism label members**

_label_ is a string to lable prisms and the corresponding offer

_members_ is an array of member objects with the following form:

```
{
  name: string,
  destination: string,
  split: int,
  type: ?string
}

```

_name_: member's name

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

_see /testing/create_prism.sh_

### listprisms

_listprisms_

Returns array of prism metadata:

```
{
   "prisms": [
      {
         "label": "band-prism",
         "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2pf3xzmny94c8y6tnd5tzzql8sxrnaaq8secwrcsw5wmdxtfqgj9kamaslpvgxk08g0tdmqzmav",
         "offer_id": "facedc24ee4587f42b75cec81863a63727acea9961d2bdd170d70b90bd28f7b7",
         "members": [
            {
               "name": "lead-singer",
               "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2q5mngwpnxstzzql8sxrnaaq8secwrcsw5wmdxtfqgj9kamaslpvgxk08g0tdmqzmav",
               "split": 5
            },
            {
               "name": "drummer",
               "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2q5mngwpnxstzzql8sxrnaaq8secwrcsw5wmdxtfqgj9kamaslpvgxk08g0tdmqzmav",
               "split": 2
            },
            {
               "name": "guitarist",
               "destination": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2q5mngwpnxstzzql8sxrnaaq8secwrcsw5wmdxtfqgj9kamaslpvgxk08g0tdmqzmav",
               "split": 3
            }
         ]
      }
   ]
}
```

### deleteprism

**deleteprism offer_id**

When prisms are created, they get stored in the node's datastore with the offer id as the key.

_see `datastore`, `listdatastore`, and `deldatastore` from the CLN docs._

## Testing and Experimenting

The two ways I would recommend playing around with this plugin are the [roygbiv-stack](https://github.com/) and the `startup_regtest` script from the lightning repo.

### roygbiv-stack

This project is a docker stack capable of deployging a bitcoin node along with any number of CLN nodes running on any network.

With the right flags and running on regtest you can spin up a lightning network of CLN nodes running the prism plugin.

See the docs for more info.

### startup_regtest

There is a copy of this script in the testing dir along with some docs on the other scripts in there.

## Future Development

- `updateprism` will be an available method for updating prism metadata while maintaining the same offer.

- generalize the testing scripts

- create a series of tests to make sure the prism isn't broken.
