from collections import deque
import random
from utils import ROWS, COLS, SPRITES, screen, TILE_SIZE, font


class MazeGenerator:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols

    def generate_maze(self):
        population = [self._random_candidate() for _ in range(30)]
        for _ in range(100):
            scored = sorted(population, key=self._fitness, reverse=True)
            elite = scored[:10]
            population = elite[:]
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
        wall_score = sum(sum(row) for row in grid)
        path_score = self._avg_path_length(grid)
        return wall_score + path_score * 0.5

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
        # Show loading message before generating maze
        from utils import screen, font, SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE
        import pygame
        screen.fill(BLACK)
        loading_text = font.render("Generating Maze...", True, WHITE)
        screen.blit(loading_text, (SCREEN_WIDTH // 2 - loading_text.get_width() // 2,
                                   SCREEN_HEIGHT // 2 - loading_text.get_height() // 2))
        pygame.display.flip()
        # retry until reachable area covers ≥50%
        total = ROWS * COLS
        while True:
            self.grid = self.generator.generate_maze()
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
