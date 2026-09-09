use pyo3::prelude::*;
use ordered_float::OrderedFloat;
use std::cmp::Reverse;
use std::collections::{BinaryHeap, HashMap};
use numpy::PyReadonlyArray2;
use heapq::PriorityQueue;

type Cell = (i32, i32);


fn heuristic(a: Cell, b: Cell) -> f64 { //heuristic
    let row_difference = a.0 - b.0;
    let column_difference = a.1 - b.1;

    ((row_difference * row_difference+ column_difference * column_difference) as f64).sqrt()
}

#[pyfunction]
fn n8(cell:Cell, side_length:i32) -> PyResult<Vec<Cell>>{
    let mut neighbors: Vec<Cell> = Vec::new();

    for dr in -1..=1 {
        for dc in -1..=1 {
            if dr == 0 && dc == 0{
                continue
            }
            let new_cell: (i32, i32) = (cell.0 + dr, cell.1 + dc);

            if 0 <= new_cell.0 && new_cell.0 < side_length 
            && 0 <= new_cell.1 && new_cell.1 < side_length {
                neighbors.push(new_cell);
            }
        }
    }
    Ok(neighbors)
}

#[pyfunction]
fn a_star_rs(field: PyReadonlyArray2<'_, f64>, start: Cell, goal: Cell,) -> PyResult<Vec<Cell>> {
    let grid = field.as_array();
    let rows = grid.shape()[0] as i32;
    let columns = grid.shape()[1] as i32;

    let in_bounds = |cell: Cell| {
        cell.0 >= 0 && cell.0 < rows && cell.1 >= 0 && cell.1 < columns
    };

    if !in_bounds(start) || !in_bounds(goal) {
        return Ok(Vec::new());
    }

    let value_at = |cell: Cell| {
        grid[(cell.0 as usize, cell.1 as usize)]
    };

    if value_at(start).is_infinite() || value_at(goal).is_infinite() {
        return Ok(Vec::new());
    }

    let mut frontier = BinaryHeap::new();
    frontier.push(Reverse((OrderedFloat(0.0), start)));

    let mut came_from: HashMap<Cell, Option<Cell>> = HashMap::new();
    let mut cost_so_far: HashMap<Cell, f64> = HashMap::new();

    came_from.insert(start, None);
    cost_so_far.insert(start, 0.0);

    while let Some(Reverse((_, current))) = frontier.pop() {
        if current == goal {
            break;
        }

        for neighbor in n8(current, rows)? {
            let neighbor_cost = value_at(neighbor);

            if neighbor_cost.is_infinite() {
                continue;
            }

            let row_change = neighbor.0 - current.0;
            let column_change = neighbor.1 - current.1;

            if row_change != 0 && column_change != 0 {
                let vertical = (current.0 + row_change, current.1);
                let horizontal = (current.0, current.1 + column_change);

                if value_at(vertical).is_infinite()
                    || value_at(horizontal).is_infinite()
                {
                    continue;
                }
            }

            let move_cost = heuristic((0, 0),(row_change, column_change),);
            let new_cost = cost_so_far[&current]+ move_cost+ neighbor_cost;

            if cost_so_far.get(&neighbor).is_none_or(|old_cost| new_cost < *old_cost){
                cost_so_far.insert(neighbor, new_cost);

                let priority = new_cost + heuristic(neighbor, goal);

                frontier.push(Reverse((OrderedFloat(priority),neighbor)));
                came_from.insert(neighbor, Some(current));
            }
        }
    }

    if !came_from.contains_key(&goal) {
        return Ok(Vec::new());
    }

    let mut path = Vec::new();
    let mut current = goal;

    while let Some(previous) = came_from[&current] {
        path.push(current);
        current = previous;
    }

    path.push(start);
    path.reverse();

    Ok(path)
}

