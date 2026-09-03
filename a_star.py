import heapq
from typing import TypeAlias
import numpy as np
from numpy import typing as npt

from helpers import euclidean_distance, neighbors_8, neighbors_4

Cell: TypeAlias = tuple[int, int]

def a_star(field: npt.ArrayLike,start: Cell,goal: Cell,) -> list[Cell]:
    grid = np.asarray(field)

    if np.isinf(grid[start]) or np.isinf(grid[goal]):
        return []

    frontier: list[tuple[float, Cell]] = []
    heapq.heappush(frontier, (0.0, start))

    came_from: dict[Cell, Cell | None] = {start: None}
    cost_so_far: dict[Cell, float] = {start: 0.0}

    while frontier:
        _, current = heapq.heappop(frontier)

        if current == goal: # if you are at the goal
            break

        for neighbor in neighbors_8(current):

            if np.isinf(grid[neighbor[0], neighbor[1]]):
                continue

            row_change = neighbor[0] - current[0]
            column_change = neighbor[1] - current[1]

            is_diagonal = row_change != 0 and column_change != 0

            if is_diagonal:
                vertical_blocked = np.isinf(grid[current[0] + row_change, current[1]])
                horizontal_blocked = np.isinf( grid[current[0], current[1] + column_change])

                if vertical_blocked or horizontal_blocked:
                    continue

            move_cost = euclidean_distance((0, 0), (row_change, column_change))
            cell_cost = grid[neighbor[0], neighbor[1]]
            new_cost = cost_so_far[current] + move_cost + cell_cost

            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + euclidean_distance(neighbor, goal)
                heapq.heappush(frontier, (priority, neighbor))
                came_from[neighbor] = current

    if goal not in came_from:
        return []

    path: list[Cell] = []
    current: Cell | None = goal

    while current is not None:
        path.append(current)
        current = came_from[current]

    return path[::-1]