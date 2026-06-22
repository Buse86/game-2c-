"""
Движок навигации — поиск пути на сетке.
Содержит два алгоритма:
- BFS (поиск в ширину) — для быстрой проверки, существует ли путь вообще
- A* (A-star) — для нахождения кратчайшего пути
"""

import heapq
from src import config as cfg


class NavigationEngine:
    """Класс для поиска путей на двумерной сетке с препятствиями."""

    def is_passable(self, start, goal, blocked):
        """Проверяет, можно ли дойти от start до goal (алгоритм BFS).

        BFS (Breadth-First Search, поиск в ширину) обходит сетку слоями:
        сначала все клетки на расстоянии 1, потом на расстоянии 2 и т.д.
        Не ищет кратчайший путь — только отвечает «да/нет».
        Используется для быстрой проверки проходимости при генерации карты.

        Аргументы:
            start   — начальная клетка (x, y) на сетке
            goal    — целевая клетка (x, y) на сетке
            blocked — множество (set) непроходимых клеток

        Возвращает True, если путь существует, иначе False.
        """
        queue = [start]      # очередь клеток для обхода
        visited = {start}    # множество уже посещённых клеток

        while queue:
            # Берём первую клетку из очереди (FIFO — первый пришёл, первый вышел)
            curr = queue.pop(0)

            # Если дошли до цели — путь есть
            if curr == goal:
                return True

            # Проверяем 4 соседних клетки (вверх, вниз, влево, вправо)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nxt = (curr[0] + dx, curr[1] + dy)

                # Проверяем, что сосед внутри сетки
                if 0 <= nxt[0] < cfg.cols and 0 <= nxt[1] < cfg.rows:
                    # Если не заблокирован и ещё не посещён — добавляем в очередь
                    if nxt not in blocked and nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)

        # Очередь пуста, а до цели не дошли — пути нет
        return False

    def find_path(self, start, goal, blocked):
        """Находит кратчайший путь от start до goal (алгоритм A*).

        A* — это улучшенный алгоритм Дейкстры, который использует эвристику
        (предсказание расстояния до цели) для ускорения поиска.

        Формула приоритета: f(n) = g(n) + h(n), где:
            g(n) — реальная стоимость пути от старта до клетки n
            h(n) — эвристика (манхэттенское расстояние до цели)
        Манхэттенское расстояние = |x1 - x2| + |y1 - y2|
        (подходит для сетки, где можно двигаться только по 4 направлениям)

        Аргументы:
            start   — начальная клетка (x, y)
            goal    — целевая клетка (x, y)
            blocked — множество непроходимых клеток

        Возвращает список клеток пути (без стартовой) или пустой список.
        """
        # Приоритетная очередь: (приоритет f, клетка)
        # heapq всегда достаёт элемент с наименьшим приоритетом
        open_set = []
        heapq.heappush(open_set, (0, start))

        came_from = {}        # для каждой клетки запоминаем, откуда пришли
        g_score = {start: 0}  # g(n) — стоимость пути от старта

        while open_set:
            # Достаём клетку с наименьшим f(n) — самую перспективную
            current = heapq.heappop(open_set)[1]

            # Если дошли до цели — восстанавливаем путь по цепочке came_from
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()  # путь был от конца к началу — разворачиваем
                return path

            # Перебираем 4 соседних клетки
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (current[0] + dx, current[1] + dy)

                # Проверяем: внутри сетки и не заблокирована
                if 0 <= neighbor[0] < cfg.cols and 0 <= neighbor[1] < cfg.rows and neighbor not in blocked:
                    # Стоимость пути через текущую клетку (каждый шаг = 1)
                    tentative_g = g_score[current] + 1

                    # Если нашли путь короче, чем уже известный — обновляем
                    if tentative_g < g_score.get(neighbor, float('inf')):
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g

                        # Вычисляем приоритет: f = g + h
                        # h = манхэттенское расстояние до цели
                        h = abs(neighbor[0] - goal[0]) + abs(neighbor[1] - goal[1])
                        f_score = tentative_g + h
                        heapq.heappush(open_set, (f_score, neighbor))

        # Очередь пуста — путь не найден
        return []