#[pyfunction]
fn a_star_rs_v2(field: PyReadonlyArray2<'_, f64>, start: Cell, goal: Cell,) -> PyResult<Vec<Cell>> {
    // a star implementation using heapq instead of hashmaps

    let grid = field.as_array();
    let rows = grid.shape()[0] as i32;
    let columns = grid.shape()[1] as i32;

    // out of bounds error handling
    let in_bounds = |cell: Cell| {
        cell.0 >= 0 && cell.0 < rows && cell.1 >= 0 && cell.1 < columns
    };

    // if start is goal
    if !in_bounds(start) || !in_bounds(goal) {
        return Ok(Vec::new());
    }

    // 
    let value_at = |cell: Cell| {
        grid[(cell.0 as usize, cell.1 as usize)]
    };

    if value_at(start).is_infinite() || value_at(goal).is_infinite() {
        return Ok(Vec::new());
    }

    let flat_index = |cell: Cell| -> usize {
        (cell.0 as usize) * (columns as usize) + (cell.1 as usize)
    };

    let total_cells = (rows as usize) * (columns as usize);
    let mut cost_so_far = vec![f64::INFINITY; total_cells];
    let mut came_from: Vec<Option<Cell>> = vec![None; total_cells];
    let mut closed_set = vec![false; total_cells];


    // holds queue payloads
    struct Node {
        cell: Cell,
        f_cost: f64,
    }

    // use 'move' so 'goal' is safely owned by the closure
    let min_heap_score = Box::new(move |node: &Node| {
        Reverse(OrderedFloat(node.f_cost))
    });

    let mut frontier = PriorityQueue::new(min_heap_score);

    // value trackers 
    cost_so_far[flat_index(start)] = 0.0;
    let start_h = heuristic(start, goal);

    frontier.push(Node{
        cell: start,
        f_cost: start_h,
    });

    while let Some(current) = frontier.pop(){
        let current = current.cell;
        let current_idx = flat_index(current);

        // if current cell is goal
        if current == goal{
            break;
        }

        // lazy deletion
        if closed_set[current_idx] {
            continue;
        }

        closed_set[current_idx] = true;

        // find next walkable cells
        for neighbor in n8(current, rows)?{ 
            let neighbor_cost: f64 = value_at(neighbor);

            if neighbor_cost.is_infinite(){
                continue;
            }

            let row_change: i32 = neighbor.0 - current.0;
            let column_change: i32 = neighbor.1 - current.1;
            
            // prevent corner cutting
            if row_change != 0 && column_change != 0 {
                let vertical: (i32, i32) = (current.0 + row_change, current.1);
                let horizontal: (i32, i32) = (current.0, current.1 + column_change);

                if value_at(vertical).is_infinite() || value_at(horizontal).is_infinite() {
                    continue;
                }
            }

            let neighbor_idx = flat_index(neighbor);

            // more lazy deletion
            if closed_set[neighbor_idx] {
                continue;
            }

            let move_cost = heuristic((0, 0), (row_change, column_change));
            let new_cost = cost_so_far[current_idx] + move_cost + neighbor_cost;

            if new_cost < cost_so_far[neighbor_idx] {
                cost_so_far[neighbor_idx] = new_cost;
                came_from[neighbor_idx] = Some(current);
                
                // pushing auto recalcs using score function
                let h_cost = heuristic(neighbor, goal);
                frontier.push(Node {
                    cell: neighbor,
                    f_cost: new_cost + h_cost,
                });
            }
        }
    }

    // constructing the right path
    let goal_idx = flat_index(goal);

    if cost_so_far[goal_idx].is_infinite() {
        return Ok(Vec::new());
    }

    let mut path = Vec::new();
    let mut current = goal;

    while let Some(previous) = came_from[flat_index(current)] {
        path.push(current);
        current = previous;
    }

    path.push(start);
    path.reverse();

    Ok(path)
}

#[pymodule]
fn flatland(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(n8, m)?)?;
    m.add_function(wrap_pyfunction!(a_star_rs, m)?)?;
    m.add_function(wrap_pyfunction!(a_star_rs_v2, m)?)?;
    Ok(())
}
