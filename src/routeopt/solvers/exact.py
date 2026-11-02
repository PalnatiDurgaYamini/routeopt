"""Backtracking with branch-and-bound: exact CVRP for small instances."""

from __future__ import annotations

import math
from dataclasses import dataclass

from routeopt.distance import Matrix
from routeopt.functional import solution_cost
from routeopt.models import InfeasibleError, Problem, Route, Solution
from routeopt.solvers.base import SOLVERS, BaseSolver
from routeopt.solvers.greedy import NearestNeighbourSolver

EPS = 1e-9


@dataclass(frozen=True, slots=True)
class SearchStats:
    nodes: int
    proved_optimal: bool


@SOLVERS.register("exact")
class BranchAndBoundSolver(BaseSolver):
    """Depth-first search over route constructions.

    Backtrack : try every unvisited order next; undo after exploring.
    Bound     : cost so far + sum over unvisited orders of the cheapest edge
                that could enter them + cheapest edge back to the depot.
                Each unvisited order is entered by exactly one edge, so this is
                a valid lower bound; prune when it cannot beat the incumbent.
    Incumbent : starts from greedy+2-opt so pruning works from the first node.
    Worst case O(n!), but pruning makes n <= ~10 practical.
    """

    name = "exact"

    def __init__(self, node_limit: int = 2_000_000) -> None:
        self.node_limit = node_limit
        self.stats: SearchStats | None = None

    def _solve(self, problem: Problem, matrix: Matrix) -> Solution:
        n = len(problem.orders)
        if n == 0:
            self.stats = SearchStats(0, True)
            return Solution(())
        cap = problem.capacity
        max_v = problem.max_vehicles or n
        demand = [0, *(o.demand for o in problem.orders)]
        min_in = [min(matrix[j][i] for j in range(n + 1) if j != i) for i in range(n + 1)]

        best_cost = math.inf
        best_routes: list[Route] = []
        incumbent = NearestNeighbourSolver(improve=True)._solve(problem, matrix)
        if len(incumbent.routes) <= max_v:
            best_cost = solution_cost(matrix, incumbent)
            best_routes = list(incumbent.routes)

        unvisited = set(range(1, n + 1))
        routes: list[list[int]] = [[]]
        nodes = 0
        exhausted = True

        def dfs(cur: int, load: int, cost: float, rest: float) -> None:
            nonlocal best_cost, best_routes, nodes, exhausted
            nodes += 1
            if nodes > self.node_limit:
                exhausted = False
                return
            if not unvisited:
                total = cost + matrix[cur][0]
                if total < best_cost - EPS:
                    best_cost = total
                    best_routes = [tuple(r) for r in routes if r]
                return
            for nxt in sorted(unvisited, key=lambda j: matrix[cur][j]):
                new_rest = rest - min_in[nxt]
                options: list[tuple[float, int, bool]] = []
                if load + demand[nxt] <= cap:  # keep filling this van
                    options.append((cost + matrix[cur][nxt], load + demand[nxt], False))
                if cur != 0 and len(routes) < max_v:  # close route, start a new van
                    options.append((cost + matrix[cur][0] + matrix[0][nxt], demand[nxt], True))
                for new_cost, new_load, new_route in options:
                    if new_cost + new_rest + min_in[0] >= best_cost - EPS:
                        continue  # prune: cannot beat the incumbent
                    unvisited.remove(nxt)
                    if new_route:
                        routes.append([nxt])
                    else:
                        routes[-1].append(nxt)
                    dfs(nxt, new_load, new_cost, new_rest)
                    if new_route:
                        routes.pop()
                    else:
                        routes[-1].pop()
                    unvisited.add(nxt)

        dfs(0, 0, 0.0, sum(min_in[1:]))
        self.stats = SearchStats(nodes, exhausted)
        if not best_routes:
            raise InfeasibleError("no feasible solution within the vehicle limit")
        return Solution(tuple(best_routes))
