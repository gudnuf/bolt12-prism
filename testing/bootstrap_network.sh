#! /bin/bash

set -ex

source /home/daim/code/bolt12-prism/testing/startup_regtest.sh > /dev/null

bc_funds=$(bitcoin-cli -regtest getwalletinfo | jq '.balance' -r | awk '{printf "%.0f\n", $0}')

if (( bc_funds < 50 )); then
  BIT_ADDR=$(bitcoin-cli -regtest getnewaddress)

  echo "Generating 101 blocks to $BIT_ADDR..."
  bitcoin-cli -regtest generatetoaddress 101 "$BIT_ADDR" > /dev/null
fi


echo "**************************************"

ADDR1=$(lightning-cli --lightning-dir=/tmp/l1-regtest newaddr | jq -r '.bech32')
ADDR2=$(lightning-cli --lightning-dir=/tmp/l2-regtest newaddr | jq -r '.bech32')
# ADDR1=$(lightning-cli --lightning-dir=/tmp/l1-regtest newaddrID1=$(lightning-cl) | jq -r '.bech32')
# ADDR1=$(lightning-cli --lightning-dir=/tmp/l1-regtest newaddrID1=$(lightning-cl) | jq -r '.bech32')
# ADDR1=$(lightning-cli --lightning-dir=/tmp/l1-regtest newaddrID1=$(lightning-cl) | jq -r '.bech32')

echo "Funding lightning nodes..."

bitcoin-cli -regtest sendtoaddress "$ADDR1" 1 > /dev/null
bitcoin-cli -regtest -generate 1 > /dev/null

bitcoin-cli -regtest sendtoaddress "$ADDR2" 1 > /dev/null
bitcoin-cli -regtest -generate 1 > /dev/null

bitcoin-cli -regtest sendtoaddress "$ADDR2" 1 > /dev/null
bitcoin-cli -regtest -generate 1 > /dev/null

bitcoin-cli -regtest sendtoaddress "$ADDR2" 1 > /dev/null
bitcoin-cli -regtest -generate 1 > /dev/null

sleep 10

echo "***************************************"

echo "Connecting 1 --> 2"
connect 1 2 > /dev/null

echo "Connecting 2 --> 3"
connect 2 3 > /dev/null

echo "Connecting 2 --> 4"
connect 2 4 > /dev/null

echo "Connecting 2--> 5"
connect 2 5 > /dev/null

sleep 10

ID2=$(lightning-cli  --lightning-dir=/tmp/l2-regtest getinfo | jq -r '.id')
ID3=$(lightning-cli  --lightning-dir=/tmp/l3-regtest getinfo | jq -r '.id')
ID4=$(lightning-cli  --lightning-dir=/tmp/l4-regtest getinfo | jq -r '.id')
ID5=$(lightning-cli  --lightning-dir=/tmp/l5-regtest getinfo | jq -r '.id')

echo "**************************************"

FUNDING_AMOUNT=1000000

echo "Funding 1 --> 2 with $FUNDING_AMOUNT sats"
lightning-cli --lightning-dir=/tmp/l1-regtest fundchannel "$ID2" "$FUNDING_AMOUNT" > /dev/null
sleep 3

echo "Funding 2 --> 3 with $FUNDING_AMOUNT sats"
lightning-cli --lightning-dir=/tmp/l2-regtest fundchannel "$ID3" "$FUNDING_AMOUNT" > /dev/null
sleep 3

echo "Funding 2 --> 4 with $FUNDING_AMOUNT sats"
lightning-cli --lightning-dir=/tmp/l2-regtest fundchannel "$ID4" "$FUNDING_AMOUNT" > /dev/null
sleep 3

echo "Funding 2 --> 5 with $FUNDING_AMOUNT sats"
lightning-cli --lightning-dir=/tmp/l2-regtest fundchannel "$ID5" "$FUNDING_AMOUNT" > /dev/null
sleep 3

bitcoin-cli -regtest -generate 10 > /dev/null

echo "***********************************"

echo "Channel configuration initialized"
echo "          ALICE"
echo "            |  "
echo "            |  "
echo "            v  "
echo "           BOB  "
echo "          / | \\"
echo "         /  |  \\"
echo "        /   |   \\"
echo "       V    V     V"
echo "   CAROL   DAVE   ERIN"