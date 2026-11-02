"""Domain model (the *abstraction* step): only what matters for routing.

Real world -> model:
  business location      -> depot Point
  customer delivery      -> Order(id, location, demand)
  van                    -> capacity (all vans identical)
  driver's daily plan    -> Route = tuple of order ids
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import chain

Route = tuple[int, ...]


class InfeasibleError(ValueError):
    """Raised when a problem or a proposed solution violates a hard constraint."""


@dataclass(frozen=True, slots=True)
class Point:
    x: float
    y: float

    def distance_to(self, other: Point) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)


@dataclass(frozen=True, slots=True)
class Order:
    id: int
    location: Point
    demand: int


@dataclass(frozen=True, slots=True)
class Problem:
    """A capacitated vehicle-routing instance.

    Order ids must be exactly 1..n so an id doubles as an index into the
    distance matrix (index 0 is the depot).
    """

    depot: Point
    orders: tuple[Order, ...]
    capacity: int
    max_vehicles: int | None = None

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise InfeasibleError("capacity must be positive")
        if self.max_vehicles is not None and self.max_vehicles < 1:
            raise InfeasibleError("max_vehicles must be at least 1")
        if [o.id for o in self.orders] != list(range(1, len(self.orders) + 1)):
            raise InfeasibleError("order ids must be exactly 1..n, in order")
        for o in self.orders:
            if not 1 <= o.demand <= self.capacity:
                raise InfeasibleError(f"order {o.id}: demand must be in 1..capacity")


@dataclass(frozen=True, slots=True)
class Solution:
    routes: tuple[Route, ...]


def validate_solution(problem: Problem, solution: Solution) -> None:
    """Check every hard constraint; raise InfeasibleError on the first violation."""
    demand = {o.id: o.demand for o in problem.orders}
    served = list(chain.from_iterable(solution.routes))
    if sorted(served) != sorted(demand):
        raise InfeasibleError("every order must be served exactly once")
    for route in solution.routes:
        if not route:
            raise InfeasibleError("empty route")
        if sum(demand[i] for i in route) > problem.capacity:
            raise InfeasibleError(f"route {route} exceeds vehicle capacity")
    if problem.max_vehicles is not None and len(solution.routes) > problem.max_vehicles:
        raise InfeasibleError("solution uses more vehicles than available")
