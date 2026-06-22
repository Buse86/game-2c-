import math
import random
from src import config as cfg
from src.navigation import NavigationEngine


class MapGenerator:

    @staticmethod
    def generate_canyon(start, goal, world_seed):
        """Процедурная генерация каньона по сиду.

        Алгоритм:
        1. random.seed(world_seed) фиксирует генератор — один сид
           всегда даёт одну и ту же карту (нужно для сохранений).
        2. Генерируем случайные параметры синусоиды:
           freq   — частота изгибов (0.3–0.5)
           amp    — амплитуда отклонения от центра (2.5–4.5 клеток)
           offset — сдвиг фазы (0–100)
        3. Для каждого столбца x вычисляем центр каньона:
           center_y = середина + sin(x * freq + offset) * amp
           Синусоида создаёт плавные извилистые стены.
        4. Клетки, удалённые от center_y больше чем на 2–3 клетки,
           становятся стенами. random.choice([2, 3]) делает края
           неровными (каждый столбец — случайная ширина прохода).
        5. Проверяем BFS-ом, что путь от start до goal существует.
           Если нет — возвращаем пустой set (вызывающий код
           попробует другой сид).
        """
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
