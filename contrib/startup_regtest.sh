#!/bin/sh

## Short script to startup some local nodes with
## bitcoind, all running on regtest
## Makes it easier to test things out, by hand.

## Should be called by source since it sets aliases
##
##  First load this file up.
##
##  $ source contrib/startup_regtest.sh
##
##  Start up the nodeset
##
##  $ start_ln 3
##
##  Let's connect the nodes. The `connect a b` command connects node a to b.
##
##  $ connect 1 2
##  {
##    "id" : "030b02fc3d043d2d47ae25a9306d98d2abb7fc9bee824e68b8ce75d6d8f09d5eb7"
##  }
##
##  When you're finished, clean up or stop
##
##  $ stop_ln
##  $ destroy_ln # clean up the lightning directories
##

# Do the Right Thing if we're currently in top of srcdir.
if [ -z "$LIGHTNING_BIN_DIR" ] && [ -x cli/lightning-cli ] && [ -x lightningd/lightningd ]; then
	LIGHTNING_BIN_DIR=$(pwd)
fi

if [ -z "$LIGHTNING_BIN_DIR" ]; then
	# Already installed maybe?  Prints
	# shellcheck disable=SC2039
	type lightning-cli || return
	# shellcheck disable=SC2039
	type lightningd || return
	LCLI=lightning-cli
	LIGHTNINGD=lightningd
else
	LCLI="$LIGHTNING_BIN_DIR"/lightning-cli
	LIGHTNINGD="$LIGHTNING_BIN_DIR"/lightningd
	# This mirrors "type" output above.
fi

echo lightningd is "$LIGHTNINGD"
echo lightning-cli is "$LCLI"
echo ~~~~~~~

if [ -z "$PATH_TO_LIGHTNING" ]; then
    PATH_TO_LIGHTNING=/tmp
fi

if [ -z "$PATH_TO_BITCOIN" ]; then
	if [ -d "$HOME/.bitcoin" ]; then
		PATH_TO_BITCOIN="$HOME/.bitcoin"
	elif [ -d "$HOME/Library/Application Support/Bitcoin/" ]; then
		PATH_TO_BITCOIN="$HOME/Library/Application Support/Bitcoin/"
	else
		echo "\$PATH_TO_BITCOIN not set to a .bitcoin dir?" >&2
		return
	fi
fi
BCLI="$BITCOIN_BIN_DIR"/bitcoin-cli
BTCD="$BITCOIN_BIN_DIR"/bitcoind

network=regtest

echo bitcoind is "$BTCD"
echo bitcoin-cli is "$BCLI"
echo ~~~~~~~
echo lightning-dir will be in: "$PATH_TO_LIGHTNING"
echo bitcoin datadir is "$PATH_TO_BITCOIN"
echo ~~~~~~~
echo network is "$network"
echo ~~~~~~~


start_nodes() {
	if [ -z "$1" ]; then
		node_count=2
	else
		node_count=$1
	fi
	if [ "$node_count" -gt 100 ]; then
		node_count=100
	fi
	if [ -z "$2" ]; then
		network=regtest
	else
		network=$2
	fi
	# This supresses db syncs, for speed.
	if type eatmydata >/dev/null 2>&1; then
	    EATMYDATA=eatmydata
	else
	    EATMYDATA=
	fi

	LN_NODES=$node_count

	for i in $(seq "$node_count"); do
		socket=$(( 7070 + i * 101))
		mkdir -p "$PATH_TO_LIGHTNING/l$i"
		# Node config
		cat <<- EOF > "$PATH_TO_LIGHTNING/l$i/config"
network=$network
log-level=debug
log-file=$PATH_TO_LIGHTNING/l$i/$network/log
addr=localhost:$socket
allow-deprecated-apis=false
developer
dev-fast-gossip
dev-bitcoind-poll=5
experimental-dual-fund
experimental-splicing
experimental-offers
funder-policy=match
funder-policy-mod=100
funder-min-their-funding=10000sats
funder-per-channel-max=0.1btc
funder-fuzz-percent=0
funder-lease-requests-only=false
lease-fee-base-sat=2sat
lease-fee-basis=50
invoices-onchain-fallback
		EOF

        # Make sure the log file exists?
        mkdir -p "$PATH_TO_LIGHTNING"/l"$i"/"$network"
        touch "$PATH_TO_LIGHTNING"/l"$i"/"$network"/log

		# Start the lightning nodes
		test -f "$PATH_TO_LIGHTNING/l$i/lightningd-$network.pid" || \
			$EATMYDATA "$LIGHTNINGD" "--network=$network" "--lightning-dir=$PATH_TO_LIGHTNING/l$i" "--bitcoin-datadir=$PATH_TO_BITCOIN" "--database-upgrade=true" &
		# shellcheck disable=SC2139 disable=SC2086
		alias l$i-cli="$LCLI --lightning-dir=$PATH_TO_LIGHTNING/l$i"
		# shellcheck disable=SC2139 disable=SC2086
		alias l$i-log="less $PATH_TO_LIGHTNING/l$i/$network/log"
	done

	if [ -z "$EATMYDATA" ]; then
	    echo "WARNING: eatmydata not found: install it for faster testing"
	fi
	# Give a hint.
	echo "Commands: "
	for i in $(seq "$node_count"); do
		echo "	l$i-cli, l$i-log,"
	done
}

