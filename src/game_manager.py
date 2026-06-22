import json
import os
import random
from src import config as cfg
from src.navigation import NavigationEngine  # Изменен импорт
from src.map_generator import MapGenerator  # Изменен импорт
from src.entities import Tower, Enemy  # Изменен импорт

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
        
        self.start_node = (0, cfg.rows // 2)
        self.end_node = (cfg.cols - 1, cfg.rows // 2)
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
        
        if not (0 <= gx < cfg.cols and 0 <= gy < cfg.rows) or cell in self.blocked_cells: return
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
        if self.game_over: return
        gx, gy = pos[0]//cfg.GRID_SIZE, pos[1]//cfg.GRID_SIZE
        cell = (gx, gy)
        
        for t in self.towers[:]:
            if t.gx == gx and t.gy == gy:
                cost = 50 if t.type == "LMG" else 125
                self.money += int(cost * 0.8)
                self.towers.remove(t)
                self.blocked_cells.remove(cell)
                self.path = self.nav.find_path(self.start_node, self.end_node, self.blocked_cells)
                self.save()
                break

    def handle_resize(self):
        self.start_node = (0, cfg.rows // 2)
        self.end_node = (cfg.cols - 1, cfg.rows // 2)
        
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
            if 0 <= t.gx < cfg.cols and 0 <= t.gy < cfg.rows:
                valid_towers.append(t)
                self.blocked_cells.add((t.gx, t.gy))
        self.towers = valid_towers
        
        self.path = self.nav.find_path(self.start_node, self.end_node, self.blocked_cells)