import os
from pyln.testing.fixtures import *  # noqa: F401,F403
from pyln.client import Millisatoshi


plugin_path = os.path.join(os.path.dirname(__file__), "bolt12_prism.py")
plugin_opt = {'plugin': plugin_path}


# def test_bolt12_prism_dynamic_start(node_factory):
#     # assert 0 == 1
#     # l1 = node_factory.get_node(opts=plugin_opt)
#     l1 = node_factory.get_node()
#     l1.rpc.plugin_start(plugin_path)
#     l1.stop()

# def test_prism_list(node_factory):
#     l1 = node_factory.get_node()

#     l1.rpc.plugin_start(plugin_path)
#     l1.daemon.wait_for_log("Plugin bolt12_prism.py initialized.*")
#     l1.rpc.plugin_stop(plugin_path)
#     l1.rpc.plugin_start(plugin_path)
#     l1.daemon.wait_for_log("Plugin bolt12_prism.py initialized.*")
#     l1.stop()
#     # # Then statically
#     # l1.daemon.opts["plugin"] = plugin_path
#     # l1.start()
#     # # Start at 0 and 're-await' the two inits above. Otherwise this is flaky.
#     # l1.daemon.logsearch_start = 0
#     # l1.daemon.wait_for_logs(["Plugin rebalance initialized.*",
#     #                          "Plugin rebalance initialized.*",
#     #                          "Plugin rebalance initialized.*"])




# this alone works
def test_my_feature(node_factory):
    # Start two lightning nodes
    l1, l2 = node_factory.get_node(), node_factory.get_node()

    # Example test to check if nodes are connected
    l1.rpc.connect(l2.info['id'], 'localhost', l2.port)

    # Check the list of peers to confirm connection
    assert len(l1.rpc.listpeers()['peers']) == 1
    assert l1.rpc.listpeers()['peers'][0]['id'] == l2.info['id']
