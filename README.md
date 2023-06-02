# ROYGBIV
This project started at the 2023 btc++ conference in Austin, TX. The plugin will now live in this repo, but you can see where it started [here](https://github.com/farscapian/prism-hackathon) and [where it went](https://github.com/farscapian/clams-app-docker/blob/76ce6d3eb278fe6c10369b8fba8e28d68041af19/roygbiv/clightning/cln-plugins/prism-plugin.py) from there. . . now we're here and here we will stay.

![Lightning Prisms](https://camo.githubusercontent.com/1952f4c33ec82c8dbe748f0b0fa5925659d66add0bd93591d24245322d100581/68747470733a2f2f692e696d6775722e636f6d2f686555636b71342e6a7067)

`createprism` and `listprisms` are RPC methods  to create and fetch bolt12 offers representing a lightning prism.

## Usage:

ROYGBIV adds two RPC methods. _createprism_ and _listprisms_.

### Creating a prism:

- **method**: _createprism_
- **params**: _label_ as a string and _members_ as an array

```
lightning-cli createprism label="string" members='[{"name": "node_pubkey", "destination": "node_pubkey", "split": 1 <= num <= 1000}]'
```

Returns the bolt12 offer:

```
{
   "offer_id": "eb9479c5f517d0194b49cb3370d87211b9548134ee2d3df244f3fd16d3922a82",
   "active": true,
   "single_use": false,
   "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qunnzwfcxq6jw93pq05mpwn9adpag8pw6jzefwyh38zte0p73zf9lfkc8mvwq6gm9ekvz",
   "used": false,
   "created": true
}

```

| Check out the [create_prism](https://github.com/farscapian/clams-app-docker/blob/main/channel_templates/create_prism.sh) script it you're running the [Clams stack](https://github.com/farscapian/clams-app-docker) with ROYGBIV

#### Key things to note:

- splits get normalized to relative sat amounts

For example:

```
lightning-cli createprism label="string" members='[{"name": "alice", "destination": "alice_pubkey", "split": 1}, {"name": "bob", "destination": "bob_pubkey", "split": 1}, {"name": "carol", "destination": "carol_pubkey", "split": 1}]'
```

The above equally distributes each payment to Alice, Bob, and Carol. . . they each get 33%.

Likewise, if Carol's split was changed to 2, then Alice --> 25%, Bob --> 25%, Carol --> 50%

- split only accepts integers 1 - 1000
- Currently **only supports recipients of prism payments with keysend enabled**

### Listing prisms

- **method**: _listprisms_

```
lightning-cli listprisms
```

Returns an array of prism metadata:

```
[
   {
      "label": "'15875'",
      "bolt12": "lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qunnzdfcxu6jw93pqwmglk2a6d6lxdpqcj4ewlmrtpuseguafyh2l48y6fnav5rqgewvj"
      "members": [
         {
            "name": "carol",
            "destination": "0251b497f566aa3308a3b70f5619d2585afe7166c26137ff769f1dc7547e1cfe0d",
            "split": 1
         },
      ]
   }
]

```

## Using with the [Clams Stack](https://github.com/farscapian/clams-app-docker)

1. Make sure you've gone through the setup and have these environment variables set:

```
CLN_COUNT=5
BTC_CHAIN=regtest
```

2. Interact with your CLN nodes by running the `lightning-cli.sh` script. To target a specific node, pass the script and id. Here's an example of how you can list the prisms on the second node (bob).

_NOTE: make sure you are in the root dir of clams-app-docker_

```
./lightning-cli.sh --id=1 listprisms
```

You could of course replace `id` with 0 <= id < CLN_COUNT

3. If you tried that and there was no prisms, try to run `create_prism.sh` (in the channel_templates dir). This will create one prism that lives on bob's node and stores carol, dave, and erin as prism members. Feel free to mess around with the splits they each recieve as defined in the script.

## Paying to a prism from the CLI

_Assuming you are still using the clams-app-docker stack_

1. Retrieve the bolt12 offer for a prism: `./lightning-cli.sh --id=1 listprisms`
2. Use Alice's node to fetch the invoice from Bob. Like so:

```
./lightning-cli.sh --id=0 fetchinvoice <bolt12> <amount_msats>
```

3. Now, Alice can pay Bob's offer:

```
./lightning-cli.sh --id=0 pay <invoice_copied_from_fetchinvoice>
```

4. Check out Carol, Dave, or Erin's balance by doing something like `./lightning-cli.sh --id=3 listfunds` and examine the `channel-sat` value for the channel they have open with Bob

# Conclusion

Creating a prism results in a payable bolt12 offer that will split the payment to n number of prism members. Each member gets a relative split. The `createprism` method allows you to create prisms and the `listprisms` method will fetch all prisms stored on that node. We then went through how you could use the [Clams Stack](https://github.com/farscapian/clams-app-docker) with prisms to easily spin up a test environment and interact with nodes and prims using the handy lightning-cli.sh script.

## Future Dev Plans
- full bolt12 support in and out of the prism
- `delprism`
- `updateprism`
