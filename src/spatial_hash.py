class SpatialGrid:
    """Второй сложный алгоритм: Пространственное хеширование для оптимизации поиска целей."""
    def __init__(self, cell_size=80):
        self.cell_size = cell_size
        self.grid = {}

    def clear(self):
        self.grid.clear()

    def _get_cell_coords(self, x, y):
        return int(x // self.cell_size), int(y // self.cell_size)

    def insert(self, entity):
        cx, cy = self._get_cell_coords(entity.x, entity.y)
        key = (cx, cy)
        if key not in self.grid:
            self.grid[key] = []
        self.grid[key].append(entity)

    def get_nearby_enemies(self, x, y, search_radius):
        """Возвращает только тех врагов, которые находятся в радиусе досягаемости секторов."""
        start_cx, start_cy = self._get_cell_coords(x - search_radius, y - search_radius)
        end_cx, end_cy = self._get_cell_coords(x + search_radius, y + search_radius)
        
        nearby_enemies = []
        for cx in range(start_cx, end_cx + 1):
            for cy in range(start_cy, end_cy + 1):
                if (cx, cy) in self.grid:
                    nearby_enemies.extend(self.grid[(cx, cy)])
        return nearby_enemies