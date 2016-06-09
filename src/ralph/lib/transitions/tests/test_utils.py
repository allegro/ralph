from django.test import TestCase

from ralph.lib.transitions.utils import _sort_graph_topologically, CycleError


class TopologicalSortTest(TestCase):
    def test_topological_sort(self):
        graph = {
            1: [],
            2: [1, 4],
            3: [],
            4: [1]
        }
        order = [a for a in _sort_graph_topologically(graph)]
        # order of 2 and 3 doesn't matter
        self.assertEqual(set(order[:2]), set([2, 3]))
        self.assertEqual(order[2:], [4, 1])

    def test_topological_sort_cycle(self):
        graph = {
            1: [2],
            2: [1, 4],
            3: [],
            4: [1]
        }
        with self.assertRaises(CycleError):
            [a for a in _sort_graph_topologically(graph)]
