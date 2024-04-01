#! /bin/bash

set -e

if [[ $# -lt 1 ]]; then
  echo "Please provide 'node_num', 'offer', and 'amount' arguments."
  exit 1
fi

NODE_NUM=$1
OFFER=$2
AMOUNT=$3

LN_DIR="/tmp/l$NODE_NUM-regtest"

if [ ! -d "$LN_DIR" ]; then
  echo "Error: Lightning directory not found. Make sure your node is started"
  exit 1
fi

LN_CLI="lightning-cli --lightning-dir=$LN_DIR"

invoice=$($LN_CLI fetchinvoice "$OFFER" "$AMOUNT" | jq -r .invoice)

$LN_CLI pay "$invoice"

