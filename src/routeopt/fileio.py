"""CSV / JSON input and output. Reading is a generator, so files stream."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Iterator, Sequence
from itertools import chain
from pathlib import Path

from routeopt.models import Order, Point, Solution


def parse_orders_csv(lines: Iterable[str]) -> Iterator[Order]:
    """Lazily yield orders from CSV lines with columns id,x,y,demand."""
    for row in csv.DictReader(lines):
        yield Order(int(row["id"]), Point(float(row["x"]), float(row["y"])), int(row["demand"]))


def read_orders_csv(path: Path) -> Iterator[Order]:
    with open(path, newline="") as handle:
        yield from parse_orders_csv(handle)


def write_orders_csv(path: Path, orders: Iterable[Order]) -> None:
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "x", "y", "demand"])
        writer.writerows((o.id, o.location.x, o.location.y, o.demand) for o in orders)


def renumber(orders: Iterable[Order]) -> list[Order]:
    """Reassign ids 1..n in order (files may use their own numbering)."""
    return [Order(i, o.location, o.demand) for i, o in enumerate(orders, start=1)]


def merge_orders(batches: Sequence[Sequence[Order]]) -> list[Order]:
    return renumber(chain.from_iterable(batches))


def solution_to_dict(solution: Solution, total_distance: float) -> dict[str, object]:
    return {
        "total_distance": round(total_distance, 4),
        "routes": [list(route) for route in solution.routes],
    }


def write_solution_json(path: Path, solution: Solution, total_distance: float) -> None:
    path.write_text(json.dumps(solution_to_dict(solution, total_distance), indent=2))