start_ln() {
	# Start bitcoind in the background
	test -f "$PATH_TO_BITCOIN/$network/bitcoind.pid" || \
		"$BTCD" -datadir="$PATH_TO_BITCOIN" -"$network" -txindex -fallbackfee=0.00000253 -daemon

	# Wait for it to start.
	while ! "$BCLI" -datadir="$PATH_TO_BITCOIN" -$network ping; do echo "awaiting bitcoind..." && sleep 1; done

	# Check if default wallet exists
	if ! "$BCLI" -datadir="$PATH_TO_BITCOIN" -$network listwalletdir | jq -r '.wallets[] | .name' | grep -wqe 'default' ; then
		# wallet dir does not exist, create one
		echo "Making \"default\" bitcoind wallet."
		"$BCLI" -datadir="$PATH_TO_BITCOIN" -$network createwallet default >/dev/null 2>&1
	fi

	# Check if default wallet is loaded
	if ! "$BCLI" -datadir="$PATH_TO_BITCOIN" -$network listwallets | jq -r '.[]' | grep -wqe 'default' ; then
		echo "Loading \"default\" bitcoind wallet."
		"$BCLI" -datadir="$PATH_TO_BITCOIN" -$network loadwallet default >/dev/null 2>&1
	fi

	# Kick it out of initialblockdownload if necessary
	if "$BCLI" -datadir="$PATH_TO_BITCOIN" -$network getblockchaininfo | grep -q 'initialblockdownload.*true'; then
		"$BCLI" -datadir="$PATH_TO_BITCOIN" -$network generatetoaddress 1 "$("$BCLI" -datadir="$PATH_TO_BITCOIN" -$network getnewaddress)" > /dev/null
	fi

	alias bt-cli='"$BCLI" -datadir="$PATH_TO_BITCOIN" -"$network"'

	if [ -z "$1" ]; then
		nodes=2
	else
		nodes="$1"
	fi
	start_nodes "$nodes" regtest
	echo "	bt-cli, stop_ln, fund_nodes"
}

ensure_bitcoind_funds() {

	if [ -z "$ADDRESS" ]; then
		ADDRESS=$("$BCLI" -datadir="$PATH_TO_BITCOIN" -"$network" "$WALLET" getnewaddress)
	fi

	balance=$("$BCLI" -datadir="$PATH_TO_BITCOIN" -"$network" "$WALLET" getbalance)
    min_bal=1

    echo Current bitcoind balance is $balance

    if awk "BEGIN {exit !("$min_bal" >= "$balance")}"; then

		printf "%s" "Mining into address " "$ADDRESS""... "

		"$BCLI" -datadir="$PATH_TO_BITCOIN" -"$network" generatetoaddress 100 "$ADDRESS" > /dev/null

		echo "done."

	    echo "New bitcoind balance:" "$("$BCLI" -datadir="$PATH_TO_BITCOIN" -"$network" "$WALLET" getbalance)"
	fi
}

fund_nodes() {
	WALLET="default"
	NODES=""

	for var in "$@"; do
		case $var in
			-w=*|--wallet=*)
				WALLET="${var#*=}"
				;;
			*)
				NODES="${NODES:+${NODES} }${var}"
				;;
		esac
	done

	if [ -z "$NODES" ]; then
		NODES=$(seq "$node_count")
	fi

	WALLET="-rpcwallet=$WALLET"

	ensure_bitcoind_funds

	last_node=""

	echo "$NODES" | while read -r i; do

		if [ -z "$last_node" ]; then
			last_node=$i
			continue
		fi

		node1=$last_node
		node2=$i
		last_node=$i

		L2_NODE_ID=$($LCLI -F --lightning-dir=$PATH_TO_LIGHTNING/l"$node2" getinfo | sed -n 's/^id=\(.*\)/\1/p')
		L2_NODE_PORT=$($LCLI -F --lightning-dir=$PATH_TO_LIGHTNING/l"$node2" getinfo | sed -n 's/^binding\[0\].port=\(.*\)/\1/p')

		$LCLI -H --lightning-dir=$PATH_TO_LIGHTNING/l"$node1" connect "$L2_NODE_ID"@localhost:"$L2_NODE_PORT" > /dev/null

        # Fund both nodes, let's do a dual funded channel :)
		L1_WALLET_ADDR=$($LCLI -F --lightning-dir=$PATH_TO_LIGHTNING/l"$node1" newaddr | sed -n 's/^bech32=\(.*\)/\1/p')
		L2_WALLET_ADDR=$($LCLI -F --lightning-dir=$PATH_TO_LIGHTNING/l"$node2" newaddr | sed -n 's/^bech32=\(.*\)/\1/p')

		ensure_bitcoind_funds

		"$BCLI" -datadir="$PATH_TO_BITCOIN" -"$network" "$WALLET" sendtoaddress "$L1_WALLET_ADDR" 1 > /dev/null
		"$BCLI" -datadir="$PATH_TO_BITCOIN" -"$network" "$WALLET" sendtoaddress "$L2_WALLET_ADDR" 1 > /dev/null

		"$BCLI" -datadir="$PATH_TO_BITCOIN" -"$network" -generate 1 > /dev/null

		printf "%s" "Waiting for lightning node funds... "

		while ! $LCLI -F --lightning-dir=$PATH_TO_LIGHTNING/l"$node1" listfunds | grep -q "outputs"
		do
			sleep 1
		done

		while ! $LCLI -F --lightning-dir=$PATH_TO_LIGHTNING/l"$node2" listfunds | grep -q "outputs"
		do
			sleep 1
		done

		echo "found."

		printf "%s" "Funding channel from node " "$node1" " to node " "$node2"". "

		$LCLI --lightning-dir=$PATH_TO_LIGHTNING/l"$node1" fundchannel "$L2_NODE_ID" 1000000 > /dev/null

		"$BCLI" -datadir="$PATH_TO_BITCOIN" -"$network" -generate 6  > /dev/null

		printf "%s" "Waiting for confirmation... "

		while ! $LCLI -F --lightning-dir=$PATH_TO_LIGHTNING/l"$node1" listchannels | grep -q "channels"
		do
			sleep 1
		done

		echo "done."

	done
}

