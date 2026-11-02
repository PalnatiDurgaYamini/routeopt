"""Pure, side-effect-free building blocks (functional style).

Every function here returns new immutable values and never mutates its inputs,
so they are trivially testable and safe to run in worker processes.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from functools import partial, reduce
from itertools import pairwise
from typing import Any

from routeopt.distance import Matrix
from routeopt.models import Route, Solution


def identity(x: Any) -> Any:
    return x


def compose(*fns: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """compose(f, g, h)(x) == h(g(f(x))) - left-to-right pipeline (higher-order)."""
    return reduce(lambda f, g: lambda x: g(f(x)), fns, identity)


def path_length(matrix: Matrix, route: Route) -> float:
    """Length of depot -> route... -> depot. O(len(route))."""
    stops = (0, *route, 0)
    return sum(matrix[a][b] for a, b in pairwise(stops))


def solution_cost(matrix: Matrix, solution: Solution) -> float:
    return sum(map(partial(path_length, matrix), solution.routes))


def nearest_neighbour_order(matrix: Matrix, nodes: Iterable[int]) -> Route:
    """Greedy tour: repeatedly visit the closest unvisited node. O(k^2)."""
    remaining = set(nodes)
    current = 0
    order: list[int] = []
    while remaining:
        nxt = min(remaining, key=lambda j: (matrix[current][j], j))  # noqa: B023
        order.append(nxt)
        remaining.remove(nxt)
        current = nxt
    return tuple(order)


def two_opt(matrix: Matrix, route: Route) -> Route:
    """2-opt local search: reverse segments while that shortens the route.

    Never returns a longer route than the input. Each pass is O(k^2) candidate
    reversals x O(k) evaluation = O(k^3); fine for the short routes here.
    """
    best, best_len = tuple(route), path_length(matrix, route)
    improved = True
    while improved:
        improved = False
        for i in range(len(best) - 1):
            for j in range(i + 1, len(best)):
                candidate = best[:i] + best[i : j + 1][::-1] + best[j + 1 :]
                length = path_length(matrix, candidate)
                if length < best_len - 1e-12:
                    best, best_len, improved = candidate, length, True
    return best
