from src import config as cfg


class SpatialHash:
    """Пространственное хеширование — ускорение поиска объектов по координатам.

    Проблема: каждая башня перебирает ВСЕХ врагов, чтобы найти тех,
    кто в радиусе. При 100 врагах и 20 башнях — 2000 проверок за кадр.

    Решение: делим игровое поле на крупные ячейки (cell_size × cell_size).
    Каждый враг попадает в одну ячейку по своим координатам.
    Когда башня ищет цель, проверяем только врагов из ближайших ячеек,
    а не из всего списка.

    Алгоритм:
    1. clear() — очищаем хеш-таблицу в начале каждого кадра
    2. insert(obj) — для каждого врага вычисляем ключ ячейки:
       key = (int(x // cell_size), int(y // cell_size))
       и добавляем врага в список этой ячейки
    3. query_radius(x, y, radius) — находим все ячейки, которые
       пересекает квадрат [x-radius, x+radius] × [y-radius, y+radius],
       и возвращаем всех врагов из этих ячеек

    Сложность поиска падает с O(N) до O(K), где K — число врагов
    в нескольких ячейках рядом с башней (обычно намного меньше N).
    """

    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.buckets = {}

    def clear(self):
        self.buckets.clear()

    def insert(self, obj):
        key = (int(obj.x // self.cell_size), int(obj.y // self.cell_size))
        if key not in self.buckets:
            self.buckets[key] = []
        self.buckets[key].append(obj)

    def query_radius(self, x, y, radius):
        min_cx = int((x - radius) // self.cell_size)
        max_cx = int((x + radius) // self.cell_size)
        min_cy = int((y - radius) // self.cell_size)
        max_cy = int((y + radius) // self.cell_size)

        result = []
        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                bucket = self.buckets.get((cx, cy))
                if bucket:
                    result.extend(bucket)
        return result
