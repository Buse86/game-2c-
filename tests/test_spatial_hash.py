import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import config as cfg
from src.spatial_hash import SpatialHash


class FakeObj:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class TestSpatialHash(unittest.TestCase):

    def test_insert_and_query(self):
        sh = SpatialHash(cell_size=100)
        obj = FakeObj(50, 50)
        sh.insert(obj)
        result = sh.query_radius(50, 50, 60)
        self.assertIn(obj, result)

    def test_query_empty(self):
        sh = SpatialHash(cell_size=100)
        result = sh.query_radius(50, 50, 60)
        self.assertEqual(result, [])

    def test_clear(self):
        sh = SpatialHash(cell_size=100)
        sh.insert(FakeObj(10, 10))
        sh.clear()
        result = sh.query_radius(10, 10, 50)
        self.assertEqual(result, [])

    def test_far_object_not_in_result(self):
        sh = SpatialHash(cell_size=100)
        near = FakeObj(50, 50)
        far = FakeObj(900, 900)
        sh.insert(near)
        sh.insert(far)
        result = sh.query_radius(50, 50, 80)
        self.assertIn(near, result)
        self.assertNotIn(far, result)

    def test_multiple_objects_same_cell(self):
        sh = SpatialHash(cell_size=100)
        a = FakeObj(10, 10)
        b = FakeObj(20, 20)
        sh.insert(a)
        sh.insert(b)
        result = sh.query_radius(15, 15, 50)
        self.assertIn(a, result)
        self.assertIn(b, result)

    def test_query_covers_neighbor_cells(self):
        sh = SpatialHash(cell_size=100)
        obj = FakeObj(105, 105)
        sh.insert(obj)
        result = sh.query_radius(95, 95, 20)
        self.assertIn(obj, result)

    def test_large_radius_finds_all(self):
        sh = SpatialHash(cell_size=100)
        objs = [FakeObj(i * 50, i * 50) for i in range(5)]
        for o in objs:
            sh.insert(o)
        result = sh.query_radius(100, 100, 500)
        for o in objs:
            self.assertIn(o, result)


if __name__ == "__main__":
    unittest.main()
