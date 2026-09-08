import numpy as np
from matplotlib.colors import LinearSegmentedColormap


def neighbors_8(cell) -> list[tuple[int, int]]:
    neighbors = []

    for row_change in (-1, 0, 1):
        for column_change in (-1, 0, 1):
            if row_change == 0 and column_change == 0:
                continue

            new_cell = (cell[0] + row_change, cell[1] + column_change)

            if 0 <= new_cell[0] < 64 and 0 <= new_cell[1] < 64:
                neighbors.append(new_cell)
    return neighbors


def neighbors_4(cell) -> list[tuple[int, int]]:
    neighbors = []
    row, column = cell

    for row_change, column_change in (
        (-1, 0),  # up
        (1, 0),   # down
        (0, -1),  # left
        (0, 1),   # right
    ):
        new_cell = (row + row_change, column + column_change)

        if 0 <= new_cell[0] < 64 and 0 <= new_cell[1] < 64:
            neighbors.append(new_cell)
    return neighbors


def euclidean_distance(first: tuple[int, int], second: tuple[int, int]) -> float:
    return float(np.linalg.norm(np.asarray(first) - np.asarray(second)))