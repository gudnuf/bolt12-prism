#!/bin/bash
set -x

# Sample variables and array
NODES=5
names=("Alice" "Bob" "Carol" "Dave" "Erin" "Frank" "George" "Herman" "Inez" "Juan")
members=()

# Generate member objects and add them to the array
for ((i=3; i<=$NODES; i++)); do
  MEMBER_NAME="${names[$i]}"
  MEMBER_DEST=$(lightning-cli --lightning-dir=/tmp/l${i}-regtest offer any \""$RANODM"\" | jq -r '.bolt12')
  MEMBER_SPLIT=$((RANDOM % 101))

  # Add member to the array
  members+=("{\"name\":\"$MEMBER_NAME\", \"destination\": \"$MEMBER_DEST\", \"split\": $MEMBER_SPLIT, \"type\": \"bolt12\"}")
done

# Prepare the members array string
members_array=$(printf '%s\n' "${members[@]}" | jq -sRc 'split("\n")[:-1] | join(",")')
members_array="[$members_array]"

# Construct the command with the members array
command="lightning-cli --lightning-dir=/tmp/l2-regtest createprism label=\"$RANDOM\" members=\"$members_array\""

# Call the generated command
eval "$command"


# # This script will assume l2 is running the prism and l1 is paying the prism to n-2 prism members

# #default number of nodes to 5
# NODES=5 

# while [[ $# -gt 0 ]]; do
#   key="$1"
#   case $key in
#     --nodes=*)
#       NODES="${key#*=}"
#       shift
#       ;;
#     *)
#       echo "Unknown option: $key"
#       exit 1
#       ;;
#   esac
# done

# members=()
# names=("Alice" "Bob" "Carol" "Dave" "Erin" "Frank" "George" "Herman" "Inez" "Juan")

# for ((i=3; i<=$NODES; i++)); do
#   MEMBER_NAME="${names[$i]}"
#   MEMBER_DEST=$(lightning-cli --lightning-dir=/tmp/l${i}-regtest offer any \""$RANODM"\" | jq -r '.bolt12')
#   MEMBER_SPLIT=$((RANDOM % 101))
  
#   # Add member to the array
#   members+=("{\"name\":\"$MEMBER_NAME\", \"destination\": \"$MEMBER_DEST\", \"split\": $MEMBER_SPLIT, \"type\": \"bolt12\"}")
# done
# echo "${members[@]}" | jq

# # Prepare the members array string
# members_array=$(printf '%s\n' "${members[@]}" | jq -sRc 'split("\n")[:-1] | join(",")')
# members_array="[$members_array]"

# # Construct the command with the members array
# command="lightning-cli --lightning-dir=/tmp/l2-regtest createprism label=\"$RANDOM\" members=\"$members_array\""

# # Call the command
# eval "$command"

# set -x

# # This script will assume l2 is running the prism and l1 is paying the prism to n-2 prism members

# #default number of nodes to 5
# NODES=5 

# while [[ $# -gt 0 ]]; do
#   key="$1"
#   case $key in
#     --nodes=*)
#       NODES="${key#*=}"
#       shift
#       ;;
#     *)
#       echo "Unknown option: $key"
#       exit 1
#       ;;
#   esac
# done

# members=()
# names=("Alice" "Bob" "Carol" "Dave" "Erin" "Frank" "George" "Herman" "Inez" "Juan")

# for ((i=3; i<=$NODES; i++)); do
#   MEMBER_NAME="${names[$i]}"
#   MEMBER_DEST=$(lightning-cli --lightning-dir=/tmp/l${i}-regtest offer any \""$RANODM"\" | jq -r '.bolt12')
#   MEMBER_SPLIT=$((RANDOM % 101))
  
#   # Add member to the array
#   members+=("{\"name\":\"$MEMBER_NAME\", \"destination\": \"$MEMBER_DEST\", \"split\": $MEMBER_SPLIT, \"type\": \"bolt12\"}")
# done
# echo "${members[@]}" | jq

# # PUB3=$(lightning-cli --lightning-dir=/tmp/l3-regtest getinfo | jq '.id')
# # # PUB3="lno1qgsqvgnwgcg35z6ee2h3yczraddm72xrfua9uve2rlrm9deu7xyfzrc2qek8xctydfnpvggr9dgv99jng3rqlh8jhw2wmsgx23l87j0l88g2q0dxnsgeac3r0k5q"
# # PUB4=$(lightning-cli --lightning-dir=/tmp/l4-regtest getinfo | jq '.id')
# # OFFER5=$(lightning-cli --lightning-dir=/tmp/l5-regtest offer any \"$RANDOM\" | jq '.bolt12')


# # lightning-cli --lightning-dir=/tmp/l2-regtest createprism label=\"$RANDOM\" members="[{\"name\":\"carol\", \"destination\": $PUB3, \"split\": 1, \"type\": \"keysend\"}, {\"name\": \"dave\", \"destination\": $PUB4, \"split\": 5, \"type\": \"keysend\"}, {\"name\": \"Erin\", \"destination\": $OFFER5, \"split\": 5}]"


# # members_array=$(echo "${members[@]}" | jq -c)

# # lightning-cli --lightning-dir=/tmp/l2-regtest createprism label=\"$RANDOM\" members=["$members_array"]

# members_array=$(printf '%s\n' "${members[@]}" | jq -c | sed 's/"/\\"/g')

# lightning-cli --lightning-dir=/tmp/l2-regtest createprism label=\"$RANDOM\" members=\"[$members_array]\"

# # Call the generated command
# eval "$COMMAND"
