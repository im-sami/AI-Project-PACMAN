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
        population = [self._random_candidate() for _ in range(30)]
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
            new_randoms = [self._random_candidate() for _ in range(2)]
            population = elite[:] + new_randoms
            while len(population) < 30:
                a, b = random.sample(elite, 2)
                child = self._mutate(self._crossover(a, b), 0.03)
                population.append(child)
        best = max(population, key=self._fitness)
        for i in range(self.rows):
            best[i][0] = best[i][-1] = 1
        for j in range(self.cols):
            best[0][j] = best[-1][j] = 1
        best[1][1] = best[self.rows-2][1] = best[1][self.cols -
                                                    2] = best[self.rows-2][self.cols-2] = 0
        return best

    def _fitness(self, grid):
        if not self._solvable(grid):
            return -1
        # Normalize wall_score and path_score
        total_cells = self.rows * self.cols
        wall_score = 1 - (sum(sum(row) for row in grid) /
                          total_cells)  # 0..1, higher is more path
        max_path = self.rows + self.cols  # rough upper bound for normalization
        path_score = self._avg_path_length(grid) / max_path  # 0..~1
        # Strongly reward openness (more paths, less wall)
        return wall_score * 0.9 + path_score * 0.1

    def _solvable(self, grid):
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
                # Lower wall probability for more open mazes
                grid[i][j] = 1 if random.random() < 0.25 else 0
        return grid

    def _crossover(self, a, b):
        # Two-point crossover: pick two random row indices
        i1, i2 = sorted(random.sample(range(1, self.rows-1), 2))
        child = [row[:] for row in a]
        for i in range(i1, i2):
            child[i] = b[i][:]
        return child

    def _mutate(self, grid, rate):
        for i in range(1, self.rows-1):
            for j in range(1, self.cols-1):
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
        screen.blit(loading_text, (SCREEN_WIDTH // 2 - loading_text.get_width() // 2,
                                   SCREEN_HEIGHT // 2 - loading_text.get_height() // 2))
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
        for x, y in self.pellets:
            screen.blit(SPRITES["pellet"], (x * TILE_SIZE, y * TILE_SIZE))
        for x, y in self.power_pellets:
            screen.blit(SPRITES["power_pellet"],
                        (x * TILE_SIZE, y * TILE_SIZE))
