import pygame
import random
import heapq
from collections import deque
import time
import os

pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 720, 720
TILE_SIZE = 30
ROWS, COLS = SCREEN_HEIGHT // TILE_SIZE, SCREEN_WIDTH // TILE_SIZE
FPS = 10

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
PINK = (255, 192, 203)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pac-Man with AI")
clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 25)

# Load and scale images


def load_and_scale(path):
    img = pygame.image.load(path).convert_alpha()
    return pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))


# Sprites dictionary with correct paths
SPRITES = {
    "pacman": load_and_scale(os.path.join("pacman-art", "pacman-right", "1.png")),
    "blinky": load_and_scale(os.path.join("pacman-art", "ghosts", "blinky.png")),
    "inky": load_and_scale(os.path.join("pacman-art", "ghosts", "inky.png")),
    "pinky": load_and_scale(os.path.join("pacman-art", "ghosts", "pinky.png")),
    "clyde": load_and_scale(os.path.join("pacman-art", "ghosts", "clyde.png")),
    "scared": load_and_scale(os.path.join("pacman-art", "ghosts", "blue_ghost.png")),
    "pellet": load_and_scale(os.path.join("pacman-art", "other", "dot.png")),
    "power_pellet": load_and_scale(os.path.join("pacman-art", "other", "powerup.png")),
    "wall": load_and_scale(os.path.join("pacman-art", "other", "wall.png")),
}


class MazeGenerator:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols

    def generate_maze(self):
        # Genetic-Algorithm based maze generation ensuring solvability & balance
        population = [self._random_candidate() for _ in range(30)]
        for _ in range(100):
            # rank by fitness
            scored = sorted(population, key=self._fitness, reverse=True)
            elite = scored[:10]
            # breed next gen
            population = elite[:]
            while len(population) < 30:
                a, b = random.sample(elite, 2)
                child = self._mutate(self._crossover(a, b), 0.03)
                population.append(child)
        best = max(population, key=self._fitness)
        # enforce border walls and clear Pac-Man start & corners
        for i in range(self.rows):
            best[i][0] = best[i][-1] = 1
        for j in range(self.cols):
            best[0][j] = best[-1][j] = 1
        best[1][1] = best[self.rows-2][1] = best[1][self.cols -
                                                    2] = best[self.rows-2][self.cols-2] = 0
        return best

    def _fitness(self, grid):
        if not self._solvable(grid):  # now checks full connectivity
            return -1
        wall_score = sum(sum(row) for row in grid)
        path_score = self._avg_path_length(grid)
        # combine: favor dense walls and moderate path length
        return wall_score + path_score * 0.5

    def _solvable(self, grid):
        # ensure every empty cell is reachable from (1,1)
        tot = sum(1 for row in grid for v in row if v == 0)
        vis = {(1, 1)}
        q = deque([(1, 1)])
        while q:
            x, y = q.popleft()
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows and grid[ny][nx] == 0 and (nx, ny) not in vis:
                    vis.add((nx, ny))
                    q.append((nx, ny))
        return len(vis) == tot

    def _avg_path_length(self, grid):
        from collections import deque

        def dist(dst):
            visited = set([(1, 1)])
            queue = deque([((1, 1), 0)])
            while queue:
                (x, y), d = queue.popleft()
                if (x, y) == dst:
                    return d
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < self.cols and 0 <= ny < self.rows and grid[ny][nx] == 0 and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append(((nx, ny), d+1))
            return self.rows + self.cols
        corners = [(1, self.rows-2), (self.cols-2, 1),
                   (self.cols-2, self.rows-2)]
        return sum(dist(c) for c in corners) / len(corners)

    def _random_candidate(self):
        grid = [[1]*self.cols for _ in range(self.rows)]
        for i in range(1, self.rows-1):
            for j in range(1, self.cols-1):
                grid[i][j] = 1 if random.random() < 0.4 else 0
        return grid

    def _crossover(self, a, b):
        mid = self.rows // 2
        child = [row[:] for row in a]
        for i in range(mid, self.rows):
            child[i] = b[i][:]
        return child

    def _mutate(self, grid, rate):
        for i in range(1, self.rows-1):
            for j in range(1, self.cols-1):
                if random.random() < rate:
                    grid[i][j] = 1 - grid[i][j]
        return grid


