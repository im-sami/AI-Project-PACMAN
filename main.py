import pygame
import time
from maze import Maze
from pacman import PacMan
from ghost import Ghost, GHOST_CONFIGS
from utils import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, RED, BLUE, PINK, ORANGE, ROWS, COLS, font, screen, clock, game_over_screen


def main_game(show_rejected=False):
    try:
        maze = Maze(show_rejected=show_rejected)
        pacman = PacMan()
        ghosts = Ghost.create_ghosts(maze)

        running = True
        game_state = "playing"
        power_duration = 10  # seconds
        frame_count = 0

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            if game_state == "playing":
                dx, dy = 0, 0
                keys = pygame.key.get_pressed()
                if keys[pygame.K_UP]:
                    dy = -1
                elif keys[pygame.K_DOWN]:
                    dy = 1
                elif keys[pygame.K_LEFT]:
                    dx = -1
                elif keys[pygame.K_RIGHT]:
                    dx = 1

                if dx != 0 or dy != 0:
                    move_result = pacman.move(dx, dy, maze)
                    pacman.handle_collisions(ghosts, maze)
                    if move_result == "win":
                        game_state = "won"
                    elif move_result == "power":
                        for g in ghosts:
                            g.ate_during_power = False
                            g.just_respawned = False

                pacman.handle_powerup_expiration(ghosts, power_duration)
                for ghost in ghosts:
                    ghost.update_scared_state(pacman)

                frame_count += 1
                if frame_count % 3 == 0:
                    for ghost in ghosts:
                        ghost.handle_ai_move(pacman, maze, ghosts)
                        if ghost.check_pacman_caught(pacman):
                            pacman.lives -= 1
                            if pacman.lives <= 0:
                                game_state = "game_over"
                            else:
                                pacman.reset_after_death(ghosts)
                            break

                screen.fill((0, 0, 0))
                maze.draw()
                pacman.draw()
                for ghost in ghosts:
                    ghost.draw()
                pacman.draw_hud()
            elif game_state in ("game_over", "won"):
                result = game_over_screen(pacman.score, game_state == "won")
                if result == "restart":
                    return True
                elif result == "quit":
                    running = False
                else:
                    # Wait for user input instead of closing immediately
                    waiting = True
                    while waiting:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                running = False
                                waiting = False
                            if event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_r:
                                    return True
                                elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                                    running = False
                                    waiting = False

            pygame.display.flip()
            clock.tick(FPS)
    except Exception as e:
        from utils import show_error_screen
        return show_error_screen(str(e))
    return False


if __name__ == "__main__":
    pygame.init()
    restart = True
    # Set this to True to see rejected mazes
    show_rejected = False
    while restart:
        restart = main_game(show_rejected=show_rejected)
    pygame.quit()
