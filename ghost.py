from utils import SPRITES, TILE_SIZE, screen, CYAN, ROWS, COLS
import random
from collections import deque

GHOST_CONFIGS = [
    ("A*", "Blinky"),
    ("Dijkstra", "Inky"),
    ("BFS", "Pinky"),
    ("Greedy", "Clyde"),
]


class Ghost:
    def __init__(self, x, y, color, algorithm, name):
        self.x = x
        self.y = y
        self.color = color
        self.algorithm = algorithm
        self.name = name
        self.path = []
        self.start_x = x
        self.start_y = y
        self.is_scared = False
        self.scared_color = CYAN
        self.prev_pos = None
        self.just_respawned = False
        self.ate_during_power = False

    @staticmethod
    def create_ghosts(maze):
        # build reachable empty cells
        all_empty = [(x, y) for y in range(ROWS)
                     for x in range(COLS) if maze.grid[y][x] == 0]
        reachable = set()
        q = deque([(1, 1)])
        reachable.add((1, 1))
        while q:
            x, y = q.popleft()
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x+dx, y+dy
                if (nx, ny) in all_empty and (nx, ny) not in reachable:
                    reachable.add((nx, ny))
                    q.append((nx, ny))
        spawnable = []
        for x, y in reachable:
            if (x, y) == (1, 1):
                continue
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                neighbor = (x + dx, y + dy)
                if neighbor in reachable:
                    spawnable.append((x, y))
                    break
        colors = [(255, 0, 0), (0, 0, 255), (255, 192, 203), (255, 165, 0)]
        ghosts = []
        for i, (alg, name) in enumerate(GHOST_CONFIGS):
            x, y = random.choice(spawnable)
            ghosts.append(Ghost(x, y, colors[i], alg, name))
            ghosts[-1].start_x, ghosts[-1].start_y = x, y
        return ghosts

    def reset_position(self):
        self.x = self.start_x
        self.y = self.start_y
        self.path = []
        self.prev_pos = None
        self.is_scared = False
        self.just_respawned = True
        self.ate_during_power = True

    def update_scared_state(self, pacman):
        if self.just_respawned:
            self.is_scared = False
        elif pacman.powered_up and not self.ate_during_power:
            self.is_scared = True
        else:
            self.is_scared = False

    def handle_ai_move(self, pacman, maze, ghosts):
        if self.is_scared:
            self.simple_move_away(pacman.x, pacman.y, maze)
        else:
            target_x, target_y = pacman.x, pacman.y
            if self.algorithm == "A*":
                self.path = self.simple_target(target_x, target_y, maze)
            elif self.algorithm == "Dijkstra":
                self.path = self.simple_bfs(
                    (self.x, self.y), (target_x, target_y), maze, 10)
            elif self.algorithm == "BFS":
                self.path = self.simple_bfs(
                    (self.x, self.y), (target_x, target_y), maze, 5)
            elif self.algorithm == "Greedy":
                self.path = self.simple_greedy(target_x, target_y, maze)
            if not self.path:
                self.simple_random_move(maze)
            else:
                next_x, next_y = self.path.pop(0)
                if self.prev_pos and (next_x, next_y) == self.prev_pos and len(self.path) > 0:
                    alt = self.path.pop(0)
                    self.prev_pos = (self.x, self.y)
                    self.x, self.y = alt
                else:
                    self.prev_pos = (self.x, self.y)
                    self.x, self.y = next_x, next_y
        if self.just_respawned:
            self.just_respawned = False

    def check_pacman_caught(self, pacman):
        return self.x == pacman.x and self.y == pacman.y and (not self.is_scared or self.ate_during_power)

    def simple_move_away(self, player_x, player_y, maze):
        valid_moves = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS and maze.grid[ny][nx] == 0:
                dist = abs(nx - player_x) + abs(ny - player_y)
                if self.prev_pos and (nx, ny) == self.prev_pos:
                    continue
                valid_moves.append((dist, nx, ny))
        if not valid_moves:
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = self.x + dx, self.y + dy
                if 0 <= nx < COLS and 0 <= ny < ROWS and maze.grid[ny][nx] == 0:
                    dist = abs(nx - player_x) + abs(ny - player_y)
                    valid_moves.append((dist, nx, ny))
        if valid_moves:
            valid_moves.sort(reverse=True)
            _, next_x, next_y = valid_moves[0]
            self.prev_pos = (self.x, self.y)
            self.x, self.y = next_x, next_y

    def simple_random_move(self, maze):
        valid_moves = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS and maze.grid[ny][nx] == 0:
                if self.prev_pos and (nx, ny) == self.prev_pos:
                    continue
                valid_moves.append((nx, ny))
        if not valid_moves:
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = self.x + dx, self.y + dy
                if 0 <= nx < COLS and 0 <= ny < ROWS and maze.grid[ny][nx] == 0:
                    valid_moves.append((nx, ny))
        if valid_moves:
            next_x, next_y = random.choice(valid_moves)
            self.prev_pos = (self.x, self.y)
            self.x, self.y = next_x, next_y

    def simple_target(self, target_x, target_y, maze):
        valid_moves = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS and maze.grid[ny][nx] == 0:
                dist = abs(nx - target_x) + abs(ny - target_y)
                valid_moves.append((dist, nx, ny))
        path = []
        if valid_moves:
            valid_moves.sort()
            _, next_x, next_y = valid_moves[0]
            path.append((next_x, next_y))
        return path

    def simple_bfs(self, start, goal, maze, max_depth):
        queue = deque([(start, [])])
        visited = {start}
        depth = 0
        while queue and depth < max_depth:
            depth += 1
            position, path = queue.popleft()
            x, y = position
            if position == goal:
                return path
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                new_pos = (nx, ny)
                if (0 <= nx < COLS and 0 <= ny < ROWS and
                        maze.grid[ny][nx] == 0 and new_pos not in visited):
                    new_path = path + [new_pos]
                    queue.append((new_pos, new_path))
                    visited.add(new_pos)
        if queue:
            return queue[0][1]
        return []

    def simple_greedy(self, target_x, target_y, maze):
        return self.simple_target(target_x, target_y, maze)

    def draw(self):
        if self.is_scared and not self.just_respawned:
            img = SPRITES["scared"]
        else:
            img = SPRITES.get(self.name.lower(), SPRITES["blinky"])
        screen.blit(img, (self.x * TILE_SIZE, self.y * TILE_SIZE))
