from collections import deque
import random
from utils import ROWS, COLS, SPRITES, screen, TILE_SIZE, font


class MazeGenerator:
    def __init__(self, rows, cols, show_generations=False):
        self.rows = rows
        self.cols = cols
        self.show_generations = show_generations

    def draw_grid(self, grid, highlight=None, caption=None):
        # Helper to draw a given grid (for visualization)
        from utils import screen, SPRITES, TILE_SIZE, pygame, SCREEN_WIDTH, SCREEN_HEIGHT, BLACK
        screen.fill(BLACK)
        for row in range(ROWS):
            for col in range(COLS):
                if grid[row][col] == 1:
                    screen.blit(SPRITES["wall"],
                                (col * TILE_SIZE, row * TILE_SIZE))
        if highlight:
            for (x, y) in highlight:
                pygame.draw.rect(
                    screen, (255, 0, 0), (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE), 2)
        if caption:
            pygame.display.set_caption(caption)
        pygame.display.flip()

    def generate_maze(self):
        import pygame
        import time
        population = []
        for _ in range(30):
            population.append(self._random_candidate())
        for gen in range(100):
            scored = sorted(population, key=self._fitness, reverse=True)
            elite = scored[:10]
            # Visualize all candidates in this generation if enabled
            if self.show_generations:
                for idx, candidate in enumerate(scored):
                    self.draw_grid(candidate)
                    pygame.display.set_caption(
                        f"Generation {gen+1} - Candidate {idx+1}/30")
                    pygame.event.pump()
                    time.sleep(0.01)
            # Diversity injection: add 2 new random candidates each generation
            new_randoms = []
            for _ in range(2):
                new_randoms.append(self._random_candidate())
            population = elite[:] + new_randoms
            while len(population) < 30:
                a, b = random.sample(elite, 2)
                child = self._mutate(self._crossover(a, b), 0.03)
                population.append(child)
        best = max(population, key=self._fitness)
        for i in range(self.rows):
            best[i][0] = 1
            best[i][-1] = 1
        for j in range(self.cols):
            best[0][j] = 1
            best[-1][j] = 1
        best[1][1] = 0
        best[self.rows-2][1] = 0
        best[1][self.cols-2] = 0
        best[self.rows-2][self.cols-2] = 0
        return best

    def _fitness(self, grid):
        if not self._solvable(grid):
            return -1
        # Normalize wall_score and path_score
        total_cells = self.rows * self.cols
        wall_score = 1 - (sum(sum(row) for row in grid) / total_cells)
        max_path = self.rows + self.cols
        path_score = self._avg_path_length(grid) / max_path
        return wall_score * 0.9 + path_score * 0.1

    def _solvable(self, grid):
        total_open = sum(1 for row in grid for v in row if v == 0)
        visited = {(1, 1)}
        queue = deque([(1, 1)])
        while queue:
            x, y = queue.popleft()
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx = x + dx
                ny = y + dy
                if (
                    0 <= nx < self.cols
                    and 0 <= ny < self.rows
                    and grid[ny][nx] == 0
                    and (nx, ny) not in visited
                ):
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        return len(visited) == total_open

    def _avg_path_length(self, grid):
        def dist(dst):
            visited = set([(1, 1)])
            queue = deque([((1, 1), 0)])
            while queue:
                (x, y), d = queue.popleft()
                if (x, y) == dst:
                    return d
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nx = x + dx
                    ny = y + dy
                    if (
                        0 <= nx < self.cols
                        and 0 <= ny < self.rows
                        and grid[ny][nx] == 0
                        and (nx, ny) not in visited
                    ):
                        visited.add((nx, ny))
                        queue.append(((nx, ny), d + 1))
            return self.rows + self.cols
        corners = [
            (1, self.rows - 2),
            (self.cols - 2, 1),
            (self.cols - 2, self.rows - 2)
        ]
        return sum(dist(corner) for corner in corners) / len(corners)

    def _random_candidate(self):
        grid = []
        for i in range(self.rows):
            row = []
            for j in range(self.cols):
                if i == 0 or i == self.rows - 1 or j == 0 or j == self.cols - 1:
                    row.append(1)
                else:
                    row.append(1 if random.random() < 0.25 else 0)
            grid.append(row)
        return grid

    def _crossover(self, a, b):
        i1, i2 = sorted(random.sample(range(1, self.rows - 1), 2))
        child = [row[:] for row in a]
        for i in range(i1, i2):
            child[i] = b[i][:]
        return child

    def _mutate(self, grid, rate):
        for i in range(1, self.rows - 1):
            for j in range(1, self.cols - 1):
                if random.random() < rate:
                    grid[i][j] = 1 - grid[i][j]
        return grid


class Maze:
    def __init__(self, show_generations=False):
        self.generator = MazeGenerator(
            ROWS, COLS, show_generations=show_generations)
        self.grid = None
        self.pellets = []
        self.power_pellets = []
        self.generate_new_maze()

    def generate_new_maze(self):
        # Show loading message before generating maze
        from utils import screen, font, SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE
        import pygame
        import time
        screen.fill(BLACK)
        loading_text = font.render("Generating Maze...", True, WHITE)
        screen.blit(
            loading_text,
            (
                SCREEN_WIDTH // 2 - loading_text.get_width() // 2,
                SCREEN_HEIGHT // 2 - loading_text.get_height() // 2
            )
        )
        pygame.display.flip()
        self.grid = self.generator.generate_maze()
        pygame.display.set_caption("Pac-Man with AI")
        self.init_pellets()

    def init_pellets(self):
        self.pellets = []
        for y in range(ROWS):
            for x in range(COLS):
                if self.grid[y][x] == 0 and (x, y) != (1, 1):
                    self.pellets.append((x, y))
        # Remove unreachable pellets
        reachable = {(1, 1)}
        queue = deque([(1, 1)])
        while queue:
            x, y = queue.popleft()
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx = x + dx
                ny = y + dy
                if (
                    (nx, ny) not in reachable
                    and 0 <= nx < COLS
                    and 0 <= ny < ROWS
                    and self.grid[ny][nx] == 0
                ):
                    reachable.add((nx, ny))
                    queue.append((nx, ny))
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
        for x, y in self.pellets:
            screen.blit(SPRITES["pellet"], (x * TILE_SIZE, y * TILE_SIZE))
        for x, y in self.power_pellets:
            screen.blit(SPRITES["power_pellet"],
                        (x * TILE_SIZE, y * TILE_SIZE))
