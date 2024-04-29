
    #time.sleep(500)
    #except Exception as e:
    #    return e


# def test_bolt12_prism_dynamic_start(node_factory):
#     # assert 0 == 1
#     # l2 = node_factory.get_node(opts=plugin_opt)
#     l2 = node_factory.get_node()
#     l2.rpc.plugin_start(plugin_path)
#     l2.stop()

# def test_prism_list(node_factory):
#     l2 = node_factory.get_node()

#     l2.rpc.plugin_start(plugin_path)
#     l2.daemon.wait_for_log("Plugin bolt12_prism.py initialized.*")
#     l2.rpc.plugin_stop(plugin_path)
#     l2.rpc.plugin_start(plugin_path)
#     l2.daemon.wait_for_log("Plugin bolt12_prism.py initialized.*")
#     l2.stop()
#     # # Then statically
#     # l2.daemon.opts["plugin"] = plugin_path
#     # l2.start()
#     # # Start at 0 and 're-await' the two inits above. Otherwise this is flaky.
#     # l2.daemon.logsearch_start = 0
#     # l2.daemon.wait_for_logs(["Plugin rebalance initialized.*",
#     #                          "Plugin rebalance initialized.*",
#     #                          "Plugin rebalance initialized.*"])


###############################3
#################################

# import os
# from pyln.testing.fixtures import *  # noqa: F401,F403
# from pyln.client import Millisatoshi

# plugin_path = os.path.join(os.path.dirname(__file__), "bolt12-prism.py")
# plugin_opt = {'plugin': plugin_path}


# def test_my_plugin(node_factory):
#     # Create a node with your plugin enabled
#     opts = {'plugin': '/path/to/your/plugin.py'}
#     l2 = node_factory.get_node(options=opts)
    
#     # Start writing tests, e.g., checking if the plugin loaded correctly
#     assert 'myplugin' in l2.rpc.help()  # Replace 'myplugin' with your plugin's command



# def test_rebalance_starts(node_factory):
#     l2 = node_factory.get_node()
#     # Test dynamically
#     l2.rpc.plugin_start(plugin_path)
#     l2.daemon.wait_for_log("Plugin rebalance initialized.*")
#     l2.rpc.plugin_stop(plugin_path)
#     l2.rpc.plugin_start(plugin_path)
#     l2.daemon.wait_for_log("Plugin rebalance initialized.*")
#     l2.stop()
#     # Then statically
#     l2.daemon.opts["plugin"] = plugin_path
#     l2.start()
#     # Start at 0 and 're-await' the two inits above. Otherwise this is flaky.
#     l2.daemon.logsearch_start = 0
#     l2.daemon.wait_for_logs(["Plugin rebalance initialized.*",
#                              "Plugin rebalance initialized.*",
#                              "Plugin rebalance initialized.*"])



# # waits for a bunch of nodes HTLCs to settle
# def wait_for_all_htlcs(nodes):
#     for n in nodes:
#         n.wait_for_htlcs()


# # waits for all nodes to have all scids gossip active
# def wait_for_all_active(nodes, scids):
#     for n in nodes:
#         for scid in scids:
#             n.wait_channel_active(scid)


# def test_rebalance_starts(node_factory):
#     l2 = node_factory.get_node()
#     # Test dynamically
#     l2.rpc.plugin_start(plugin_path)
#     l2.daemon.wait_for_log("Plugin rebalance initialized.*")
#     l2.rpc.plugin_stop(plugin_path)
#     l2.rpc.plugin_start(plugin_path)
#     l2.daemon.wait_for_log("Plugin rebalance initialized.*")
#     l2.stop()
#     # Then statically
#     l2.daemon.opts["plugin"] = plugin_path
#     l2.start()
#     # Start at 0 and 're-await' the two inits above. Otherwise this is flaky.
#     l2.daemon.logsearch_start = 0
#     l2.daemon.wait_for_logs(["Plugin rebalance initialized.*",
#                              "Plugin rebalance initialized.*",
#                              "Plugin rebalance initialized.*"])


# def test_rebalance_manual(node_factory, bitcoind):
#     l2, l3, l4 = node_factory.line_graph(3, opts=plugin_opt)
#     l2.daemon.logsearch_start = 0
#     l2.daemon.wait_for_log("Plugin rebalance initialized.*")
#     nodes = [l2, l3, l4]

#     # form a circle so we can do rebalancing
#     l4.connect(l2)
#     l4.fundchannel(l2)

#     # get scids
#     scid12 = l2.get_channel_scid(l3)
#     scid23 = l3.get_channel_scid(l4)
#     scid31 = l4.get_channel_scid(l2)
#     scids = [scid12, scid23, scid31]

