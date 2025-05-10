import pygame
import time
from maze import Maze
from pacman import PacMan
from ghost import Ghost, GHOST_CONFIGS
from utils import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, RED, BLUE, PINK, ORANGE, ROWS, COLS, font, screen, clock, game_over_screen, TILE_SIZE


def main_game(show_rejected=False, show_ghost_paths=True):
    try:
        maze = Maze(show_rejected=show_rejected)
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

                # Always update ghost paths for visualization
                ghost_paths = []
                if show_ghost_paths:
                    for ghost in ghosts:
                        if not ghost.is_scared:
                            path = ghost.full_bfs_path(
                                pacman.x, pacman.y, maze)
                            ghost.visual_path = path
                            ghost.path_length = len(path)
                            ghost_paths.append((ghost, path))
                        else:
                            ghost.visual_path = []
                            ghost.path_length = float('inf')

                    # Build a map: (x, y) -> (ghost_idx, path_length)
                    tile_to_ghost = {}
                    for idx, (ghost, path) in enumerate(ghost_paths):
                        for step, pos in enumerate(path):
                            if pos not in tile_to_ghost or step < tile_to_ghost[pos][1]:
                                tile_to_ghost[pos] = (idx, step)

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
                for ghost_idx, ghost in enumerate(ghosts):
                    # Draw ghost path as a colored line if enabled
                    if show_ghost_paths and hasattr(ghost, "visual_path") and ghost.visual_path:
                        color = ghost_path_colors[ghost_idx % len(
                            ghost_path_colors)]
                        # Only keep tiles where this ghost is the closest
                        filtered_path = []
                        for step, pos in enumerate(ghost.visual_path):
                            if tile_to_ghost.get(pos, (None,))[0] == ghost_idx:
                                filtered_path.append(pos)
                        # Draw line from ghost to filtered path
                        if filtered_path:
                            points = [
                                (ghost.x * TILE_SIZE + TILE_SIZE // 2,
                                 ghost.y * TILE_SIZE + TILE_SIZE // 2)
                            ] + [
                                (gx * TILE_SIZE + TILE_SIZE // 2,
                                 gy * TILE_SIZE + TILE_SIZE // 2)
                                for gx, gy in filtered_path
                            ]
                            if len(points) > 1:
                                pygame.draw.lines(
                                    screen, color, False, points, 3)
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
