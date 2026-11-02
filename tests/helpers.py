"""Shared test helpers: an independent brute-force oracle."""

from __future__ import annotations

import itertools
import math

from routeopt.distance import Matrix
from routeopt.models import Problem


def brute_force_cvrp(problem: Problem, matrix: Matrix) -> float:
    """Try every permutation x every way to cut it into routes. Only for n <= 6."""
    n = len(problem.orders)
    demand = [0, *(o.demand for o in problem.orders)]
    best = math.inf
    for perm in itertools.permutations(range(1, n + 1)):
        for cuts in range(1 << max(n - 1, 0)):
            routes, current = [], [perm[0]] if n else []
            for pos in range(1, n):
                if (cuts >> (pos - 1)) & 1:
                    routes.append(current)
                    current = []
                current.append(perm[pos])
            if current:
                routes.append(current)
            if any(sum(demand[i] for i in r) > problem.capacity for r in routes):
                continue
            total = sum(matrix[a][b] for r in routes for a, b in itertools.pairwise([0, *r, 0]))
            best = min(best, total)
    return best


def brute_force_tsp(matrix: Matrix) -> float:
    k = len(matrix) - 1
    if k == 0:
        return 0.0
    return min(
        sum(matrix[a][b] for a, b in itertools.pairwise([0, *perm, 0]))
        for perm in itertools.permutations(range(1, k + 1))
    )