#     # wait for each others gossip
#     bitcoind.generate_block(6)
#     for n in nodes:
#         for scid in scids:
#             n.wait_channel_active(scid)

#     # check we can do an auto amount rebalance
#     result = l2.rpc.rebalance(scid12, scid31)
#     print(result)
#     assert result['status'] == 'complete'
#     assert result['outgoing_scid'] == scid12
#     assert result['incoming_scid'] == scid31
#     assert result['hops'] == 3
#     assert result['received'] == '500000000msat'

#     # wait until listpeers is up2date
#     wait_for_all_htlcs(nodes)

#     # check that channels are now balanced
#     c12 = l2.rpc.listpeerchannels(l3.info['id'])['channels'][0]
#     c13 = l2.rpc.listpeerchannels(l4.info['id'])['channels'][0]
#     assert abs(0.5 - (Millisatoshi(c12['to_us_msat']) / Millisatoshi(c12['total_msat']))) < 0.01
#     assert abs(0.5 - (Millisatoshi(c13['to_us_msat']) / Millisatoshi(c13['total_msat']))) < 0.01

#     # check we can do a manual amount rebalance in the other direction
#     result = l2.rpc.rebalance(scid31, scid12, '250000000msat')
#     assert result['status'] == 'complete'
#     assert result['outgoing_scid'] == scid31
#     assert result['incoming_scid'] == scid12
#     assert result['hops'] == 3
#     assert result['received'] == '250000000msat'

#     # briefly check rebalancereport works
#     report = l2.rpc.rebalancereport()
#     assert report.get('rebalanceall_is_running') is False
#     assert report.get('total_successful_rebalances') == 2


# def test_rebalance_all(node_factory, bitcoind):
#     l2, l3, l4 = node_factory.line_graph(3, opts=plugin_opt)
#     l2.daemon.logsearch_start = 0
#     l2.daemon.wait_for_log("Plugin rebalance initialized.*")
#     nodes = [l2, l3, l4]

#     # check we get an error if theres just one channel
#     result = l2.rpc.rebalanceall()
#     assert result['message'] == 'Error: Not enough open channels to rebalance anything'

#     # now we add another 100% outgoing liquidity to l2 which does not help
#     l5 = node_factory.get_node()
#     l2.connect(l5)
#     l2.fundchannel(l5)

#     # test this is still not possible
#     result = l2.rpc.rebalanceall()
#     assert result['message'] == 'Error: Not enough liquidity to rebalance anything'

#     # remove l5 it does not distort further testing
#     l2.rpc.close(l2.get_channel_scid(l5))

#     # now we form a circle so we can do actually rebalanceall
#     l4.connect(l2)
#     l4.fundchannel(l2)

#     # get scids
#     scid12 = l2.get_channel_scid(l3)
#     scid23 = l3.get_channel_scid(l4)
#     scid31 = l4.get_channel_scid(l2)
#     scids = [scid12, scid23, scid31]

#     # wait for each others gossip
#     bitcoind.generate_block(6)
#     wait_for_all_active(nodes, scids)

#     # check that theres nothing to stop when theres nothing to stop
#     result = l2.rpc.rebalancestop()
#     assert result['message'] == "No rebalance is running, nothing to stop."

#     # check the rebalanceall starts
#     result = l2.rpc.rebalanceall(feeratio=5.0)  # we need high fees to work
#     assert result['message'].startswith('Rebalance started')
#     l2.daemon.wait_for_logs([f"tries to rebalance: {scid12} -> {scid31}",
#                              f"Automatic rebalance finished"])

#     # check additional calls to stop return 'nothing to stop' + last message
#     result = l2.rpc.rebalancestop()['message']
#     assert result.startswith("No rebalance is running, nothing to stop. "
#                              "Last 'rebalanceall' gave: Automatic rebalance finished")

#     # wait until listpeers is up2date
#     wait_for_all_htlcs(nodes)

#     # check that channels are now balanced
#     c12 = l2.rpc.listpeerchannels(l3.info['id'])['channels'][0]
#     c13 = l2.rpc.listpeerchannels(l4.info['id'])['channels'][0]
#     assert abs(0.5 - (Millisatoshi(c12['to_us_msat']) / Millisatoshi(c12['total_msat']))) < 0.01
#     assert abs(0.5 - (Millisatoshi(c13['to_us_msat']) / Millisatoshi(c13['total_msat']))) < 0.01

#     # briefly check rebalancereport works
#     report = l2.rpc.rebalancereport()
#     assert report.get('rebalanceall_is_running') is False
#     assert report.get('total_successful_rebalances') == 2