import numpy as np

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
                if (0 <= new_cell[0] < field.shape[0] and 0 <= new_cell[1] < field.shape[0]):
                    distance = np.linalg.norm(hero - new_cell) # calc euclidean distance to hero from new cell 
                    candidates.append((distance, new_cell[0], new_cell[1]))

        if not candidates:
            updated.append([row, column])
            continue

        _, new_cell[0], new_cell[1] = min(candidates) # return the shortest distance

        if field[new_cell[0], new_cell[1]] != 0: # hitting an obstacle logic
            field[row, column] = 100
            continue

        updated.append([new_cell[0], new_cell[1]])

    return np.asarray(updated, dtype=int).reshape(-1, 2)

def game_over(field, enemies, hero, goal):
    """Return 'win', 'lose', 'trapped', or None."""
    if np.array_equal(hero, goal):
        return "win"

    if np.any(np.all(enemies == hero, axis=1)):
        return "lose"

    if field[tuple(goal)] != 0:
        return "trapped"

    return None

def move_hero(path, hero):
    '''move the hero along the path'''
    if len(path) > 1:
        return np.asarray(path[1], dtype=int)

    return hero


