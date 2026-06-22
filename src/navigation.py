import heapq
from src import config as cfg

class NavigationEngine:
    def is_passable(self, start, goal, blocked):
        queue = [start]
        visited = {start}
        while queue:
            curr = queue.pop(0)
            if curr == goal: return True
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                nxt = (curr[0] + dx, curr[1] + dy)
                if 0 <= nxt[0] < cfg.cols and 0 <= nxt[1] < cfg.rows:
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
                if 0 <= neighbor[0] < cfg.cols and 0 <= neighbor[1] < cfg.rows and neighbor not in blocked:
                    tentative_g = g_score[current] + 1
                    if tentative_g < g_score.get(neighbor, float('inf')):
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f_score = tentative_g + (abs(neighbor[0]-goal[0]) + abs(neighbor[1]-goal[1]))
                        heapq.heappush(open_set, (f_score, neighbor))
        return []