import asyncio
from pathlib import Path

import pytest

from routeopt.concurrency import fetch_orders, parallel_map, thread_map
from routeopt.distance import build_matrix
from routeopt.fileio import (
    merge_orders,
    read_orders_csv,
    renumber,
    solution_to_dict,
    write_orders_csv,
    write_solution_json,
)
from routeopt.functional import solution_cost
from routeopt.generator import generate_orders, generate_problem
from routeopt.models import Solution
from routeopt.solvers import ClusterFirstSolver
from routeopt.utils import Timer, batched, timed


def square(x: int) -> int:
    return x * x


def test_parallel_map_matches_serial() -> None:
    assert parallel_map(square, list(range(20)), workers=2) == [x * x for x in range(20)]
    assert parallel_map(square, [3], workers=4) == [9]
    assert parallel_map(square, [1, 2], workers=1) == [1, 4]


def test_thread_map() -> None:
    assert thread_map(square, [1, 2, 3], workers=3) == [1, 4, 9]


def test_parallel_solver_equals_serial_solver() -> None:
    problem = generate_problem(60, seed=9, capacity=40)
    matrix = build_matrix(problem)
    serial = ClusterFirstSolver(workers=1).solve(problem)
    parallel = ClusterFirstSolver(workers=2).solve(problem)
    assert solution_cost(matrix, serial) == pytest.approx(solution_cost(matrix, parallel))


def test_csv_roundtrip(tmp_path: Path) -> None:
    orders = generate_orders(12, seed=2)
    path = tmp_path / "o.csv"
    write_orders_csv(path, orders)
    assert list(read_orders_csv(path)) == orders


def test_renumber_and_merge() -> None:
    a, b = generate_orders(3, seed=1), generate_orders(2, seed=2)
    merged = merge_orders([a, b])
    assert [o.id for o in merged] == [1, 2, 3, 4, 5]
    assert [o.id for o in renumber(b)] == [1, 2]


def test_fetch_orders_async(tmp_path: Path) -> None:
    paths = []
    for i in range(4):
        p = tmp_path / f"f{i}.csv"
        write_orders_csv(p, generate_orders(5, seed=i))
        paths.append(p)
    orders = asyncio.run(fetch_orders(paths, concurrency=2, latency=0.01))
    assert len(orders) == 20
    assert [o.id for o in orders] == list(range(1, 21))


def test_solution_json(tmp_path: Path) -> None:
    out = tmp_path / "s.json"
    write_solution_json(out, Solution(((1, 2), (3,))), 12.3456789)
    assert solution_to_dict(Solution(((1,),)), 1.0)["routes"] == [[1]]
    assert '"total_distance": 12.3457' in out.read_text()


def test_timer_and_timed_decorator() -> None:
    with Timer() as t:
        sum(range(1000))
    assert t.elapsed >= 0

    @timed
    def add(a: int, b: int) -> int:
        return a + b

    assert add(1, 2) == 3
    assert add.__name__ == "add"


def test_batched_generator() -> None:
    assert list(batched(range(7), 3)) == [(0, 1, 2), (3, 4, 5), (6,)]
    with pytest.raises(ValueError):
        list(batched([1], 0))
