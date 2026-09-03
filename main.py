#!/usr/bin/env python3
import argparse

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from a_star import a_star
from game_logic import move_enemies, game_over, move_hero, teleport
from costmap import build_costmap, nav2_cmap, display_costs
from colorama import Fore, Style, init
import time
from matplotlib.colors import Normalize


MAP_SIZE = 64
RESOLUTION = 0.1
ENEMY_COUNT = 10
SPEED = 500 # in ms

init(autoreset=True)

def build_field(coverage_percent, rng):
    '''randomly generate a field with a specific % of obstacles in it'''
    field = np.zeros((MAP_SIZE, MAP_SIZE), dtype=np.int8)

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

        x0 = rng.integers(0, MAP_SIZE - max_x)
        y0 = rng.integers(0, MAP_SIZE - max_y)

        for dx, dy in tetromino:
            field[y0 + dy, x0 + dx] = 100

    return field

def choose_positions(field, rng):
    '''choose initial positions for the goal, enemies, and hero'''
    free_cells = np.argwhere(field == 0)

    if len(free_cells) < ENEMY_COUNT + 2:
        raise ValueError("not enough free cells!")

    selected = rng.choice(len(free_cells), ENEMY_COUNT + 2, replace=False)

    hero = free_cells[selected[0]]
    goal = free_cells[selected[1]]
    enemies = free_cells[selected[2:]]

    return hero, goal, enemies

def main():
    '''main setup and update loop'''
    teleport_counter = 0
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", type=float, default=20.0) # percent coverage
    parser.add_argument("--seed", type=int, default=None)
    arguments = parser.parse_args()

    rng = np.random.default_rng(arguments.seed)
    field = build_field(arguments.coverage, rng)
    hero, goal, enemies = choose_positions(field, rng)
    costs = build_costmap(field, enemies)

    figure, axis = plt.subplots()
    extent = [ 
        -MAP_SIZE * RESOLUTION / 2,
        MAP_SIZE * RESOLUTION / 2,
        -MAP_SIZE * RESOLUTION / 2,
        MAP_SIZE * RESOLUTION / 2,
    ]

    path = a_star(field, tuple(hero), tuple(goal))
    path_plot, = axis.plot([], [], "y-", linewidth=2, label="A* Path")

    def render_path(path):
        if not path:
            path_plot.set_data([], [])
            return

        path_array = np.asarray(path)
        path_x = (path_array[:, 1] + 0.5) * RESOLUTION + extent[0]
        path_y = (path_array[:, 0] + 0.5) * RESOLUTION + extent[2]

        path_plot.set_data(path_x, path_y)

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

    hero_plot, = axis.plot([], [], "bo", markersize=9, label="Hero")
    enemy_plot, = axis.plot([], [], "ro", markersize=7, label="Enemies")
    goal_plot, = axis.plot([], [], "go", markersize=9, label="Goal")

    axis.set_title("Flatland")
    axis.set_aspect("equal")
    axis.legend()

    animation = None

    def update(_frame):
        '''field state update loop'''
        nonlocal enemies, hero, path, teleport_counter # want persistance between frames

        hero_costmap = build_costmap(field, enemies)
        path = a_star(hero_costmap, tuple(hero), tuple(goal))
        hero_cost = hero_costmap[hero[0], hero[1]]

        if hero_cost >= 25.0 and teleport_counter < 5:
            hero = teleport(hero_costmap, field, rng)
            teleport_counter += 1
        else:
            hero = move_hero(path, hero)

        enemies = move_enemies(field, enemies, hero)

        costs = build_costmap(field, enemies)
        costmap_image.set_data(display_costs(costs))
        field_image.set_data(field)

        rendered_path = path[1:]
        render_path(rendered_path)

        hero_x = (hero[1] + 0.5) * RESOLUTION + extent[0]
        hero_y = (hero[0] + 0.5) * RESOLUTION + extent[2]

        enemy_x = (enemies[:, 1] + 0.5) * RESOLUTION + extent[0]
        enemy_y = (enemies[:, 0] + 0.5) * RESOLUTION + extent[2]

        goal_x = (goal[1] + 0.5) * RESOLUTION + extent[0]
        goal_y = (goal[0] + 0.5) * RESOLUTION + extent[2]

        hero_plot.set_data([hero_x], [hero_y])
        enemy_plot.set_data(enemy_x, enemy_y)
        goal_plot.set_data([goal_x], [goal_y])

        result = game_over(enemies, hero, goal, field)

        if result == "lose":
            axis.set_title("Game Over")
            print(Fore.RED + Style.BRIGHT + "You Lost :(")
        elif result == "win":
            axis.set_title("The Hero Wins!")
            print(Fore.GREEN + Style.BRIGHT + "You Won :)")

        if result is not None:
            if animation is not None and animation.event_source is not None:
                animation.event_source.stop()
            figure.canvas.draw()
            figure.canvas.flush_events()
            plt.pause(1)
            plt.close(figure)

        return hero_plot, enemy_plot, goal_plot, path_plot, costmap_image

    animation = FuncAnimation(
        figure,
        update,
        interval=SPEED,
        cache_frame_data=False
    )
    # animation.save("animation.gif", writer="pillow", fps=5)
    plt.show()


if __name__ == "__main__":
    main()