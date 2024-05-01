import os
from pyln.testing.fixtures import *  # noqa: F401,F403
from pyln.client import Millisatoshi

plugin_path = os.path.join(os.path.dirname(__file__), './bolt12-prism.py')
plugin_opt = {'plugin': plugin_path}

# spin up a network
def test_basic_test(node_factory):
    # Start two lightning nodes
    l1, l2, l3, l4, l5 = node_factory.get_node(), node_factory.get_node(), node_factory.get_node(), node_factory.get_node(), node_factory.get_node()

    # Connect the nodes in a prism layout.
    l1.rpc.connect(l2.info['id'], 'localhost', l2.port) # Alice -> Bob
    l2.rpc.connect(l3.info['id'], 'localhost', l3.port) # Bob -> Carol
    l2.rpc.connect(l4.info['id'], 'localhost', l4.port) # Bob -> Dave
    l2.rpc.connect(l5.info['id'], 'localhost', l5.port) # Bob -> Erin

    # Check the list of peers to confirm connection
    # Alice -> Bob
    assert len(l1.rpc.listpeers()['peers']) == 1
    assert l1.rpc.listpeers()['peers'][0]['id'] == l2.info['id']

    # Bob -> all others
    assert len(l2.rpc.listpeers()['peers']) == 4
    # TODO we don't really know which index an id will be in; just search for existence?

    #try:
    assert l2.rpc.plugin_start(plugin_path), "Failed to start plugin"
    assert l2.rpc.plugin_list()
    assert l2.rpc.prism_list()
    assert l2.rpc.prism_bindinglist()
    assert l2.rpc.plugin_stop(plugin_path)
