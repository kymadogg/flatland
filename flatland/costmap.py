import numpy as np
from matplotlib.colors import LinearSegmentedColormap

def build_costmap(field: np.ndarray, enemies: np.ndarray, inflation_radius: int = 5,) -> np.ndarray:
    costs = field.astype(float, copy=True)

    for row, column in enemies:
        for row_change in range(-inflation_radius, inflation_radius + 1):
            for column_change in range(-inflation_radius, inflation_radius + 1):
                new_row = row + row_change
                new_column = column + column_change

                if not 0 <= new_row < costs.shape[0] or not 0 <= new_column < costs.shape[1]:
                    continue

                distance = np.hypot(row_change, column_change)

                if distance == 0:
                    costs[new_row, new_column] = np.inf
                elif distance <= inflation_radius:
                    costs[new_row, new_column] += 50 / distance

    costs[field != 0] = np.inf
    return costs

nav2_costmap_colors = [
    (0.00, "#cac4cd"),  # free space
    (0.05, "#4b145f"),  
    (0.20, "#7a1fa2"),  # low
    (0.40, "#b026c7"),  
    (0.60, "#e83eaa"),  # high
    (0.75, "#ff70c7"),  
    (0.88, "#00d9d9"),  
    (0.96, "#ffb3e6"),  
    (1.00, "#8f007f"),  # lethal
]

nav2_cmap = LinearSegmentedColormap.from_list("Nav2Costmap", nav2_costmap_colors)

def display_costs(costs):
    return np.nan_to_num(
        costs,
        nan=0.0,
        posinf=100.0,
        neginf=0.0,
    ).clip(0, 100)
