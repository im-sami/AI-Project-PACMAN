import pygame
import os

SCREEN_WIDTH = 720
SCREEN_HEIGHT = 720
TILE_SIZE = 30
ROWS = SCREEN_HEIGHT // TILE_SIZE
COLS = SCREEN_WIDTH // TILE_SIZE
FPS = 10

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
PINK = (255, 192, 203)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pac-Man with AI")
clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 25)


def load_and_scale(image_path):
    image = pygame.image.load(image_path).convert_alpha()
    scaled_image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
    return scaled_image


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
    text_x = SCREEN_WIDTH // 2 - text.get_width() // 2
    text_y = SCREEN_HEIGHT // 2 - 50
    restart_x = SCREEN_WIDTH // 2 - restart_text.get_width() // 2
    restart_y = SCREEN_HEIGHT // 2
    quit_x = SCREEN_WIDTH // 2 - quit_text.get_width() // 2
    quit_y = SCREEN_HEIGHT // 2 + 50
    screen.blit(text, (text_x, text_y))
    screen.blit(restart_text, (restart_x, restart_y))
    screen.blit(quit_text, (quit_x, quit_y))
    pygame.display.flip()
    waiting_for_input = True
    while waiting_for_input:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return "restart"
                elif event.key == pygame.K_q:
                    return "quit"
    return "quit"


def show_error_screen(error_message):
    screen.fill(BLACK)
    error_text = font.render(f"Error: {str(error_message)}", True, RED)
    retry_text = font.render("Press R to restart or Q to quit", True, WHITE)
    error_x = SCREEN_WIDTH // 2 - error_text.get_width() // 2
    error_y = SCREEN_HEIGHT // 2 - 50
    retry_x = SCREEN_WIDTH // 2 - retry_text.get_width() // 2
    retry_y = SCREEN_HEIGHT // 2 + 20
    screen.blit(error_text, (error_x, error_y))
    screen.blit(retry_text, (retry_x, retry_y))
    pygame.display.flip()
    waiting_for_input = True
    while waiting_for_input:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
                elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    return False
    return False
