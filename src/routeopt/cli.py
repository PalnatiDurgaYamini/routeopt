"""Command-line interface: generate | solve | benchmark | serve."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from routeopt.benchmark import run_all
from routeopt.distance import build_matrix
from routeopt.fileio import read_orders_csv, renumber, write_orders_csv, write_solution_json
from routeopt.functional import path_length, solution_cost
from routeopt.generator import generate_orders
from routeopt.models import InfeasibleError, Point, Problem
from routeopt.solvers import SOLVERS
from routeopt.utils import Timer


def _point(text: str) -> Point:
    x, y = text.split(",")
    return Point(float(x), float(y))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="routeopt", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="write a random orders CSV")
    gen.add_argument("--n", type=int, default=30)
    gen.add_argument("--seed", type=int, default=0)
    gen.add_argument("--out", type=Path, required=True)

    solve = sub.add_parser("solve", help="plan routes for an orders CSV")
    solve.add_argument("--orders", type=Path, required=True)
    solve.add_argument("--capacity", type=int, required=True)
    solve.add_argument("--depot", type=_point, default=Point(50.0, 50.0), help="x,y")
    solve.add_argument("--solver", choices=SOLVERS.names(), default="cluster")
    solve.add_argument("--workers", type=int, default=1, help="processes (cluster solver)")
    solve.add_argument("--max-vehicles", type=int, default=None)
    solve.add_argument("--json", type=Path, default=None, help="write solution here")

    web = sub.add_parser("serve", help="start the web interface")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=8000)

    bench = sub.add_parser("benchmark", help="performance evaluation")
    bench.add_argument("--sizes", type=int, nargs="+", default=[8, 50, 200])
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "generate":
        write_orders_csv(args.out, generate_orders(args.n, args.seed))
        print(f"wrote {args.n} orders to {args.out}")
        return 0

    if args.command == "serve":
        from routeopt.web import serve

        serve(args.host, args.port)
        return 0

    if args.command == "benchmark":
        print(run_all(args.sizes))
        return 0

    try:
        orders = tuple(renumber(read_orders_csv(args.orders)))
        problem = Problem(args.depot, orders, args.capacity, args.max_vehicles)
        kwargs = {"workers": args.workers} if args.solver == "cluster" else {}
        solver = SOLVERS.create(args.solver, **kwargs)
        with Timer() as timer:
            solution = solver.solve(problem)
    except (InfeasibleError, OSError, KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    matrix = build_matrix(problem)
    total = solution_cost(matrix, solution)
    demand = {o.id: o.demand for o in problem.orders}
    print(
        f"solver={args.solver} routes={len(solution.routes)} "
        f"distance={total:.2f} time={timer.elapsed:.4f}s"
    )
    for i, route in enumerate(solution.routes, start=1):
        stops = " -> ".join(["depot", *map(str, route), "depot"])
        load = sum(demand[j] for j in route)
        print(
            f"  van {i}: {stops}  (load {load}/{problem.capacity}, "
            f"{path_length(matrix, route):.1f})"
        )
    if args.json:
        write_solution_json(args.json, solution, total)
    return 0
