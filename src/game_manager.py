import json
import os
import random
from src import config as cfg
from src.navigation import NavigationEngine
from src.map_generator import MapGenerator
from src.entities import create_tower, Enemy, TOWER_TYPES
from src.spatial_hash import SpatialHash


class GameManager:

    def __init__(self, load_save):
        self.money = cfg.START_MONEY
        self.wave = 1
        self.base_hp = cfg.START_HP
        self.max_base_hp = cfg.START_HP
        self.tower_level = 1
        self.game_over = False
        self.world_seed = 0

        self.upgrade_text = ""
        self.upgrade_text_timer = 0.0

        self.start_node = (0, cfg.rows // 2)
        self.end_node = (cfg.cols - 1, cfg.rows // 2)
        self.nav = NavigationEngine()

        self.enemies = []
        self.towers = []
        self.projectiles = []
        self.selected_type = "LMG"
        self.spawn_timer = 0
        self.enemies_to_spawn = 0
        self.spatial_hash = SpatialHash(cell_size=cfg.GRID_SIZE * 3)

        if load_save and os.path.exists("td_seed_save.json"):
            self._load_game()
        else:
            self._new_game()

        self.path = self.nav.find_path(self.start_node, self.end_node, self.blocked_cells)

    def _new_game(self):
        self.obstacles = set()
        while len(self.obstacles) == 0:
            random.seed(None)
            self.world_seed = random.randint(1, 9999999)
            self.obstacles = MapGenerator.generate_canyon(
                self.start_node, self.end_node, self.world_seed
            )
        self.blocked_cells = self.obstacles.copy()

    def _load_game(self):
        with open("td_seed_save.json", "r") as f:
            data = json.load(f)

        self.money = data["money"]
        self.wave = data["wave"]
        self.base_hp = data.get("base_hp", cfg.START_HP)
        self.max_base_hp = data.get("max_base_hp", cfg.START_HP)
        self.tower_level = data.get("tower_level", 1)
        self.world_seed = data["world_seed"]

        self.obstacles = MapGenerator.generate_canyon(
            self.start_node, self.end_node, self.world_seed
        )
        while len(self.obstacles) == 0:
            self.world_seed = random.randint(1, 9999999)
            self.obstacles = MapGenerator.generate_canyon(
                self.start_node, self.end_node, self.world_seed
            )
        self.blocked_cells = self.obstacles.copy()

        for tower_data in data.get("towers", []):
            gx, gy, tower_type = tower_data[0], tower_data[1], tower_data[2]
            tower = create_tower(gx, gy, tower_type, self.tower_level)
            self.towers.append(tower)
            self.blocked_cells.add((gx, gy))

    def save(self):
        if self.game_over:
            return
        towers_list = [[t.gx, t.gy, t.type_name] for t in self.towers]
        with open("td_seed_save.json", "w") as f:
            json.dump({
                "money": self.money,
                "wave": self.wave,
                "base_hp": self.base_hp,
                "max_base_hp": self.max_base_hp,
                "tower_level": self.tower_level,
                "world_seed": self.world_seed,
                "towers": towers_list,
            }, f)

    def update(self, dt):
        if self.upgrade_text_timer > 0:
            self.upgrade_text_timer -= dt

        self._spawn_enemies(dt)
        self._update_enemies(dt)
        self._update_towers(dt)
        self._update_projectiles(dt)
        self._check_wave_end()

    def _spawn_enemies(self, dt):
        if self.enemies_to_spawn <= 0:
            return
        self.spawn_timer += dt
        if self.spawn_timer >= cfg.SPAWN_INTERVAL:
            if self.path:
                self.enemies.append(Enemy(self.path, self.wave))
            self.enemies_to_spawn -= 1
            self.spawn_timer = 0

    def _update_enemies(self, dt):
        for enemy in self.enemies[:]:
            status = enemy.tick(dt)
            if status == "FINISHED":
                self.base_hp -= 1
                self.enemies.remove(enemy)
                if self.base_hp <= 0:
                    self.game_over = True
                    if os.path.exists("td_seed_save.json"):
                        os.remove("td_seed_save.json")
            elif status == "DEAD":
                self.money += enemy.reward
                self.enemies.remove(enemy)

    def _update_towers(self, dt):
        self.spatial_hash.clear()
        for enemy in self.enemies:
            self.spatial_hash.insert(enemy)
        for tower in self.towers:
            tower.update_and_shoot(self.projectiles, dt, self.obstacles, self.spatial_hash)

    def _update_projectiles(self, dt):
        for proj in self.projectiles[:]:
            proj.update(dt, self.enemies)
            if not proj.active:
                self.projectiles.remove(proj)

    def _check_wave_end(self):
        if self.enemies or self.enemies_to_spawn > 0:
            return

        if self.wave % cfg.UPGRADE_EVERY_N_WAVES == 0:
            self.tower_level += 1
            self.max_base_hp += cfg.UPGRADE_HP_BONUS
            self.base_hp = self.max_base_hp
            for tower in self.towers:
                tower.upgrade_stats(self.tower_level)
            self.upgrade_text = (
                f"10 ВОЛН ПРОЙДЕНО! Орудия Т-{self.tower_level}! База укреплена!"
            )
            self.upgrade_text_timer = cfg.UPGRADE_TEXT_DURATION

        self.wave += 1
        self.save()
        self.enemies_to_spawn = cfg.BASE_ENEMIES_PER_WAVE + self.wave * cfg.ENEMIES_PER_WAVE_SCALE

    def handle_click(self, pos):
        """Размещение башни с проверкой проходимости пути.

        Перед постройкой временно блокируем клетку и запускаем A*:
        если путь от входа до базы всё ещё существует — ставим башню,
        иначе отменяем (нельзя перекрыть единственный проход).
        """
        if self.game_over:
            return

        gx = pos[0] // cfg.GRID_SIZE
        gy = pos[1] // cfg.GRID_SIZE
        cell = (gx, gy)

        if not (0 <= gx < cfg.cols and 0 <= gy < cfg.rows):
            return
        if cell in self.blocked_cells or cell in self.path:
            return

        tower_class = TOWER_TYPES.get(self.selected_type)
        if not tower_class or self.money < tower_class.cost:
            return

        self.blocked_cells.add(cell)
        new_path = self.nav.find_path(self.start_node, self.end_node, self.blocked_cells)
        if new_path:
            self.path = new_path
            self.towers.append(create_tower(gx, gy, self.selected_type, self.tower_level))
            self.money -= tower_class.cost
            self.save()
        else:
            self.blocked_cells.remove(cell)

    def handle_right_click(self, pos):
        if self.game_over:
            return

        gx = pos[0] // cfg.GRID_SIZE
        gy = pos[1] // cfg.GRID_SIZE

        for tower in self.towers[:]:
            if tower.gx == gx and tower.gy == gy:
                self.money += int(tower.cost * cfg.SELL_REFUND)
                self.towers.remove(tower)
                self.blocked_cells.remove((gx, gy))
                self.path = self.nav.find_path(
                    self.start_node, self.end_node, self.blocked_cells
                )
                self.save()
                break

    def handle_resize(self):
        self.start_node = (0, cfg.rows // 2)
        self.end_node = (cfg.cols - 1, cfg.rows // 2)

        temp_seed = self.world_seed
        new_obs = set()
        attempts = 0
        while len(new_obs) == 0 and attempts < 5:
            new_obs = MapGenerator.generate_canyon(
                self.start_node, self.end_node, temp_seed
            )
            temp_seed += 1
            attempts += 1

        if new_obs:
            self.obstacles = new_obs
            self.blocked_cells = self.obstacles.copy()

        valid_towers = []
        for tower in self.towers:
            if 0 <= tower.gx < cfg.cols and 0 <= tower.gy < cfg.rows:
                valid_towers.append(tower)
                self.blocked_cells.add((tower.gx, tower.gy))
        self.towers = valid_towers

        self.path = self.nav.find_path(self.start_node, self.end_node, self.blocked_cells)
