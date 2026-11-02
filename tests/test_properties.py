"""Property-based tests: state a rule, let Hypothesis hunt for counter-examples."""

from hypothesis import given, settings
from hypothesis import strategies as st

from routeopt.distance import build_matrix
from routeopt.functional import path_length, solution_cost, two_opt
from routeopt.models import Order, Point, Problem
from routeopt.solvers import SOLVERS

coords = st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False)


@st.composite
def problems(draw: st.DrawFn, max_n: int = 9) -> Problem:
    n = draw(st.integers(min_value=0, max_value=max_n))
    capacity = draw(st.integers(min_value=5, max_value=20))
    orders = tuple(
        Order(i, Point(draw(coords), draw(coords)), draw(st.integers(1, capacity)))
        for i in range(1, n + 1)
    )
    return Problem(Point(50, 50), orders, capacity)


@settings(max_examples=40, deadline=None)
@given(problems(), st.sampled_from(["greedy", "greedy-2opt", "cluster"]))
def test_solution_serves_every_order_exactly_once(problem: Problem, name: str) -> None:
    solution = SOLVERS.create(name).solve(problem)
    served = sorted(i for route in solution.routes for i in route)
    assert served == list(range(1, len(problem.orders) + 1))


@settings(max_examples=40, deadline=None)
@given(problems(), st.sampled_from(["greedy", "greedy-2opt", "cluster"]))
def test_no_route_exceeds_capacity(problem: Problem, name: str) -> None:
    demand = {o.id: o.demand for o in problem.orders}
    for route in SOLVERS.create(name).solve(problem).routes:
        assert sum(demand[i] for i in route) <= problem.capacity


@settings(max_examples=25, deadline=None)
@given(problems(max_n=7))
def test_exact_is_never_worse_than_any_heuristic(problem: Problem) -> None:
    matrix = build_matrix(problem)
    best = solution_cost(matrix, SOLVERS.create("exact").solve(problem))
    for name in ("greedy", "greedy-2opt", "cluster"):
        assert best <= solution_cost(matrix, SOLVERS.create(name).solve(problem)) + 1e-6


@settings(max_examples=40, deadline=None)
@given(problems(max_n=8))
def test_two_opt_never_increases_length(problem: Problem) -> None:
    matrix = build_matrix(problem)
    route = tuple(range(1, len(problem.orders) + 1))
    assert path_length(matrix, two_opt(matrix, route)) <= path_length(matrix, route) + 1e-9
