import random

import pytest
from helpers import brute_force_cvrp, brute_force_tsp

from routeopt.distance import build_matrix, submatrix
from routeopt.dp import held_karp
from routeopt.functional import (
    compose,
    nearest_neighbour_order,
    path_length,
    solution_cost,
    two_opt,
)
from routeopt.generator import generate_problem
from routeopt.models import InfeasibleError, Order, Point, Problem
from routeopt.solvers import SOLVERS, BranchAndBoundSolver
from routeopt.solvers.cluster import bisect_clusters


def random_matrix(k: int, seed: int) -> tuple[tuple[float, ...], ...]:
    rng = random.Random(seed)
    pts = [Point(rng.uniform(0, 50), rng.uniform(0, 50)) for _ in range(k + 1)]
    return tuple(tuple(a.distance_to(b) for b in pts) for a in pts)


@pytest.mark.parametrize("k", [0, 1, 2, 3, 5, 6])
def test_held_karp_matches_brute_force(k: int) -> None:
    for seed in range(5):
        m = random_matrix(k, seed)
        order = held_karp(m)
        assert sorted(order) == list(range(1, k + 1))
        assert path_length(m, order) == pytest.approx(brute_force_tsp(m))


def test_nearest_neighbour_visits_all_once() -> None:
    m = random_matrix(7, 1)
    assert sorted(nearest_neighbour_order(m, range(1, 8))) == list(range(1, 8))


def test_two_opt_never_worse_and_keeps_stops() -> None:
    for seed in range(10):
        m = random_matrix(8, seed)
        start = tuple(range(1, 9))
        result = two_opt(m, start)
        assert sorted(result) == list(start)
        assert path_length(m, result) <= path_length(m, start) + 1e-9


def test_compose_runs_left_to_right() -> None:
    assert compose(lambda x: x + 1, lambda x: x * 10)(2) == 30


def test_bisect_clusters_respects_capacity() -> None:
    problem = generate_problem(60, seed=4, capacity=25)
    clusters = bisect_clusters(list(problem.orders), problem.capacity)
    assert all(sum(o.demand for o in c) <= 25 for c in clusters)
    assert sorted(o.id for c in clusters for o in c) == list(range(1, 61))


def test_bisect_empty() -> None:
    assert bisect_clusters([], 10) == []


@pytest.mark.parametrize("name", ["greedy", "greedy-2opt", "cluster", "exact"])
def test_every_solver_returns_valid_solution(name: str) -> None:
    problem = generate_problem(9, seed=7, capacity=20)
    solution = SOLVERS.create(name).solve(problem)  # solve() validates internally
    assert sorted(i for r in solution.routes for i in r) == list(range(1, 10))


def test_exact_matches_brute_force() -> None:
    for seed in range(4):
        problem = generate_problem(6, seed=seed, capacity=15)
        matrix = build_matrix(problem)
        solver = BranchAndBoundSolver()
        cost = solution_cost(matrix, solver.solve(problem))
        assert solver.stats is not None and solver.stats.proved_optimal
        assert cost == pytest.approx(brute_force_cvrp(problem, matrix))


def test_heuristics_never_beat_exact() -> None:
    problem = generate_problem(7, seed=11, capacity=18)
    matrix = build_matrix(problem)
    optimum = solution_cost(matrix, SOLVERS.create("exact").solve(problem))
    for name in ("greedy", "greedy-2opt", "cluster"):
        assert solution_cost(matrix, SOLVERS.create(name).solve(problem)) >= optimum - 1e-9


def test_exact_node_limit_flags_unproven() -> None:
    problem = generate_problem(9, seed=5, capacity=20)
    solver = BranchAndBoundSolver(node_limit=5)
    solver.solve(problem)
    assert solver.stats is not None and not solver.stats.proved_optimal


def test_exact_respects_vehicle_limit() -> None:
    orders = tuple(Order(i, Point(10 * i, 0), 6) for i in range(1, 4))
    problem = Problem(Point(0, 0), orders, capacity=10, max_vehicles=2)
    with pytest.raises(InfeasibleError):
        SOLVERS.create("exact").solve(problem)  # 3 orders of 6 need 3 vans


def test_submatrix_reindexes() -> None:
    m = random_matrix(4, 0)
    sub = submatrix(m, [0, 2, 4])
    assert sub[1][2] == m[2][4]


def test_unknown_solver_name() -> None:
    with pytest.raises(KeyError):
        SOLVERS.create("nope")
