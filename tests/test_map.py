import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import config as cfg
from src.map_generator import MapGenerator


class TestMapGenerator(unittest.TestCase):

    def setUp(self):
        cfg.cols = 25
        cfg.rows = 15
        self.start = (0, 7)
        self.goal = (24, 7)

    def test_returns_set(self):
        result = MapGenerator.generate_canyon(self.start, self.goal, 12345)
        self.assertIsInstance(result, set)

    def test_start_not_blocked(self):
        obstacles = MapGenerator.generate_canyon(self.start, self.goal, 12345)
        self.assertNotIn(self.start, obstacles)

    def test_goal_not_blocked(self):
        obstacles = MapGenerator.generate_canyon(self.start, self.goal, 12345)
        self.assertNotIn(self.goal, obstacles)

    def test_same_seed_same_map(self):
        map1 = MapGenerator.generate_canyon(self.start, self.goal, 42)
        map2 = MapGenerator.generate_canyon(self.start, self.goal, 42)
        self.assertEqual(map1, map2)

    def test_different_seed_different_map(self):
        map1 = MapGenerator.generate_canyon(self.start, self.goal, 100)
        map2 = MapGenerator.generate_canyon(self.start, self.goal, 200)
        self.assertNotEqual(map1, map2)

    def test_generates_obstacles(self):
        obstacles = MapGenerator.generate_canyon(self.start, self.goal, 12345)
        self.assertGreater(len(obstacles), 0)

    def test_obstacles_within_grid(self):
        obstacles = MapGenerator.generate_canyon(self.start, self.goal, 12345)
        for x, y in obstacles:
            self.assertTrue(0 <= x < cfg.cols)
            self.assertTrue(0 <= y < cfg.rows)


if __name__ == "__main__":
    unittest.main()
