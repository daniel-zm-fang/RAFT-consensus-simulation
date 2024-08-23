import unittest
from simulation import Node, Cluster, NodeRole

class TestInitialState(unittest.TestCase):
    def setUp(self):
        self.cluster = Cluster(node_count=3)

    def test_initial_node_state(self):
        """Test that nodes are initialized with correct default values."""
        for node in self.cluster.nodes:
            self.assertEqual(node.role, NodeRole.FOLLOWER)
            self.assertEqual(node.term, 0)
            self.assertEqual(node.voted_for, None)