stop_nodes() {
	network=${1:-$network}
	if [ -n "$LN_NODES" ]; then
		for i in $(seq "$LN_NODES"); do
			test ! -f "$PATH_TO_LIGHTNING/l$i/lightningd-$network.pid" || \
				(kill "$(cat "$PATH_TO_LIGHTNING/l$i/lightningd-$network.pid")"; \
				rm "$PATH_TO_LIGHTNING/l$i/lightningd-$network.pid")
			unalias "l$i-cli"
			unalias "l$i-log"
		done
	fi
}

stop_ln() {
	stop_nodes "$@"
	test ! -f "$PATH_TO_BITCOIN/regtest/bitcoind.pid" || \
		(kill "$(cat "$PATH_TO_BITCOIN/regtest/bitcoind.pid")"; \
		rm "$PATH_TO_BITCOIN/regtest/bitcoind.pid")

	unset LN_NODES
	unalias bt-cli
}

destroy_ln() {
	network=${1:-$network}
	rm -rf "$PATH_TO_LIGHTNING"/l[0-9]*
}

start_elem() {
	if [ -z "$PATH_TO_ELEMENTS" ]; then
		if [ -d "$HOME/.elements" ]; then
			PATH_TO_ELEMENTS="$HOME/.elements"
		else
			echo "\$PATH_TO_ELEMENTS not set to a .elements dir" >&2
			return
		fi
	fi

	test -f "$PATH_TO_ELEMENTS/liquid-$network/bitcoin.pid" || \
		elementsd -chain=liquid-$network -printtoconsole -logtimestamps -nolisten -validatepegin=0 -con_blocksubsidy=5000000000 -daemon

	# Wait for it to start.
	while ! elements-cli -chain=liquid-$network ping 2> /tmp/null; do echo "awaiting elementsd..." && sleep 1; done

	# Kick it out of initialblockdownload if necessary
	if elements-cli -chain=liquid-$network getblockchaininfo | grep -q 'initialblockdownload.*true'; then
		elements-cli -chain=liquid-$network generatetoaddress 1 "$(elements-cli -chain=liquid-$network getnewaddress)" > /dev/null
	fi
	alias et-cli='elements-cli -chain=liquid-$network'

	if [ -z "$1" ]; then
		nodes=2
	else
		nodes="$1"
	fi
	start_nodes "$nodes" liquid-$network
	echo "	et-cli, stop_elem"
}


stop_elem() {
	stop_nodes "$1" liquid-$network
	test ! -f "$PATH_TO_ELEMENTS/liquid-$network/bitcoind.pid" || \
		(kill "$(cat "$PATH_TO_ELEMENTS/liquid-$network/bitcoind.pid")"; \
		rm "$PATH_TO_ELEMENTS/liquid-$network/bitcoind.pid")

	unset LN_NODES
	unalias et-cli
}

connect() {
	if [ -z "$1" ] || [ -z "$2" ]; then
		printf "usage: connect 1 2\n"
	else
		to=$($LCLI --lightning-dir="$PATH_TO_LIGHTNING/l$2" -F getinfo | grep '^\(id\|binding\[0\]\.\(address\|port\)\)' | cut -d= -f2- | tr '\n' ' ' | (read -r ID ADDR PORT; echo "$ID@${ADDR}:$PORT"))
		$LCLI --lightning-dir="$PATH_TO_LIGHTNING/l$1" connect "$to"
	fi
}

echo Useful commands:
echo "  start_ln 3: start three nodes, l1, l2, l3"
echo "  connect 1 2: connect l1 and l2"
echo "  fund_nodes: connect all nodes with channels, in a row"
echo "  stop_ln: shutdown"
echo "  destroy_ln: remove ln directories"