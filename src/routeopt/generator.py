"""Reproducible random problem instances (seeded)."""

from __future__ import annotations

import random

from routeopt.models import Order, Point, Problem


def generate_orders(n: int, seed: int = 0, size: float = 100.0, max_demand: int = 9) -> list[Order]:
    rng = random.Random(seed)
    return [
        Order(
            i,
            Point(round(rng.uniform(0, size), 2), round(rng.uniform(0, size), 2)),
            rng.randint(1, max_demand),
        )
        for i in range(1, n + 1)
    ]


def generate_problem(
    n: int, seed: int = 0, capacity: int = 30, size: float = 100.0, max_demand: int = 9
) -> Problem:
    depot = Point(size / 2, size / 2)
    orders = tuple(generate_orders(n, seed, size, max_demand))
    return Problem(depot, orders, capacity)