class Maze:
    def __init__(self):
        self.generator = MazeGenerator(ROWS, COLS)
        self.grid = None
        self.pellets = []
        self.power_pellets = []
        self.generate_new_maze()

    def generate_new_maze(self):
        # Loading message...
        screen.fill(BLACK)
        loading_text = font.render("Generating Maze...", True, WHITE)
        screen.blit(loading_text, (SCREEN_WIDTH//2 - loading_text.get_width()//2,
                                   SCREEN_HEIGHT//2 - loading_text.get_height()//2))
        pygame.display.flip()

        # retry until reachable area covers ≥50%
        total = ROWS * COLS
        while True:
            self.grid = self.generator.generate_maze()
            # compute reachable empty cells
            vis = {(1, 1)}
            q = deque([(1, 1)])
            while q:
                x, y = q.popleft()
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nx, ny = x+dx, y+dy
                    if (nx, ny) not in vis and 0 <= nx < COLS and 0 <= ny < ROWS and self.grid[ny][nx] == 0:
                        vis.add((nx, ny))
                        q.append((nx, ny))
            if len(vis) >= total//2:
                break
        self.init_pellets()

    def init_pellets(self):
        # Add pellets to empty spaces
        self.pellets = []
        for y in range(ROWS):
            for x in range(COLS):
                # Don't place pellet at Pacman's start
                if self.grid[y][x] == 0 and (x, y) != (1, 1):
                    self.pellets.append((x, y))

        # Remove unreachable pellets
        reachable = {(1, 1)}
        q = deque([(1, 1)])
        while q:
            x, y = q.popleft()
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x+dx, y+dy
                if (nx, ny) not in reachable and 0 <= nx < COLS and 0 <= ny < ROWS and self.grid[ny][nx] == 0:
                    reachable.add((nx, ny))
                    q.append((nx, ny))
        self.pellets = [p for p in self.pellets if p in reachable]

        # random power-pellets from reachable cells
        power_candidates = [p for p in reachable if p != (1, 1)]
        count = min(4, len(power_candidates))
        self.power_pellets = random.sample(power_candidates, count)
        for p in self.power_pellets:
            if p in self.pellets:
                self.pellets.remove(p)

    def draw(self):
        for row in range(ROWS):
            for col in range(COLS):
                if self.grid[row][col] == 1:
                    screen.blit(SPRITES["wall"],
                                (col * TILE_SIZE, row * TILE_SIZE))
        # Draw pellets
        for x, y in self.pellets:
            screen.blit(SPRITES["pellet"], (x * TILE_SIZE, y * TILE_SIZE))
        # Draw power pellets
        for x, y in self.power_pellets:
            screen.blit(SPRITES["power_pellet"],
                        (x * TILE_SIZE, y * TILE_SIZE))


class PacMan:
    def __init__(self):
        self.x = 1
        self.y = 1
        self.color = YELLOW
        self.score = 0
        self.powered_up = False
        self.power_time = 0
        self.lives = 3

    def move(self, dx, dy, maze):
        new_x, new_y = self.x + dx, self.y + dy
        if 0 <= new_x < COLS and 0 <= new_y < ROWS and maze.grid[new_y][new_x] == 0:
            self.x, self.y = new_x, new_y

            # Check for pellet collection
            if (self.x, self.y) in maze.pellets:
                maze.pellets.remove((self.x, self.y))
                self.score += 10

            # Check for power pellet collection
            if (self.x, self.y) in maze.power_pellets:
                maze.power_pellets.remove((self.x, self.y))
                self.powered_up = True
                self.power_time = time.time()
                self.score += 50
                return "power"

            # Check if all pellets are collected
            if not maze.pellets and not maze.power_pellets:
                return "win"

            return "moved"
        return "blocked"

    def draw(self):
        screen.blit(SPRITES["pacman"], (self.x *
                    TILE_SIZE, self.y * TILE_SIZE))


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
        self.prev_pos = None  # Track previous position to avoid immediate backtracking
        self.just_respawned = False  # Add this line
        self.ate_during_power = False  # Track if eaten during current power-up

    def reset_position(self):
        self.x = self.start_x
        self.y = self.start_y
        self.path = []
        self.prev_pos = None
        self.is_scared = False  # Always reset scared state when eaten
        self.just_respawned = True  # Mark as just respawned
        self.ate_during_power = True  # Mark as eaten during this power-up

    def move(self, target_x, target_y, maze, pacman):
        # always check collision immediately
        if self.x == pacman.x and self.y == pacman.y:
            if self.is_scared:
                self.reset_position()
                pacman.score += 200
                return "ghost_eaten"
            else:
                return "pacman_caught"

        # Don't move if at target
        if self.x == target_x and self.y == target_y:
            # Always check for collision
            if self.x == pacman.x and self.y == pacman.y:
                if self.is_scared:
                    self.reset_position()
                    pacman.score += 200
                    return "ghost_eaten"
                else:
                    return "pacman_caught"
            return

        # Use simplified movement if scared to improve performance
        if self.is_scared:
            result = self.simple_move_away(pacman.x, pacman.y, maze)
            # Always check for collision after moving
            if self.x == pacman.x and self.y == pacman.y:
                if self.is_scared:
                    self.reset_position()
                    pacman.score += 200
                    return "ghost_eaten"
                else:
                    return "pacman_caught"
            return

        # Always update path toward target (not just when empty)
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

        # If no path, move randomly
        if not self.path:
            self.simple_random_move(maze)
            # Always check for collision after moving
            if self.x == pacman.x and self.y == pacman.y:
                if self.is_scared:
                    self.reset_position()
                    pacman.score += 200
                    return "ghost_eaten"
                else:
                    return "pacman_caught"
            return

        # Move along path
        if self.path:
            next_x, next_y = self.path.pop(0)
            # Avoid immediate backtracking unless stuck
            if self.prev_pos and (next_x, next_y) == self.prev_pos and len(self.path) > 0:
                # Try next step in path if available
                alt = self.path.pop(0)
                self.prev_pos = (self.x, self.y)
                self.x, self.y = alt
            else:
                self.prev_pos = (self.x, self.y)
                self.x, self.y = next_x, next_y

            # Always check for collision after moving
            if self.x == pacman.x and self.y == pacman.y:
                if self.is_scared:
                    self.reset_position()
                    pacman.score += 200
                    return "ghost_eaten"
                else:
                    return "pacman_caught"

        # At the end of any move, if just_respawned, clear the flag after first move
        if self.just_respawned:
            self.just_respawned = False

        return None

    def simple_move_away(self, player_x, player_y, maze):
        """Simple method to move away from player when scared"""
        valid_moves = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS and maze.grid[ny][nx] == 0:
                dist = abs(nx - player_x) + abs(ny - player_y)
                # Avoid immediate backtracking if possible
                if self.prev_pos and (nx, ny) == self.prev_pos:
                    continue
                valid_moves.append((dist, nx, ny))
        # If all moves are backtracking, allow it
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

            # Check if moved into Pacman (for consistent ghost eating)
            if self.x == player_x and self.y == player_y:
                return "ghost_eaten"

        return None

    def simple_random_move(self, maze):
        """Make a random valid move"""
        valid_moves = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS and maze.grid[ny][nx] == 0:
                # Avoid immediate backtracking if possible
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
        return None

    def simple_target(self, target_x, target_y, maze):
        """Simple method to move toward target"""
        valid_moves = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS and maze.grid[ny][nx] == 0:
                # Calculate Manhattan distance to target
                dist = abs(nx - target_x) + abs(ny - target_y)
                valid_moves.append((dist, nx, ny))

        # Sort by distance (ascending)
        path = []
        if valid_moves:
            valid_moves.sort()  # Sort by distance (smallest first)
            _, next_x, next_y = valid_moves[0]  # Choose move closest to target
            path.append((next_x, next_y))

        return path

    def simple_bfs(self, start, goal, maze, max_depth):
        """Very simplified BFS with depth limit"""
        queue = deque([(start, [])])  # (position, path)
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

        # Return partial path if found
        if queue:
            return queue[0][1]  # Return the path from the first item in queue
        return []

    def simple_greedy(self, target_x, target_y, maze):
        """Simplified greedy best-first search"""
        # Just return the direction that gets us closest to target
        return self.simple_target(target_x, target_y, maze)

    def heuristic(self, a, b):
        """Manhattan distance heuristic"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def draw(self):
        # Optionally: never show scared sprite for just-respawned ghosts
        if self.is_scared and not self.just_respawned:
            img = SPRITES["scared"]
        else:
            if self.name == "Blinky":
                img = SPRITES["blinky"]
            elif self.name == "Inky":
                img = SPRITES["inky"]
            elif self.name == "Pinky":
                img = SPRITES["pinky"]
            elif self.name == "Clyde":
                img = SPRITES["clyde"]
            else:
                img = SPRITES["blinky"]
        screen.blit(img, (self.x * TILE_SIZE, self.y * TILE_SIZE))


def game_over_screen(score, won=False):
    screen.fill(BLACK)

    if won:
        message = f"You Won! Score: {score}"
        color = YELLOW
    else:
        message = f"Game Over! Score: {score}"
        color = RED

    text = font.render(message, True, color)
    restart_text = font.render("Press R to Restart", True, WHITE)
    quit_text = font.render("Press Q to Quit", True, WHITE)

    screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() //
                2, SCREEN_HEIGHT // 2 - 50))
    screen.blit(restart_text, (SCREEN_WIDTH // 2 -
                restart_text.get_width() // 2, SCREEN_HEIGHT // 2))
    screen.blit(quit_text, (SCREEN_WIDTH // 2 -
                quit_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))

    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return "restart"
                elif event.key == pygame.K_q:
                    return "quit"
    return "quit"


def main_game():
    try:
        # Initialize game objects
        maze = Maze()
        pacman = PacMan()

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

        # spawn ghosts at random reachable cells with at least one exit
        ghosts = [Ghost(0, 0, c, alg, n) for c, alg, n in [
            (RED, "A*", "Blinky"), (BLUE, "Dijkstra", "Inky"),
            (PINK, "BFS", "Pinky"), (ORANGE, "Greedy", "Clyde")
        ]]
        spawnable = [(x, y) for x, y in reachable if (x, y) != (1, 1) and
                     any((x+dx, y+dy) in reachable for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)])]
        for g in ghosts:
            g.x, g.y = random.choice(spawnable)
            g.start_x, g.start_y = g.x, g.y

        # Game loop
        running = True
        game_state = "playing"
        power_duration = 10  # seconds
        last_time = time.time()
        frame_count = 0

        while running:
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                # Add escape key to quit
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            if game_state == "playing":
                # Player movement
                keys = pygame.key.get_pressed()
                dx, dy = 0, 0
                if keys[pygame.K_UP]:
                    dy = -1
                elif keys[pygame.K_DOWN]:
                    dy = 1
                elif keys[pygame.K_LEFT]:
                    dx = -1
                elif keys[pygame.K_RIGHT]:
                    dx = 1

                # Move pacman
                if dx != 0 or dy != 0:
                    move_result = pacman.move(dx, dy, maze)
                    # --- immediate collision check after Pac-Man moved ---
                    for ghost in ghosts:
                        if ghost.x == pacman.x and ghost.y == pacman.y:
                            # only eat if it's actually frightened and wasn't just eaten/respawned
                            if ghost.is_scared and not ghost.ate_during_power:
                                ghost.reset_position()
                                pacman.score += 200
                            else:
                                # Pac-Man gets caught by any normal or just-respawned ghost
                                pacman.lives -= 1
                                if pacman.lives <= 0:
                                    game_state = "game_over"
                                else:
                                    # reset positions & states
                                    pacman.x, pacman.y = 1, 1
                                    pacman.powered_up = False
                                    for g in ghosts:
                                        g.x, g.y = g.start_x, g.start_y
                                        g.prev_pos = None
                                        g.just_respawned = False
                                        g.ate_during_power = False
                                        g.is_scared = False
                                    pygame.display.flip()
                                    pygame.time.delay(1000)
                            break
                    # --- end immediate collision check ---
                    if move_result == "win":
                        game_state = "won"
                    elif move_result == "power":
                        # new power-up → allow all ghosts to be scared again
                        for g in ghosts:
                            g.ate_during_power = False
                            g.just_respawned = False

                # Check power-up expiration
                if pacman.powered_up and time.time() - pacman.power_time > power_duration:
                    pacman.powered_up = False
                    for ghost in ghosts:
                        ghost.is_scared = False
                        ghost.ate_during_power = False  # Allow to be scared by next power-up

                # Update ghost states
                for ghost in ghosts:
                    if ghost.just_respawned:
                        ghost.is_scared = False
                    elif pacman.powered_up and not ghost.ate_during_power:
                        ghost.is_scared = True
                    else:
                        ghost.is_scared = False

                # Move ghosts - slow them down
                frame_count += 1
                if frame_count % 3 == 0:  # Even slower ghost movement
                    for i, ghost in enumerate(ghosts):
                        # Move all ghosts every ghost frame (not just one per frame)
                        # Set target based on whether ghost is scared
                        if ghost.is_scared:
                            # Choose random corner to flee to
                            corners = [(1, 1), (1, ROWS-2),
                                       (COLS-2, 1), (COLS-2, ROWS-2)]
                            target = random.choice(corners)
                            target_x, target_y = target
                        else:
                            target_x, target_y = pacman.x, pacman.y

                        # Move ghost
                        try:
                            ghost_move_result = ghost.move(
                                target_x, target_y, maze, pacman)

                            if ghost_move_result == "pacman_caught" and (
                                not pacman.powered_up or ghost.ate_during_power
                            ):
                                pacman.lives -= 1
                                if pacman.lives <= 0:
                                    game_state = "game_over"
                                else:
                                    # Reset positions and states
                                    pacman.x, pacman.y = 1, 1
                                    pacman.powered_up = False
                                    for g in ghosts:
                                        g.x, g.y = g.start_x, g.start_y
                                        g.prev_pos = None
                                        g.just_respawned = False
                                        g.ate_during_power = False
                                        g.is_scared = False
                                    # Short pause to show loss of life
                                    pygame.display.flip()
                                    pygame.time.delay(1000)
                                    break  # Stop moving ghosts this frame
                            elif ghost_move_result == "ghost_eaten":
                                # Reset ghost's scared state after being eaten
                                ghost.is_scared = False
                        except Exception as e:
                            print(f"Error moving ghost: {e}")
                            # Fall back to random movement
                            ghost.simple_random_move(maze)
                            # Check for collision after fallback move
                            if ghost.x == pacman.x and ghost.y == pacman.y:
                                # only treat as eaten if still scared and eligible
                                if pacman.powered_up and not ghost.ate_during_power:
                                    ghost.reset_position()
                                    pacman.score += 200
                                else:
                                    pacman.lives -= 1
                                    if pacman.lives <= 0:
                                        game_state = "game_over"
                                    else:
                                        pacman.x, pacman.y = 1, 1
                                        pacman.powered_up = False
                                        for g in ghosts:
                                            g.x, g.y = g.start_x, g.start_y
                                            g.prev_pos = None
                                            g.just_respawned = False
                                            g.ate_during_power = False
                                            g.is_scared = False
                                        pygame.display.flip()
                                        pygame.time.delay(1000)
                                        break

                # Render game
                screen.fill(BLACK)
                maze.draw()
                pacman.draw()
                for ghost in ghosts:
                    ghost.draw()

                # Display score, lives and power-up info
                score_text = font.render(f"Score: {pacman.score}", True, WHITE)
                lives_text = font.render(f"Lives: {pacman.lives}", True, WHITE)
                screen.blit(score_text, (10, 10))
                screen.blit(lives_text, (SCREEN_WIDTH -
                            lives_text.get_width() - 10, 10))

                if pacman.powered_up:
                    time_left = power_duration - \
                        (time.time() - pacman.power_time)
                    power_text = font.render(
                        f"Power: {int(time_left)}s", True, CYAN)
                    screen.blit(power_text, (SCREEN_WIDTH // 2 -
                                power_text.get_width() // 2, 10))

            elif game_state == "game_over" or game_state == "won":
                result = game_over_screen(pacman.score, game_state == "won")
                if result == "restart":
                    return True  # Restart the game
                else:
                    running = False

            pygame.display.flip()
            clock.tick(FPS)

    except Exception as e:
        # Show error on screen
        screen.fill(BLACK)
        error_text = font.render(f"Error: {str(e)}", True, RED)
        retry_text = font.render(
            "Press R to restart or Q to quit", True, WHITE)
        screen.blit(error_text, (SCREEN_WIDTH // 2 -
                    error_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(retry_text, (SCREEN_WIDTH // 2 -
                    retry_text.get_width() // 2, SCREEN_HEIGHT // 2 + 20))
        pygame.display.flip()

        # Wait for user input
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        return True  # Restart
                    elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                        return False  # Quit

    return False  # Don't restart


# Main game loop
restart = True
while restart:
    restart = main_game()

pygame.quit()
