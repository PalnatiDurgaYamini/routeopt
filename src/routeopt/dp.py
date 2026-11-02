"""Dynamic programming: Held-Karp exact ordering of one route.

State  : (set of visited stops as a bitmask, last stop)
Recurrence: cost[mask | m][m] = min over j in mask of cost[mask][j] + d(j, m)
Time O(k^2 * 2^k), space O(k * 2^k), versus O(k!) for brute force.
"""

from __future__ import annotations

import math

from routeopt.distance import Matrix


def held_karp(matrix: Matrix) -> tuple[int, ...]:
    """Optimal visiting order of stops 1..k starting/ending at depot 0.

    ``matrix`` is a (k+1)x(k+1) matrix with the depot at index 0.
    Returns the stops as indices 1..k in optimal order.
    """
    k = len(matrix) - 1
    if k <= 0:
        return ()
    if k == 1:
        return (1,)
    full = 1 << k
    inf = math.inf
    cost = [[inf] * k for _ in range(full)]
    parent = [[-1] * k for _ in range(full)]
    for j in range(k):
        cost[1 << j][j] = matrix[0][j + 1]

    for mask in range(1, full):
        row = cost[mask]
        for j in range(k):
            base = row[j]
            if not (mask >> j) & 1 or base == inf:
                continue
            dj = matrix[j + 1]
            for m in range(k):
                if (mask >> m) & 1:
                    continue
                nmask = mask | (1 << m)
                c = base + dj[m + 1]
                if c < cost[nmask][m]:
                    cost[nmask][m] = c
                    parent[nmask][m] = j

    last = min(range(k), key=lambda j: cost[full - 1][j] + matrix[j + 1][0])
    order: list[int] = []
    mask, j = full - 1, last
    while j != -1:
        order.append(j + 1)
        prev = parent[mask][j]
        mask ^= 1 << j
        j = prev
    order.reverse()
    return tuple(order)
