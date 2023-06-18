# Testing and Experimenting

Make sure you have cln and bitcoin core installed.

## Starting your network

`source ./startup_regtest.sh`

That will give you access to a series of handy scripts.

**NOTE**: Most of these scripts are hardcoded to work with prisms in a 5 node network

`start_ln 5` will create 5 lightning nodes.

## Prism network configuration

Make sure your bitcoind node is funded, and then run `./bootstrap_network.sh`

That will fund all the nodes, connect them, and then open channels in the configuration necessary for creating prisms with 3 members payable by l1.

## Start/restart plugin

`./prism_restart.sh`

## Create prisms

`./create_prism.sh`

This just creates a prism where l1 can pay l2's prism which pays out to l3, l4, and l5.

## Paying a prism

Prisms are stored as BOLT 12 offers in the uncle Jim node.

This means "paying a prism" is equivalent to paying a BOLT 12 offer.

1. l1 has to fetch an invoice from l2. See `fetchinvoice` in the CLN docs
2. l1 pays that invoice. See `pay` in the CLN docs

When a payment is received, the node looks up in the datastore to see if a prism exists for that offer. Then it iterates through each member paying out their deserved amount.

## Help

Reach out if you have any questions. This project has been a learning experience for me. Feedback is appreciated.
