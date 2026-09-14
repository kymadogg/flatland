#!/usr/bin/env python3
import argparse
import time
import sys

import matplotlib

if "--headless" in sys.argv:
    matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from .a_star import a_star
from .game_logic import move_enemies, game_over, move_hero
from .costmap import build_costmap, nav2_cmap, display_costs
from colorama import Fore, Style, init
from matplotlib.colors import Normalize
from .flatland import a_star_rs # rust module import
from .game_logging import log_config, log_state, log_result

RESOLUTION = 0.1 # grid resolution
DIFFICULTY = 0 # 0 = easy, 1 = medium, 2 = hard (maybe implement?)

init(autoreset=True)

def build_field(size, coverage_percent, rng):
    '''randomly generate a field with a specific % of obstacles in it'''
    field = np.zeros((size, size), dtype=np.int8)

    tetrominoes = [
        [(0, 0), (1, 0), (2, 0), (2, 1)],
        [(0, 0), (1, 0), (2, 0), (3, 0)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(0, 0), (1, 0), (2, 0), (1, 1)],
    ]

    while np.count_nonzero(field) / field.size * 100 < coverage_percent:
        tetromino = tetrominoes[rng.integers(len(tetrominoes))]
        max_x = max(x for x, _ in tetromino)
        max_y = max(y for _, y in tetromino)

        x0 = rng.integers(0, size - max_x)
        y0 = rng.integers(0, size - max_y)

        for dx, dy in tetromino:
            field[y0 + dy, x0 + dx] = 100

    return field

def choose_positions(field, enemy_count, rng):
    '''choose initial positions for the goal, enemies, and hero'''
    free_cells = np.argwhere(field == 0)

    if len(free_cells) < enemy_count + 2:
        raise ValueError("not enough free cells!")

    selected = rng.choice(len(free_cells), enemy_count + 2, replace=False)

    hero = free_cells[selected[0]]
    goal = free_cells[selected[1]]
    enemies = free_cells[selected[2:]]

    return hero, goal, enemies


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage","-c", type=float, default=20.0) # percent coverage
    parser.add_argument("--seed","-r", type=int, default=None)
    parser.add_argument("--speed","-ms", type=int, default=500) # update speed in ms
    parser.add_argument("--size", "-s", type=int, default=64) # grid size
    parser.add_argument("--version", "-v", type=str, default="py") # other option is "rs" 
    parser.add_argument("--enemies", "-e", type=int, default=10)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--data", action="store_true")
    parser.add_argument("--frames", type=int, default=1000) # for headless mode
    return parser.parse_args()

