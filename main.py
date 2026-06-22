import pygame
import math
import json
import os
import heapq
import random
import config as cfg

# Инициализация Pygame
pygame.init()

pygame.mixer.init()

pygame.mixer.music.load('kushnya.mp3')

# Запуск воспроизведения (-1 означает бесконечный цикл)
pygame.mixer.music.play(-1)


SCREEN = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("SOLID Dynamic Tower Defense (Upgrades & Deletion)")
CLOCK = pygame.time.Clock()

# Глобальные динамические переменные сетки
current_width, current_height = cfg.WIDTH, cfg.HEIGHT
cols, rows = current_width // cfg.GRID_SIZE, (current_height - 100) // cfg.GRID_SIZE

def update_grid_dimensions(w, h):
    global current_width, current_height, cols, rows
    current_width, current_height = w, h
    cols = max(5, w // cfg.GRID_SIZE)
    rows = max(5, (h - 100) // cfg.GRID_SIZE)

update_grid_dimensions(current_width, current_height)

# ==========================================
# 1. АЛГОРИТМЫ И ДВИЖОК НАВИГАЦИИ
# ==========================================

class NavigationEngine:
    def is_passable(self, start, goal, blocked):
        queue = [start]
        visited = {start}
        while queue:
            curr = queue.pop(0)
            if curr == goal: return True
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nxt = (curr[0] + dx, curr[1] + dy)
                if 0 <= nxt[0] < cols and 0 <= nxt[1] < rows:
                    if nxt not in blocked and nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)
        return False

    def find_path(self, start, goal, blocked):
        open_set = []
        heapq.heappush(open_set, (0, start)) 
        came_from = {}
        g_score = {start: 0}

        while open_set:
            current = heapq.heappop(open_set)[1]
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < cols and 0 <= neighbor[1] < rows and neighbor not in blocked:
                    tentative_g = g_score[current] + 1
                    if tentative_g < g_score.get(neighbor, float('inf')):
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f_score = tentative_g + (abs(neighbor[0]-goal[0]) + abs(neighbor[1]-goal[1]))
                        heapq.heappush(open_set, (f_score, neighbor))
        return []


# ==========================================
# 2. ПРОЦЕДУРНАЯ ГЕНЕРАЦИЯ КАРТЫ ПО СИДУ
# ==========================================

class MapGenerator:
    @staticmethod
    def generate_canyon(start, goal, world_seed):
        blocked = set()
        random.seed(world_seed)
        
        freq = random.uniform(0.3, 0.5)
        amp = random.uniform(2.5, 4.5)
        offset = random.randint(0, 100)

        for x in range(cols):
            center_y = int(rows / 2 + math.sin(x * freq + offset) * amp)
            center_y = max(2, min(rows - 3, center_y))
            
            for y in range(rows):
                if abs(y - center_y) > random.choice([2, 3]):
                    if (x, y) != start and (x, y) != goal:
                        blocked.add((x, y))
                        
        nav = NavigationEngine()
        if not nav.is_passable(start, goal, blocked):
            return set() 
        return blocked


# ==========================================
# 3. СУЩНОСТИ И ПОВЕДЕНИЕ ИИ
# ==========================================

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
        
        # Динамическое увеличение силы врагов с каждой волной
        self.max_hp = int(90 * (1 + (wave - 1) * 1.5))
        self.hp = self.max_hp
        self.speed = min(160, 80 + (wave - 1) * 4)
        
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
        # Оружие наносит больше урона и бьет дальше с каждым уровнем
        base_dmg = 20 if self.type == "LMG" else 70
        self.damage = int(base_dmg * (1 + (level - 1) * 0.3))
        
        self.range = 140 if self.type == "LMG" else 240
        # self.range = int(base_range * (1 + (level - 1) * 0.1))
        
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


# ==========================================
# 4. МЕНЕДЖЕР ИГРЫ И СИСТЕМА СОХРАНЕНИЙ
# ==========================================

class GameManager:
    def __init__(self, load_save):
        self.money, self.wave = 250, 1
        self.base_hp = 10  
        self.max_base_hp = 10
        self.tower_level = 1
        self.game_over = False
        self.world_seed = 0 
        
        self.upgrade_text = ""
        self.upgrade_text_timer = 0.0
        
        self.start_node = (0, rows // 2)
        self.end_node = (cols - 1, rows // 2)
        self.nav = NavigationEngine()
        
        self.enemies, self.towers, self.projectiles = [], [], []
        self.selected_type = "LMG"
        self.spawn_timer, self.enemies_to_spawn = 0, 0

        if load_save and os.path.exists("td_seed_save.json"):
            with open("td_seed_save.json", "r") as f:
                data = json.load(f)
                self.money, self.wave = data["money"], data["wave"]
                self.base_hp = data.get("base_hp", 10)
                self.max_base_hp = data.get("max_base_hp", 10)
                self.tower_level = data.get("tower_level", 1)
                self.world_seed = data["world_seed"] 
                
                self.obstacles = MapGenerator.generate_canyon(self.start_node, self.end_node, self.world_seed)
                while len(self.obstacles) == 0:
                    self.world_seed = random.randint(1, 9999999)
                    self.obstacles = MapGenerator.generate_canyon(self.start_node, self.end_node, self.world_seed)
                self.blocked_cells = self.obstacles.copy()
                
                for t_data in data.get("towers", []):
                    gx, gy, t_type = t_data[0], t_data[1], t_data[2]
                    self.towers.append(Tower(gx, gy, t_type, self.tower_level))
                    self.blocked_cells.add((gx, gy))
        else:
            self.obstacles = set()
            while len(self.obstacles) == 0:
                random.seed(None) 
                self.world_seed = random.randint(1, 9999999)
                self.obstacles = MapGenerator.generate_canyon(self.start_node, self.end_node, self.world_seed)
            self.blocked_cells = self.obstacles.copy()

        self.path = self.nav.find_path(self.start_node, self.end_node, self.blocked_cells)

    def save(self):
        if self.game_over: return
        towers_list = [[t.gx, t.gy, t.type] for t in self.towers]
        with open("td_seed_save.json", "w") as f:
            json.dump({
                "money": self.money, 
                "wave": self.wave, 
                "base_hp": self.base_hp,
                "max_base_hp": self.max_base_hp,
                "tower_level": self.tower_level,
                "world_seed": self.world_seed,  
                "towers": towers_list  
            }, f)

    def handle_click(self, pos):
        if self.game_over: return
        gx, gy = pos[0]//cfg.GRID_SIZE, pos[1]//cfg.GRID_SIZE
        cell = (gx, gy)
        
        if not (0 <= gx < cols and 0 <= gy < rows) or cell in self.blocked_cells: return
        if cell in self.path: return 

        cost = 50 if self.selected_type == "LMG" else 125
        if self.money >= cost:
            self.blocked_cells.add(cell)
            new_path = self.nav.find_path(self.start_node, self.end_node, self.blocked_cells)
            if new_path:
                self.path = new_path
                self.towers.append(Tower(gx, gy, self.selected_type, self.tower_level))
                self.money -= cost
                self.save() 
            else:
                self.blocked_cells.remove(cell)

    def handle_right_click(self, pos):
        # ФУНКЦИЯ УДАЛЕНИЯ ТУРЕЛИ (ПКМ)
        if self.game_over: return
        gx, gy = pos[0]//cfg.GRID_SIZE, pos[1]//cfg.GRID_SIZE
        cell = (gx, gy)
        
        for t in self.towers[:]:
            if t.gx == gx and t.gy == gy:
                cost = 50 if t.type == "LMG" else 125
                self.money += int(cost * 0.8) # Возврат 80% ресурсов
                self.towers.remove(t)
                self.blocked_cells.remove(cell)
                # Пересчитываем путь (он гарантированно найдется)
                self.path = self.nav.find_path(self.start_node, self.end_node, self.blocked_cells)
                self.save()
                break

    def handle_resize(self):
        self.start_node = (0, rows // 2)
        self.end_node = (cols - 1, rows // 2)
        
        temp_seed = self.world_seed
        new_obs = set()
        attempts = 0
        while len(new_obs) == 0 and attempts < 5:
            new_obs = MapGenerator.generate_canyon(self.start_node, self.end_node, temp_seed)
            temp_seed += 1
            attempts += 1
            
        if new_obs:
            self.obstacles = new_obs
            self.blocked_cells = self.obstacles.copy()
        
        valid_towers = []
        for t in self.towers:
            if 0 <= t.gx < cols and 0 <= t.gy < rows:
                valid_towers.append(t)
                self.blocked_cells.add((t.gx, t.gy))
        self.towers = valid_towers
        
        self.path = self.nav.find_path(self.start_node, self.end_node, self.blocked_cells)


# ==========================================
# ТОЧКА ВХОДА И ИГРОВОЙ ЦИКЛ
# ==========================================

def main():
    global SCREEN
    manager = None
    in_menu = True
    font = pygame.font.SysFont('Arial', 24)
    big_font = pygame.font.SysFont('Arial', 48, bold=True)
    
    btn_new = pygame.Rect(current_width//2 - 150, 260, 300, 50)
    btn_cont = pygame.Rect(current_width//2 - 150, 340, 300, 50)
    btn_to_menu = pygame.Rect(current_width - 180, current_height - 65, 150, 40)

    clock = pygame.time.Clock()
    accumulator = 0.0
    dt_fixed = 1 / 60.0 

    running = True
    while running:
        duration = clock.tick(120) 
        accumulator += duration / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                running = False
                
            elif event.type == pygame.VIDEORESIZE:
                SCREEN = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                update_grid_dimensions(event.w, event.h)
                
                btn_new.x, btn_new.y = current_width//2 - 150, 260
                btn_cont.x, btn_cont.y = current_width//2 - 150, 340
                btn_to_menu.x, btn_to_menu.y = current_width - 180, current_height - 65
                
                if manager:
                    manager.handle_resize()
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if in_menu:
                    if event.button == 1:
                        if btn_new.collidepoint(pos):
                            if os.path.exists("td_seed_save.json"):
                                os.remove("td_seed_save.json")
                            manager = GameManager(load_save=False)
                            manager.enemies_to_spawn = 5
                            in_menu = False
                        elif btn_cont.collidepoint(pos) and os.path.exists("td_seed_save.json"):
                            manager = GameManager(load_save=True)
                            manager.enemies_to_spawn = 5
                            in_menu = False
                else:
                    if btn_to_menu.collidepoint(pos) and event.button == 1:
                        manager.save()  
                        in_menu = True
                    elif pos[1] < rows * cfg.GRID_SIZE and not manager.game_over: 
                        if event.button == 1:   # ЛКМ — Строить
                            manager.handle_click(pos)
                        elif event.button == 3: # ПКМ — Удалять
                            manager.handle_right_click(pos)
                    elif manager.game_over and event.button == 1: 
                        in_menu = True
                        
            elif event.type == pygame.KEYDOWN and not in_menu and not manager.game_over:
                if event.key == pygame.K_1: manager.selected_type = "LMG"
                if event.key == pygame.K_2: manager.selected_type = "SNIPER"

        if in_menu:
            SCREEN.fill((20, 20, 20))
            pygame.draw.rect(SCREEN, cfg.BLUE, btn_new, border_radius=4)
            cc = cfg.GREEN if os.path.exists("td_seed_save.json") else (70,70,70)
            pygame.draw.rect(SCREEN, cc, btn_cont, border_radius=4)
            SCREEN.blit(font.render("Новая игра", True, cfg.WHITE), (btn_new.x+85, btn_new.y+12))
            SCREEN.blit(font.render("Продолжить", True, cfg.WHITE), (btn_cont.x+85, btn_cont.y+12))
        else:
            if not manager.game_over:
                while accumulator >= dt_fixed:
                    accumulator -= dt_fixed
                    
                    if manager.upgrade_text_timer > 0:
                        manager.upgrade_text_timer -= dt_fixed

                    if manager.enemies_to_spawn > 0:
                        manager.spawn_timer += dt_fixed
                        if manager.spawn_timer >= 0.7:
                            if manager.path: 
                                manager.enemies.append(Enemy(manager.path, manager.wave))
                            manager.enemies_to_spawn -= 1
                            manager.spawn_timer = 0

                    for e in manager.enemies[:]:
                        ai_status = EnemyAI.tick(e, dt_fixed)
                        if ai_status == "FINISHED": 
                            manager.base_hp -= 1
                            manager.enemies.remove(e)
                            if manager.base_hp <= 0:
                                manager.game_over = True
                                if os.path.exists("td_seed_save.json"):
                                    os.remove("td_seed_save.json") 
                        elif ai_status == "DEAD":
                            manager.money += e.reward
                            manager.enemies.remove(e)

                    for t in manager.towers: 
                        t.update_and_shoot(manager.projectiles, dt_fixed, manager.enemies, manager.obstacles)
                        
                    for p in manager.projectiles[:]:
                        p.update(dt_fixed, manager.enemies)
                        if not p.active: manager.projectiles.remove(p)

                    # Триггер завершения волны
                    if not manager.enemies and manager.enemies_to_spawn == 0:
                        # ПРОВЕРКА КАЖДОЙ 10-Й ВОЛНЫ
                        if manager.wave % 10 == 0:
                            manager.tower_level += 1
                            manager.max_base_hp += 5
                            manager.base_hp = manager.max_base_hp # Хилим базу до нового максимума
                            
                            for t in manager.towers:
                                t.upgrade_stats(manager.tower_level)
                                
                            manager.upgrade_text = f"10 ВОЛН ПРОЙДЕНО! Орудия улучшены до Т-{manager.tower_level}! База укреплена!"
                            manager.upgrade_text_timer = 4.0 # Таймер плашки уведомления
                            
                        manager.wave += 1
                        manager.save()
                        manager.enemies_to_spawn = 5 + manager.wave * 2
            else:
                accumulator = 0 

            # Отрисовка уровня
            SCREEN.fill(cfg.SAND)
            for cx in range(cols):
                for cy in range(rows):
                    pygame.draw.rect(SCREEN, (225, 215, 160), (cx*cfg.GRID_SIZE, cy*cfg.GRID_SIZE, cfg.GRID_SIZE, cfg.GRID_SIZE), 1)
                    if (cx, cy) in manager.obstacles:
                        pygame.draw.rect(SCREEN, cfg.BROWN, (cx*cfg.GRID_SIZE, cy*cfg.GRID_SIZE, cfg.GRID_SIZE, cfg.GRID_SIZE))
            
            for n in manager.path:
                pygame.draw.rect(SCREEN, (215, 240, 215), (n[0]*cfg.GRID_SIZE, n[1]*cfg.GRID_SIZE, cfg.GRID_SIZE, cfg.GRID_SIZE))
            
            pygame.draw.rect(SCREEN, cfg.GREEN, (manager.start_node[0]*cfg.GRID_SIZE, manager.start_node[1]*cfg.GRID_SIZE, cfg.GRID_SIZE, cfg.GRID_SIZE))
            pygame.draw.rect(SCREEN, cfg.BLUE, (manager.end_node[0]*cfg.GRID_SIZE, manager.end_node[1]*cfg.GRID_SIZE, cfg.GRID_SIZE, cfg.GRID_SIZE))
            
            if not manager.game_over:
                bx, by = manager.end_node[0] * cfg.GRID_SIZE, manager.end_node[1] * cfg.GRID_SIZE
                pygame.draw.rect(SCREEN, cfg.RED, (bx, by - 12, cfg.GRID_SIZE, 5))
                pygame.draw.rect(SCREEN, cfg.GREEN, (bx, by - 12, cfg.GRID_SIZE * (manager.base_hp / manager.max_base_hp), 5))

            for t in manager.towers: pygame.draw.rect(SCREEN, t.color, (t.gx*cfg.GRID_SIZE+4, t.gy*cfg.GRID_SIZE+4, cfg.GRID_SIZE-8, cfg.GRID_SIZE-8))
            for e in manager.enemies: 
                pygame.draw.circle(SCREEN, cfg.RED, (int(e.x), int(e.y)), 12)
                pygame.draw.rect(SCREEN, cfg.RED, (e.x - 15, e.y - 20, 30, 4))
                pygame.draw.rect(SCREEN, cfg.GREEN, (e.x - 15, e.y - 20, 30 * (e.hp / e.max_hp), 4))
                
            for p in manager.projectiles: pygame.draw.circle(SCREEN, cfg.YELLOW, (int(p.x), int(p.y)), 4)

            # HUD Панель
            pygame.draw.rect(SCREEN, cfg.DARK_GREY, (0, current_height-100, current_width, 100))
            SCREEN.blit(font.render(f"Gold: {manager.money}  Wave: {manager.wave}  Base HP: {manager.base_hp}/{manager.max_base_hp}", True, cfg.WHITE), (30, current_height-75))
            SCREEN.blit(font.render(f"Weapon Lvl: T-{manager.tower_level} (ПКМ на турель — удалить)", True, (200, 200, 200)), (30, current_height-40))
            SCREEN.blit(font.render(f"Weapon: {manager.selected_type} (1: LMG, 2: SNIPER)", True, cfg.WHITE), (current_width//2 - 100, current_height-60))

            pygame.draw.rect(SCREEN, cfg.RED, btn_to_menu, border_radius=4)
            SCREEN.blit(font.render("В меню", True, cfg.WHITE), (btn_to_menu.x + 42, btn_to_menu.y + 7))

            # Рендеринг сообщения об апгрейде
            if manager.upgrade_text_timer > 0:
                t_surf = font.render(manager.upgrade_text, True, cfg.YELLOW)
                t_rect = t_surf.get_rect(center=(current_width // 2, 40))
                b_rect = pygame.Rect(t_rect.x - 15, t_rect.y - 8, t_rect.width + 30, t_rect.height + 16)
                pygame.draw.rect(SCREEN, (15, 15, 15), b_rect, border_radius=6)
                pygame.draw.rect(SCREEN, cfg.YELLOW, b_rect, width=2, border_radius=6)
                SCREEN.blit(t_surf, t_rect)

            if manager.game_over:
                s = pygame.Surface((current_width, current_height-100), pygame.SRCALPHA)
                s.fill((0, 0, 0, 180)) 
                SCREEN.blit(s, (0, 0))
                text_go = big_font.render("GAME OVER", True, cfg.RED)
                text_sub = font.render("Главный дом разрушен! Кликните для меню.", True, cfg.WHITE)
                SCREEN.blit(text_go, (current_width//2 - text_go.get_width()//2, current_height//2 - 60))
                SCREEN.blit(text_sub, (current_width//2 - text_sub.get_width()//2, current_height//2 + 10))

        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()