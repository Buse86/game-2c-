import math
from src import config as cfg

class EnemyAI:
    @staticmethod
    def tick(enemy, dt):
        if enemy.hp <= 0: return "DEAD"
        if enemy.move(dt): return "FINISHED"
        return "RUNNING"

class Enemy:
    def __init__(self, path, wave):
        self.path = [(n[0]*cfg.GRID_SIZE + cfg.GRID_SIZE//2, n[1]*cfg.GRID_SIZE + cfg.GRID_SIZE//2) for n in path]
        self.path_index = 0
        self.x, self.y = self.path[0] if self.path else (0,0)
        
        self.max_hp = int(90 * (1 + (wave - 1) * 0.25))
        self.hp = self.max_hp
        self.speed = min(160, 80 + (wave - 1) * 3) 
        self.reward = 15 + (wave // 3)
        self.distance_traveled = 0

    def move(self, dt):
        if self.path_index >= len(self.path) - 1: return True
        tx, ty = self.path[self.path_index + 1]
        dx, dy = tx - self.x, ty - self.y
        dist = math.hypot(dx, dy)
        step = self.speed * dt
        if dist <= step:
            self.x, self.y = tx, ty
            self.path_index += 1
        else:
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step
            self.distance_traveled += step
        return False

class Tower:
    def __init__(self, gx, gy, t_type, level=1):
        self.gx, self.gy = gx, gy
        self.type = t_type  
        self.x, self.y = gx*cfg.GRID_SIZE + cfg.GRID_SIZE//2, gy*cfg.GRID_SIZE + cfg.GRID_SIZE//2
        self.cooldown = 0
        self.color = cfg.BLUE if t_type == "LMG" else cfg.PURPLE
        self.upgrade_stats(level)

    def upgrade_stats(self, level):
        base_dmg = 20 if self.type == "LMG" else 70
        self.damage = int(base_dmg * (1 + (level - 1) * 0.3))
        base_range = 140 if self.type == "LMG" else 240
        self.range = int(base_range * (1 + (level - 1) * 0.1))
        self.max_cd = 0.3 if self.type == "LMG" else 1.2

    def has_line_of_sight(self, target, obstacles):
        target_gx = int(target.x // cfg.GRID_SIZE)
        target_gy = int(target.y // cfg.GRID_SIZE)
        start_x, start_y = self.gx, self.gy
        end_x, end_y = target_gx, target_gy
        
        dx = abs(end_x - start_x)
        dy = abs(end_y - start_y)
        sx = 1 if start_x < end_x else -1
        sy = 1 if start_y < end_y else -1
        err = dx - dy
        curr_x, curr_y = start_x, start_y
        
        while (curr_x, curr_y) != (end_x, end_y):
            if (curr_x, curr_y) in obstacles: return False
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                curr_x += sx
            if e2 < dx:
                err += dx
                curr_y += sy
        return True

    def update_and_shoot(self, projectiles, dt, active_enemies, obstacles):
        if self.cooldown > 0:
            self.cooldown -= dt
            return
            
        best_target = None
        max_distance = -1.0  

        for t in active_enemies:
            if t.hp > 0:
                dist = math.hypot(t.x - self.x, t.y - self.y)
                if dist <= self.range:
                    if t.distance_traveled > max_distance:
                        if self.has_line_of_sight(t, obstacles):
                            max_distance = t.distance_traveled
                            best_target = t

        if best_target:
            projectiles.append(Projectile(self.x, self.y, best_target, self.damage))
            self.cooldown = self.max_cd

class Projectile:
    def __init__(self, x, y, target, damage):
        self.x, self.y = x, y
        self.target = target
        self.damage = damage
        self.active = True

    def update(self, dt, active_enemies):
        if self.target not in active_enemies or self.target.hp <= 0:
            self.active = False
            return
        dx, dy = self.target.x - self.x, self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist <= 15:
            self.target.hp -= self.damage
            self.active = False
            return
        
        step = 400 * dt
        if dist <= step:
            self.target.hp -= self.damage
            self.active = False
        else:
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step