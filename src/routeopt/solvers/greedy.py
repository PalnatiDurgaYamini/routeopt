"""Greedy nearest-neighbour construction (+ optional 2-opt polish)."""

from __future__ import annotations

from routeopt.distance import Matrix
from routeopt.functional import two_opt
from routeopt.models import Problem, Route, Solution
from routeopt.solvers.base import SOLVERS, BaseSolver


class NearestNeighbourSolver(BaseSolver):
    """Fill one van at a time, always driving to the closest order that still fits.

    Greedy-choice: local best, no backtracking, so fast but not optimal.
    Time O(n^2), space O(n).
    """

    name = "greedy"

    def __init__(self, improve: bool = False) -> None:
        self.improve = improve

    def _solve(self, problem: Problem, matrix: Matrix) -> Solution:
        demand = {o.id: o.demand for o in problem.orders}
        unvisited = set(demand)
        routes: list[Route] = []
        while unvisited:
            current, load = 0, 0
            route: list[int] = []
            while True:
                fits = [j for j in unvisited if load + demand[j] <= problem.capacity]
                if not fits:
                    break
                nxt = min(fits, key=lambda j: (matrix[current][j], j))  # noqa: B023
                route.append(nxt)
                unvisited.remove(nxt)
                load += demand[nxt]
                current = nxt
            routes.append(tuple(route))
        if self.improve:
            routes = [two_opt(matrix, r) for r in routes]
        return Solution(tuple(routes))


@SOLVERS.register("greedy")
def _greedy() -> BaseSolver:
    return NearestNeighbourSolver()


@SOLVERS.register("greedy-2opt")
def _greedy_2opt() -> BaseSolver:
    return NearestNeighbourSolver(improve=True)
