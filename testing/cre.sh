#!/bin/bash

set -x

# This script will assume l2 is running the prism and l1 is paying the prism to n-2 prism members

#default number of nodes to 5
NODES=5 

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --nodes=*)
      NODES="${key#*=}"
      shift
      ;;
    *)
      echo "Unknown option: $key"
      exit 1
      ;;
  esac
done

members=()
names=("Alice" "Bob" "Carol" "Dave" "Erin" "Frank" "George" "Herman" "Inez" "Juan")

for ((i=3; i<=$NODES; i++)); do
  MEMBER_NAME="${names[$i]}"
  MEMBER_DEST=$(lightning-cli --lightning-dir=/tmp/l${i}-regtest offer any \""$RANODM"\" | jq -r '.bolt12')
  MEMBER_SPLIT=$((RANDOM % 101))
  
  # Add member to the array
  members+=("{\"name\":\"$MEMBER_NAME\", \"destination\": \"$MEMBER_DEST\", \"split\": $MEMBER_SPLIT, \"type\": \"bolt12\"}")
done
echo "${members[@]}" | jq

# Prepare the members array string
members_array=$(IFS=","; echo "${members[*]}")

# Construct the command with the members array
command="lightning-cli --lightning-dir=/tmp/l2-regtest createprism label=\"$RANDOM\" members=\"[$members_array]\""

# Call the command
eval "$command"
