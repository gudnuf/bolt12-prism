#!/bin/bash

set -e


CAROL_OFFER=$(lightning-cli --lightning-dir=/tmp/l3-regtest offer any "\"$RANDOM"\" | jq -r '.bolt12')
DAVE_OFFER=$(lightning-cli --lightning-dir=/tmp/l4-regtest offer any "\"$RANDOM"\" | jq -r '.bolt12')
ERIN_OFFER=$(lightning-cli --lightning-dir=/tmp/l5-regtest offer any "\"$RANDOM"\" | jq -r '.bolt12')

lightning-cli --lightning-dir=/tmp/l2-regtest updateprism offer_id="0d20fe61865e988b5ea7abc40cddcc737f6b5b210e28153a2211ee50807820c8" members="[{\"name\" : \"carol\", \"destination\": \"$CAROL_OFFER\", \"split\": 5}, {\"name\": \"bob\", \"destination\": \"$DAVE_OFFER\", \"split\": 10}, {\"name\": \"erin\", \"destination\": \"$ERIN_OFFER\", \"split\": 10}]"

