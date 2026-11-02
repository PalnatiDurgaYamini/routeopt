"""Divide-and-conquer clustering + dynamic-programming route ordering."""

from __future__ import annotations

from functools import partial

from routeopt.concurrency import parallel_map
from routeopt.distance import Matrix, submatrix
from routeopt.dp import held_karp
from routeopt.functional import compose, nearest_neighbour_order, two_opt
from routeopt.models import Order, Problem, Route, Solution
from routeopt.solvers.base import SOLVERS, BaseSolver


def bisect_clusters(orders: list[Order], capacity: int) -> list[list[Order]]:
    """Recursively split orders in space until each cluster fits in one van.

    Divide: cut along the wider axis at the demand-weighted median.
    Conquer: stop when total demand <= capacity.
    T(n) = 2T(n/2) + O(n log n)  =>  O(n log^2 n).
    """
    if not orders:
        return []
    if sum(o.demand for o in orders) <= capacity or len(orders) == 1:
        return [orders]
    xs = [o.location.x for o in orders]
    ys = [o.location.y for o in orders]
    wide_x = max(xs) - min(xs) >= max(ys) - min(ys)
    ordered = sorted(
        orders,
        key=lambda o: (o.location.x, o.location.y) if wide_x else (o.location.y, o.location.x),
    )
    half, running, cut = sum(o.demand for o in ordered) / 2, 0, 1
    for idx, order in enumerate(ordered[:-1], start=1):
        running += order.demand
        cut = idx
        if running >= half:
            break
    return bisect_clusters(ordered[:cut], capacity) + bisect_clusters(ordered[cut:], capacity)


def optimise_cluster(task: tuple[Matrix, int]) -> Route:
    """Order one cluster's stops (local indices 1..k). Top-level => picklable.

    Exact Held-Karp when small enough, otherwise nearest-neighbour + 2-opt.
    """
    sub, exact_limit = task
    k = len(sub) - 1
    if k <= exact_limit:
        return held_karp(sub)
    heuristic = compose(partial(nearest_neighbour_order, sub), partial(two_opt, sub))
    return tuple(heuristic(range(1, k + 1)))


@SOLVERS.register("cluster")
class ClusterFirstSolver(BaseSolver):
    """Cluster-first, route-second. ``workers > 1`` optimises clusters in parallel."""

    name = "cluster"

    def __init__(self, exact_limit: int = 10, workers: int = 1) -> None:
        self.exact_limit = exact_limit
        self.workers = workers

    def _solve(self, problem: Problem, matrix: Matrix) -> Solution:
        clusters = bisect_clusters(list(problem.orders), problem.capacity)
        id_lists = [[o.id for o in cluster] for cluster in clusters]
        tasks = [(submatrix(matrix, [0, *ids]), self.exact_limit) for ids in id_lists]
        local_orders = parallel_map(optimise_cluster, tasks, self.workers)
        routes = tuple(
            tuple(ids[i - 1] for i in local)
            for ids, local in zip(id_lists, local_orders, strict=True)
        )
        return Solution(routes)
