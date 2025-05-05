import pygame
import random
import heapq
from collections import deque
import time

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


class MazeGenerator:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols

    def generate_maze(self):
        # Simplified maze generation - no genetic algorithm for better performance
        maze = [[1 for _ in range(self.cols)] for _ in range(self.rows)]

        # Make sure the border is walls
        for i in range(1, self.rows-1):
            for j in range(1, self.cols-1):
                # Create a simple maze with ~70% open spaces
                maze[i][j] = 1 if random.random() < 0.3 else 0

        # Ensure pathways to move around
        for i in range(2, self.rows-2, 2):
            for j in range(1, self.cols-1):
                maze[i][j] = 0

        for j in range(2, self.cols-2, 2):
            for i in range(1, self.rows-1):
                maze[i][j] = 0

        # Ensure Pacman start and corners are clear
        maze[1][1] = 0  # Pacman start
        maze[self.rows-2][1] = 0  # Bottom left
        maze[1][self.cols-2] = 0  # Top right
        maze[self.rows-2][self.cols-2] = 0  # Bottom right

        return maze


class Maze:
    def __init__(self):
        self.generator = MazeGenerator(ROWS, COLS)
        self.grid = None
        self.pellets = []
        self.power_pellets = []
        self.generate_new_maze()

    def generate_new_maze(self):
        # Loading message
        screen.fill(BLACK)
        loading_text = font.render("Generating Maze...", True, WHITE)
        screen.blit(loading_text, (SCREEN_WIDTH // 2 - loading_text.get_width() // 2,
                                   SCREEN_HEIGHT // 2 - loading_text.get_height() // 2))
        pygame.display.flip()

        # Generate the maze
        self.grid = self.generator.generate_maze()
        self.init_pellets()

    def init_pellets(self):
        # Add pellets to empty spaces
        self.pellets = []
        for y in range(ROWS):
            for x in range(COLS):
                # Don't place pellet at Pacman's start
                if self.grid[y][x] == 0 and (x, y) != (1, 1):
                    self.pellets.append((x, y))

        # Add power pellets at specific locations
        self.power_pellets = []
        power_positions = [(3, 3), (3, COLS-4), (ROWS-4, 3), (ROWS-4, COLS-4)]
        for x, y in power_positions:
            # Only add if position is open and valid
            if 0 <= x < COLS and 0 <= y < ROWS and self.grid[y][x] == 0:
                self.power_pellets.append((x, y))
                if (x, y) in self.pellets:
                    self.pellets.remove((x, y))

    def draw(self):
        for row in range(ROWS):
            for col in range(COLS):
                if self.grid[row][col] == 1:
                    pygame.draw.rect(screen, BLUE,
                                     (col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        # Draw pellets
        for x, y in self.pellets:
            pygame.draw.circle(screen, WHITE,
                               (x * TILE_SIZE + TILE_SIZE // 2,
                                y * TILE_SIZE + TILE_SIZE // 2),
                               TILE_SIZE // 10)

        # Draw power pellets (larger)
        for x, y in self.power_pellets:
            pygame.draw.circle(screen, WHITE,
                               (x * TILE_SIZE + TILE_SIZE // 2,
                                y * TILE_SIZE + TILE_SIZE // 2),
                               TILE_SIZE // 4)


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

            # Check if all pellets are collected
            if not maze.pellets and not maze.power_pellets:
                return "win"

            return "moved"
        return "blocked"

    def draw(self):
        pygame.draw.circle(screen, self.color,
                           (self.x * TILE_SIZE + TILE_SIZE // 2,
                            self.y * TILE_SIZE + TILE_SIZE // 2),
                           TILE_SIZE // 2 - 2)


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

    def reset_position(self):
        self.x = self.start_x
        self.y = self.start_y
        self.path = []

    def move(self, target_x, target_y, maze, pacman):
        # Don't move if at target
        if self.x == target_x and self.y == target_y:
            # Still check for collision if on Pac-Man
            if self.x == pacman.x and self.y == pacman.y:
                if pacman.powered_up:
                    self.reset_position()
                    pacman.score += 200
                    return "ghost_eaten"
                else:
                    return "pacman_caught"
            return

        # Use simplified movement if scared to improve performance
        if self.is_scared:
            self.simple_move_away(pacman.x, pacman.y, maze)
            # Check for collision after move
            if self.x == pacman.x and self.y == pacman.y:
                if pacman.powered_up:
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
            # Check for collision after move
            if self.x == pacman.x and self.y == pacman.y:
                if pacman.powered_up:
                    self.reset_position()
                    pacman.score += 200
                    return "ghost_eaten"
                else:
                    return "pacman_caught"
            return

        # Move along path
        if self.path:
            next_x, next_y = self.path.pop(0)
            self.x, self.y = next_x, next_y

            # Check for collision with pacman
            if self.x == pacman.x and self.y == pacman.y:
                if pacman.powered_up:
                    self.reset_position()
                    pacman.score += 200
                    return "ghost_eaten"
                else:
                    return "pacman_caught"

        return None

    def simple_move_away(self, player_x, player_y, maze):
        """Simple method to move away from player when scared"""
        # Find valid directions
        valid_moves = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS and maze.grid[ny][nx] == 0:
                # Calculate distance from player for this move
                dist = abs(nx - player_x) + abs(ny - player_y)
                valid_moves.append((dist, nx, ny))

        # Choose direction that maximizes distance from player
        if valid_moves:
            valid_moves.sort(reverse=True)  # Sort by descending distance
            # Choose move with largest distance
            _, next_x, next_y = valid_moves[0]
            self.x, self.y = next_x, next_y

        return None

    def simple_random_move(self, maze):
        """Make a random valid move"""
        valid_moves = []
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS and maze.grid[ny][nx] == 0:
                valid_moves.append((nx, ny))

        if valid_moves:
            next_x, next_y = random.choice(valid_moves)
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
        color = self.scared_color if self.is_scared else self.color
        pygame.draw.circle(screen, color,
                           (self.x * TILE_SIZE + TILE_SIZE // 2,
                            self.y * TILE_SIZE + TILE_SIZE // 2),
                           TILE_SIZE // 2 - 2)


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

        # Create ghosts after maze generation to prevent crashes
        ghosts = [
            Ghost(COLS - 2, 1, RED, "A*", "Blinky"),
            Ghost(1, ROWS - 2, BLUE, "Dijkstra", "Inky"),
            Ghost(COLS - 2, ROWS - 2, PINK, "BFS", "Pinky"),
            Ghost(COLS // 2, ROWS // 2, ORANGE, "Greedy", "Clyde")
        ]

        # Game loop
        running = True
        game_state = "playing"
        power_duration = 10  # seconds
        last_time = time.time()
        frame_count = 0

        # Make sure ghosts don't start on walls
        for ghost in ghosts:
            if maze.grid[ghost.y][ghost.x] == 1:
                # Find a nearby empty cell
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        ny, nx = ghost.y + dy, ghost.x + dx
                        if (0 <= nx < COLS and 0 <= ny < ROWS and
                                maze.grid[ny][nx] == 0):
                            ghost.x, ghost.y = nx, ny
                            ghost.start_x, ghost.start_y = nx, ny
                            break
                    else:
                        continue
                    break

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
                    if move_result == "win":
                        game_state = "won"

                # Check power-up expiration
                if pacman.powered_up and time.time() - pacman.power_time > power_duration:
                    pacman.powered_up = False
                    for ghost in ghosts:
                        ghost.is_scared = False

                # Update ghost states
                for ghost in ghosts:
                    ghost.is_scared = pacman.powered_up

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

                            if ghost_move_result == "pacman_caught" and not pacman.powered_up:
                                pacman.lives -= 1
                                if pacman.lives <= 0:
                                    game_state = "game_over"
                                else:
                                    # Reset positions and states
                                    pacman.x, pacman.y = 1, 1
                                    pacman.powered_up = False
                                    for g in ghosts:
                                        g.reset_position()
                                        g.is_scared = False
                                    # Short pause to show loss of life
                                    pygame.display.flip()
                                    pygame.time.delay(1000)
                                    break  # Stop moving ghosts this frame
                        except Exception as e:
                            print(f"Error moving ghost: {e}")
                            # Fall back to random movement
                            ghost.simple_random_move(maze)
                            # Check for collision after fallback move
                            if ghost.x == pacman.x and ghost.y == pacman.y:
                                if pacman.powered_up:
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
                                            g.reset_position()
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
