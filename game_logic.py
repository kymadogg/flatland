import numpy as np
from colorama import Fore, Style, init

init(autoreset=True)

def move_enemies(field, enemies, hero):
    '''update the position of each enemy'''
    updated = []

    for row, column in enemies:
        candidates = []

        # loop through neighbors of 8 
        for row_change in (-1, 0, 1):
            for column_change in (-1, 0, 1):
                if row_change == 0 and column_change == 0:
                    continue

                new_cell = [row + row_change, column + column_change]

                # make sure new cell is in map bounds
                if (0 <= new_cell[0] < 64 and 0 <= new_cell[1] < 64):
                    distance = np.linalg.norm(hero - new_cell) # calc euclidean distance 
                    candidates.append((distance, new_cell[0], new_cell[1]))

        if not candidates:
            updated.append([row, column])
            continue

        _, new_cell[0], new_cell[1] = min(candidates)

        if field[new_cell[0], new_cell[1]] != 0: # hitting an obstacle logic
            field[row, column] = 100
            continue

        updated.append([new_cell[0], new_cell[1]])

    return np.asarray(updated, dtype=int).reshape(-1, 2)

def game_over(enemies, hero, goal, field):
    """return 'win', 'lose', or None while the game continues."""
    if np.array_equal(goal, hero):
        return "win"

    if np.any(np.all(enemies == hero, axis=1)): # hit obstacle or encounter enemy
        return "lose"

    return None

def move_hero(path, hero):
    if len(path) > 1:
        return np.asarray(path[1], dtype=int)

    return hero

def teleport(costmap, field, rng):
    """Move the hero to a randomly selected safe free cell."""
    
    free_cells = np.argwhere((costmap == 0) & (field == 0))
    selected = rng.integers(len(free_cells))
    print(Fore.BLUE + "Teleport Used!")
    return free_cells[selected].astype(int)










