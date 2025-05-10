import pygame
import time
from maze import Maze
from pacman import PacMan
from ghost import Ghost, GHOST_CONFIGS
from utils import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, RED, BLUE, PINK, ORANGE, ROWS, COLS, font, screen, clock, game_over_screen, TILE_SIZE


def main_game(show_ghost_paths, show_generations):
    try:
        maze = Maze(show_generations=show_generations)
        pacman = PacMan()
        ghosts = Ghost.create_ghosts(maze)

        running = True
        game_state = "playing"
        power_duration = 10  # seconds
        frame_count = 0

        # Assign a unique color for each ghost's path
        ghost_path_colors = [RED, BLUE, PINK, ORANGE]

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
                # Draw ghost paths and ghosts
                # Determine the closest ghost to Pac-Man
                ghost_distances = [
                    ((ghost.x - pacman.x) ** 2 + (ghost.y - pacman.y) ** 2)
                    for ghost in ghosts
                ]
                closest_idx = ghost_distances.index(min(ghost_distances))
                # Prepare drawing order: all except closest, then closest
                draw_order = [i for i in range(
                    len(ghosts)) if i != closest_idx] + [closest_idx]
                for ghost_idx in draw_order:
                    ghost = ghosts[ghost_idx]
                    # Draw ghost path as a colored line if enabled
                    if show_ghost_paths and hasattr(ghost, "visual_path") and ghost.visual_path:
                        color = ghost_path_colors[ghost_idx % len(
                            ghost_path_colors)]
                        points = [
                            (ghost.x * TILE_SIZE + TILE_SIZE // 2,
                             ghost.y * TILE_SIZE + TILE_SIZE // 2)
                        ] + [
                            (gx * TILE_SIZE + TILE_SIZE // 2,
                             gy * TILE_SIZE + TILE_SIZE // 2)
                            for gx, gy in ghost.visual_path
                        ]
                        if len(points) > 1:
                            pygame.draw.lines(screen, color, False, points, 3)
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

    SHOW_GHOST_PATHS = True
    SHOW_GENERATIONS = False  # Toggle this to show/hide maze generation visualization

    while restart:
        restart = main_game(show_ghost_paths=SHOW_GHOST_PATHS,
                            show_generations=SHOW_GENERATIONS)
    pygame.quit()
