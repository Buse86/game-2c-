import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import config as cfg
from src.navigation import NavigationEngine


class TestNavigation(unittest.TestCase):

    def setUp(self):
        cfg.cols = 25
        cfg.rows = 15
        self.nav = NavigationEngine()

    def test_path_exists_on_empty_grid(self):
        path = self.nav.find_path((0, 7), (24, 7), set())
        self.assertTrue(len(path) > 0)

    def test_path_ends_at_goal(self):
        path = self.nav.find_path((0, 7), (24, 7), set())
        self.assertEqual(path[-1], (24, 7))

    def test_path_blocked_returns_empty(self):
        wall = {(5, y) for y in range(15)}
        path = self.nav.find_path((0, 7), (24, 7), wall)
        self.assertEqual(path, [])

    def test_is_passable_on_empty_grid(self):
        result = self.nav.is_passable((0, 7), (24, 7), set())
        self.assertTrue(result)

    def test_is_not_passable_when_wall(self):
        wall = {(5, y) for y in range(15)}
        result = self.nav.is_passable((0, 7), (24, 7), wall)
        self.assertFalse(result)

    def test_path_avoids_obstacles(self):
        obstacles = {(5, 6), (5, 7), (5, 8)}
        path = self.nav.find_path((0, 7), (10, 7), obstacles)
        for node in path:
            self.assertNotIn(node, obstacles)

    def test_start_equals_goal(self):
        path = self.nav.find_path((5, 5), (5, 5), set())
        self.assertEqual(path, [])


if __name__ == "__main__":
    unittest.main()
