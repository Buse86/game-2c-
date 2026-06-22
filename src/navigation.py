import heapq
from src import config as cfg


class NavigationEngine:

    def is_passable(self, start, goal, blocked):
        """Алгоритм BFS (поиск в ширину) — проверяет, есть ли путь.

        Обходит сетку «волнами» от стартовой клетки:
        сначала все соседи на расстоянии 1, потом 2, потом 3...
        Если волна дошла до goal — путь существует.

        Структура данных — очередь (FIFO):
        - queue.append() добавляет в конец
        - queue.pop(0) берёт из начала
        Это гарантирует обход по слоям, а не в глубину.

        visited — множество, чтобы не заходить в одну клетку дважды.
        """
        queue = [start]
        visited = {start}

        while queue:
            curr = queue.pop(0)
            if curr == goal:
                return True
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nxt = (curr[0] + dx, curr[1] + dy)
                if 0 <= nxt[0] < cfg.cols and 0 <= nxt[1] < cfg.rows:
                    if nxt not in blocked and nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)
        return False

    def find_path(self, start, goal, blocked):
        """Алгоритм A* — находит кратчайший путь на сетке.

        Улучшение алгоритма Дейкстры за счёт эвристики:
        вместо равномерного обхода приоритет отдаётся клеткам,
        которые ближе к цели.

        Приоритет клетки: f(n) = g(n) + h(n)
          g(n) — реальная длина пути от старта до клетки n
          h(n) — эвристика: оценка расстояния от n до цели.
                 Используем манхэттенское расстояние |x1-x2| + |y1-y2|
                 (точная метрика для сетки с 4 направлениями движения)

        Структуры данных:
          open_set  — приоритетная очередь (heapq), всегда достаёт
                      клетку с наименьшим f (самую перспективную)
          came_from — словарь «откуда пришли», для восстановления пути
          g_score   — словарь «кратчайшая известная стоимость от старта»

        Восстановление пути: от goal идём по цепочке came_from
        назад до start, потом разворачиваем список.
        """
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

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < cfg.cols and 0 <= neighbor[1] < cfg.rows and neighbor not in blocked:
                    tentative_g = g_score[current] + 1
                    if tentative_g < g_score.get(neighbor, float('inf')):
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        h = abs(neighbor[0] - goal[0]) + abs(neighbor[1] - goal[1])
                        f_score = tentative_g + h
                        heapq.heappush(open_set, (f_score, neighbor))

        return []
