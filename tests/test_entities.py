import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import config as cfg
from src.entities import (
    Enemy, Tower, LMGTower, SniperTower,
    create_tower, Projectile, TOWER_TYPES,
)


class TestEnemy(unittest.TestCase):

    def setUp(self):
        cfg.cols = 25
        cfg.rows = 15

    def test_enemy_starts_alive(self):
        enemy = Enemy([(0, 7), (1, 7)], wave=1)
        self.assertTrue(enemy.is_alive())
        self.assertEqual(enemy.hp, enemy.max_hp)

    def test_hp_grows_with_wave(self):
        e1 = Enemy([(0, 7), (1, 7)], wave=1)
        e5 = Enemy([(0, 7), (1, 7)], wave=5)
        self.assertGreater(e5.max_hp, e1.max_hp)

    def test_speed_grows_with_wave(self):
        e1 = Enemy([(0, 7), (1, 7)], wave=1)
        e10 = Enemy([(0, 7), (1, 7)], wave=10)
        self.assertGreaterEqual(e10.speed, e1.speed)

    def test_speed_has_max_limit(self):
        e100 = Enemy([(0, 7), (1, 7)], wave=100)
        self.assertLessEqual(e100.speed, cfg.MAX_ENEMY_SPEED)

    def test_tick_returns_dead_when_no_hp(self):
        enemy = Enemy([(0, 7), (1, 7)], wave=1)
        enemy.hp = 0
        self.assertEqual(enemy.tick(0.016), "DEAD")

    def test_tick_returns_running_normally(self):
        enemy = Enemy([(0, 7), (5, 7)], wave=1)
        self.assertEqual(enemy.tick(0.016), "RUNNING")

    def test_move_changes_position(self):
        enemy = Enemy([(0, 7), (10, 7)], wave=1)
        old_x = enemy.x
        enemy.move(0.1)
        self.assertNotEqual(enemy.x, old_x)


class TestTowerInheritance(unittest.TestCase):

    def setUp(self):
        cfg.cols = 25
        cfg.rows = 15

    def test_lmg_is_tower(self):
        tower = LMGTower(5, 5)
        self.assertIsInstance(tower, Tower)

    def test_sniper_is_tower(self):
        tower = SniperTower(5, 5)
        self.assertIsInstance(tower, Tower)

    def test_lmg_stats(self):
        tower = LMGTower(5, 5)
        self.assertEqual(tower.type_name, "LMG")
        self.assertEqual(tower.cost, 50)
        self.assertGreater(tower.damage, 0)
        self.assertGreater(tower.range, 0)

    def test_sniper_stats(self):
        tower = SniperTower(5, 5)
        self.assertEqual(tower.type_name, "SNIPER")
        self.assertEqual(tower.cost, 125)

    def test_sniper_hits_harder(self):
        lmg = LMGTower(5, 5)
        sniper = SniperTower(5, 5)
        self.assertGreater(sniper.damage, lmg.damage)

    def test_sniper_has_longer_range(self):
        lmg = LMGTower(5, 5)
        sniper = SniperTower(5, 5)
        self.assertGreater(sniper.range, lmg.range)

    def test_upgrade_increases_damage(self):
        t1 = LMGTower(5, 5, level=1)
        t3 = LMGTower(5, 5, level=3)
        self.assertGreater(t3.damage, t1.damage)

    def test_upgrade_increases_range(self):
        t1 = SniperTower(5, 5, level=1)
        t3 = SniperTower(5, 5, level=3)
        self.assertGreater(t3.range, t1.range)

    def test_create_tower_lmg(self):
        tower = create_tower(3, 3, "LMG")
        self.assertIsInstance(tower, LMGTower)

    def test_create_tower_sniper(self):
        tower = create_tower(3, 3, "SNIPER")
        self.assertIsInstance(tower, SniperTower)

    def test_tower_types_dict(self):
        self.assertIn("LMG", TOWER_TYPES)
        self.assertIn("SNIPER", TOWER_TYPES)


class TestProjectile(unittest.TestCase):

    def setUp(self):
        cfg.cols = 25
        cfg.rows = 15

    def test_projectile_hits_close_target(self):
        enemy = Enemy([(0, 7), (1, 7)], wave=1)
        proj = Projectile(enemy.x, enemy.y, enemy, 10)
        old_hp = enemy.hp
        proj.update(0.016, [enemy])
        self.assertLess(enemy.hp, old_hp)
        self.assertFalse(proj.active)

    def test_projectile_deactivates_if_target_dead(self):
        enemy = Enemy([(0, 7), (1, 7)], wave=1)
        proj = Projectile(0, 0, enemy, 10)
        enemy.hp = 0
        proj.update(0.016, [enemy])
        self.assertFalse(proj.active)

    def test_projectile_moves_toward_target(self):
        enemy = Enemy([(0, 7), (10, 7)], wave=1)
        proj = Projectile(0, 0, enemy, 10)
        old_x = proj.x
        proj.update(0.016, [enemy])
        self.assertNotEqual(proj.x, old_x)


if __name__ == "__main__":
    unittest.main()