def main():
    '''main setup and update loop'''
    teleport_counter = 0
    step = 0
    args = get_args()

    rng = np.random.default_rng(args.seed)
    field = build_field(args.size, args.coverage, rng)
    hero, goal, enemies = choose_positions(field, args.enemies, rng)

    if args.data:
        log_config(args, hero, goal, enemies)

    figure, axis = plt.subplots()
    extent = [ 
        -args.size * RESOLUTION / 2,
        args.size * RESOLUTION / 2,
        -args.size * RESOLUTION / 2,
        args.size * RESOLUTION / 2,
    ]

    path = None

    path_plot, = axis.plot([], [], "y-", linewidth=2, label="A* Path")

    def render_path(path):
        if not path:
            path_plot.set_data([], [])
            return

        path_array = np.asarray(path)
        path_x = (path_array[:, 1] + 0.5) * RESOLUTION + extent[0]
        path_y = (path_array[:, 0] + 0.5) * RESOLUTION + extent[2]

        path_plot.set_data(path_x, path_y)


    costs = build_costmap(field, enemies)

    field_image = axis.imshow(
        field,
        cmap="gray_r",
        vmin=0,
        vmax=100,
        origin="lower",
        extent=extent #type:ignore
    )

    costmap_image = axis.imshow(
        display_costs(costs),
        cmap=nav2_cmap,
        norm=Normalize(vmin=0, vmax=50),
        alpha=0.65,
        origin="lower",
        extent=extent #type:ignore
    )

    hero_plot, = axis.plot([], [], "bo", markersize=7, label="Hero")
    enemy_plot, = axis.plot([], [], "ro", markersize=7, label="Enemies")
    goal_plot, = axis.plot([], [], "go", markersize=7, label="Goal")

    axis.set_title("Flatland")
    axis.set_aspect("equal")
    axis.grid(False)
    axis.set_xticks([])
    axis.set_yticks([])

    animation = None

    def render(enemies, hero, path, costs):
        costmap_image.set_data(display_costs(costs))
        field_image.set_data(field)

        render_path(path[1:] if path else [])

        hero_x = (hero[1] + 0.5) * RESOLUTION + extent[0]
        hero_y = (hero[0] + 0.5) * RESOLUTION + extent[2]
 
        enemy_x = (enemies[:, 1] + 0.5) * RESOLUTION + extent[0]
        enemy_y = (enemies[:, 0] + 0.5) * RESOLUTION + extent[2]

        goal_x = (goal[1] + 0.5) * RESOLUTION + extent[0]
        goal_y = (goal[0] + 0.5) * RESOLUTION + extent[2]

        hero_plot.set_data([hero_x], [hero_y])
        enemy_plot.set_data(enemy_x, enemy_y)
        goal_plot.set_data([goal_x], [goal_y])

        return hero_plot, enemy_plot, goal_plot, path_plot, costmap_image

    def update(_frame):
        '''game state update loop'''
        nonlocal enemies, hero, path, teleport_counter, step # want persistance between frames

        hero_costmap = build_costmap(field, enemies)
        rust_field = np.asarray(hero_costmap, dtype=np.float64)
        start_time = time.perf_counter_ns()

        if args.version == "py":
            path = a_star(hero_costmap, tuple(hero), tuple(goal))
        elif args.version == "rs":
            path = a_star_rs(rust_field, tuple(hero),tuple(goal),)
        else:
            raise ValueError(f"Unknown A* version: {args.version}")

        elapsed_ms = (time.perf_counter_ns() - start_time) / 1_000_000
        step += 1

        if args.data:
            log_state(
                step=step,
                hero=hero,
                goal=goal,
                enemies=enemies,
                path=path,
                hero_cost=float(hero_costmap[tuple(hero)]),
                planner_time_ms=elapsed_ms,
            )

        should_teleport = (
            teleport_counter < 5
            and (hero_costmap[tuple(hero)] >= 25.0 or not path)
        )

        if should_teleport:
            safe_cells = np.argwhere(
                (hero_costmap == 0) & (field == 0)
            )

            if len(safe_cells) == 0:
                print("No safe teleport location.")
                plt.close(figure)
                return

            hero = safe_cells[rng.integers(len(safe_cells))].astype(int)
            teleport_counter += 1
        else:
            if not path:
                print("Null Game")
                plt.close(figure)
                return

            hero = move_hero(path, hero)

        enemies = move_enemies(field, enemies, hero)

        if not args.headless:
            costs = build_costmap(field, enemies)
            render(enemies, hero, path, costs)

        result = game_over(field, enemies, hero, goal)

        if result == "win":
            print(Fore.GREEN + Style.BRIGHT + "Won", teleport_counter)
        elif result == "lose":
            print(Fore.RED + Style.BRIGHT + "Lost", teleport_counter)
        elif result == "trapped":
            print(Fore.MAGENTA + Style.BRIGHT + "Blocked Goal", teleport_counter)

        if result is not None:
            if args.data:
                log_result(result, step, teleport_counter)
            if animation is not None and animation.event_source is not None:
                animation.event_source.stop()
            figure.canvas.draw()
            figure.canvas.flush_events()
            plt.pause(0.1)
            plt.close(figure)

        return hero_plot, enemy_plot, goal_plot, path_plot, costmap_image

    if args.headless:
        for _ in range(args.frames):
            if not plt.fignum_exists(figure.number):
                break

            update(None)
    else:
        animation = FuncAnimation(
            figure,
            update,
            interval=args.speed,
            cache_frame_data=False,
        )
        plt.show()


if __name__ == "__main__":
    main()