import math
import random
from src import config as cfg
from src.navigation import NavigationEngine  # Изменен импорт

class MapGenerator:
    @staticmethod
    def generate_canyon(start, goal, world_seed):
        blocked = set()
        random.seed(world_seed)
        
        freq = random.uniform(0.3, 0.5)
        amp = random.uniform(2.5, 4.5)
        offset = random.randint(0, 100)

        for x in range(cfg.cols):
            center_y = int(cfg.rows / 2 + math.sin(x * freq + offset) * amp)
            center_y = max(2, min(cfg.rows - 3, center_y))
            
            for y in range(cfg.rows):
                if abs(y - center_y) > random.choice([2, 3]):
                    if (x, y) != start and (x, y) != goal:
                        blocked.add((x, y))
                        
        nav = NavigationEngine()
        if not nav.is_passable(start, goal, blocked):
            return set() 
        return blocked