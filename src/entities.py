import math
from src import config as cfg


class Enemy:

    def __init__(self, path, wave):
        self.path = [
            (node[0] * cfg.GRID_SIZE + cfg.GRID_SIZE // 2,
             node[1] * cfg.GRID_SIZE + cfg.GRID_SIZE // 2)
            for node in path
        ]
        self.path_index = 0
        self.x, self.y = self.path[0] if self.path else (0, 0)

        self.max_hp = int(cfg.BASE_ENEMY_HP * (1 + (wave - 1) * cfg.ENEMY_HP_SCALE))
        self.hp = self.max_hp
        self.speed = min(cfg.MAX_ENEMY_SPEED,
                         cfg.BASE_ENEMY_SPEED + (wave - 1) * cfg.ENEMY_SPEED_SCALE)
        self.reward = cfg.BASE_ENEMY_REWARD + (wave // cfg.REWARD_WAVE_DIVISOR)
        self.distance_traveled = 0

    def is_alive(self):
        return self.hp > 0

    def move(self, dt):
        if self.path_index >= len(self.path) - 1:
            return True

        target_x, target_y = self.path[self.path_index + 1]
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)
        step = self.speed * dt

        if dist <= step:
            self.x, self.y = target_x, target_y
            self.path_index += 1
        else:
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step
            self.distance_traveled += step
        return False

    def tick(self, dt):
        if not self.is_alive():
            return "DEAD"
        if self.move(dt):
            return "FINISHED"
        return "RUNNING"


class Tower:

    base_damage = 0
    base_range = 0
    max_cd = 0
    color = cfg.WHITE
    cost = 0
    type_name = ""

    def __init__(self, gx, gy, level=1):
        self.gx = gx
        self.gy = gy
        self.x = gx * cfg.GRID_SIZE + cfg.GRID_SIZE // 2
        self.y = gy * cfg.GRID_SIZE + cfg.GRID_SIZE // 2
        self.cooldown = 0
        self.level = level
        self.upgrade_stats(level)

    def upgrade_stats(self, level):
        self.damage = int(self.base_damage * (1 + (level - 1) * cfg.DAMAGE_SCALE))
        self.range = int(self.base_range * (1 + (level - 1) * cfg.RANGE_SCALE))

    def has_line_of_sight(self, target, obstacles):
        """Алгоритм Брезенхэма — растеризация отрезка на сетке.

        Рисует «линию» из клеток от башни до цели. Если хоть одна
        клетка на этой линии — препятствие, значит видимости нет.

        Работает так:
        1. Вычисляем dx, dy — расстояния по осям до цели
        2. sx, sy — направление шага (+1 или -1 по каждой оси)
        3. err — ошибка накопления. Определяет, когда делать шаг
           по второй оси. Когда err смещается за порог — шагаем.
        4. e2 = 2*err — удвоенная ошибка для сравнения без дробей:
           - e2 > -dy → шаг по X (горизонтальный)
           - e2 < dx  → шаг по Y (вертикальный)
        5. Повторяем, пока не дойдём до клетки цели.
        """
        target_gx = int(target.x // cfg.GRID_SIZE)
        target_gy = int(target.y // cfg.GRID_SIZE)
        curr_x, curr_y = self.gx, self.gy
        end_x, end_y = target_gx, target_gy

        dx = abs(end_x - curr_x)
        dy = abs(end_y - curr_y)
        sx = 1 if curr_x < end_x else -1
        sy = 1 if curr_y < end_y else -1
        err = dx - dy

        while (curr_x, curr_y) != (end_x, end_y):
            if (curr_x, curr_y) in obstacles:
                return False
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                curr_x += sx
            if e2 < dx:
                err += dx
                curr_y += sy
        return True

    def find_target(self, candidates, obstacles):
        best_target = None
        max_progress = -1.0

        for enemy in candidates:
            if enemy.is_alive():
                dist = math.hypot(enemy.x - self.x, enemy.y - self.y)
                if dist <= self.range and enemy.distance_traveled > max_progress:
                    if self.has_line_of_sight(enemy, obstacles):
                        max_progress = enemy.distance_traveled
                        best_target = enemy
        return best_target

    def update_and_shoot(self, projectiles, dt, obstacles, spatial_hash):
        if self.cooldown > 0:
            self.cooldown -= dt
            return

        candidates = spatial_hash.query_radius(self.x, self.y, self.range)
        target = self.find_target(candidates, obstacles)
        if target:
            projectiles.append(Projectile(self.x, self.y, target, self.damage))
            self.cooldown = self.max_cd


class LMGTower(Tower):
    base_damage = 20
    base_range = 140
    max_cd = 0.3
    color = cfg.BLUE
    cost = 50
    type_name = "LMG"


class SniperTower(Tower):
    base_damage = 70
    base_range = 240
    max_cd = 1.2
    color = cfg.PURPLE
    cost = 125
    type_name = "SNIPER"


TOWER_TYPES = {
    "LMG": LMGTower,
    "SNIPER": SniperTower,
}


def create_tower(gx, gy, tower_type, level=1):
    tower_class = TOWER_TYPES[tower_type]
    return tower_class(gx, gy, level)


class Projectile:

    def __init__(self, x, y, target, damage):
        self.x = x
        self.y = y
        self.target = target
        self.damage = damage
        self.active = True

    def update(self, dt, active_enemies):
        if self.target not in active_enemies or not self.target.is_alive():
            self.active = False
            return

        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)

        if dist <= cfg.PROJECTILE_HIT_RADIUS:
            self.target.hp -= self.damage
            self.active = False
            return

        step = cfg.PROJECTILE_SPEED * dt
        if dist <= step:
            self.target.hp -= self.damage
            self.active = False
        else:
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step
