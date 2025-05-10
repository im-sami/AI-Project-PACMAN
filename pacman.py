from utils import YELLOW, SPRITES, TILE_SIZE, screen, font, SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, CYAN, ROWS, COLS
import time


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
            if (self.x, self.y) in maze.pellets:
                maze.pellets.remove((self.x, self.y))
                self.score += 10
            if (self.x, self.y) in maze.power_pellets:
                maze.power_pellets.remove((self.x, self.y))
                self.powered_up = True
                self.power_time = time.time()
                self.score += 50
                return "power"
            if not maze.pellets and not maze.power_pellets:
                return "win"
            return "moved"
        return "blocked"

    def draw(self):
        screen.blit(SPRITES["pacman"], (self.x *
                    TILE_SIZE, self.y * TILE_SIZE))

    def draw_hud(self):
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        lives_text = font.render(f"Lives: {self.lives}", True, WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (SCREEN_WIDTH -
                    lives_text.get_width() - 10, 10))
        if self.powered_up:
            time_left = max(0, int(10 - (time.time() - self.power_time)))
            power_text = font.render(f"Power: {time_left}s", True, CYAN)
            screen.blit(power_text, (SCREEN_WIDTH // 2 -
                        power_text.get_width() // 2, 10))

    def handle_collisions(self, ghosts, maze):
        for ghost in ghosts:
            if ghost.x == self.x and ghost.y == self.y:
                if ghost.is_scared and not ghost.ate_during_power:
                    ghost.reset_position()
                    self.score += 200
                else:
                    self.lives -= 1
                    if self.lives > 0:
                        self.reset_after_death(ghosts)
                    break

    def handle_powerup_expiration(self, ghosts, power_duration):
        import time
        if self.powered_up and time.time() - self.power_time > power_duration:
            self.powered_up = False
            for ghost in ghosts:
                ghost.is_scared = False
                ghost.ate_during_power = False

    def reset_after_death(self, ghosts):
        self.x, self.y = 1, 1
        self.powered_up = False
        for g in ghosts:
            g.x, g.y = g.start_x, g.start_y
            g.prev_pos = None
            g.just_respawned = False
            g.ate_during_power = False
            g.is_scared = False
        import pygame
        pygame.display.flip()
        time.sleep(1)
