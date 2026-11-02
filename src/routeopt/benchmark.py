"""Performance evaluation: solver quality/time, CPU scaling, I/O scaling."""

from __future__ import annotations

import asyncio
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from routeopt.concurrency import fetch_orders, thread_map
from routeopt.distance import build_matrix
from routeopt.fileio import read_orders_csv, write_orders_csv
from routeopt.functional import solution_cost
from routeopt.generator import generate_orders, generate_problem
from routeopt.models import Problem
from routeopt.solvers import SOLVERS, ClusterFirstSolver
from routeopt.utils import Timer

EXACT_MAX_N = 9


@dataclass(frozen=True, slots=True)
class Row:
    solver: str
    n: int
    routes: int
    distance: float
    seconds: float


def compare_solvers(sizes: Sequence[int], seed: int = 1, capacity: int = 30) -> list[Row]:
    rows: list[Row] = []
    for n in sizes:
        problem = generate_problem(n, seed=seed, capacity=capacity)
        matrix = build_matrix(problem)
        for name in SOLVERS.names():
            if name == "exact" and n > EXACT_MAX_N:
                continue
            solver = SOLVERS.create(name)
            with Timer() as t:
                solution = solver.solve(problem)
            rows.append(
                Row(name, n, len(solution.routes), solution_cost(matrix, solution), t.elapsed)
            )
    return rows


def format_table(rows: Sequence[Row]) -> str:
    lines = [f"{'solver':<13}{'n':>5}{'routes':>8}{'distance':>11}{'seconds':>10}"]
    lines += [
        f"{r.solver:<13}{r.n:>5}{r.routes:>8}{r.distance:>11.1f}{r.seconds:>10.4f}" for r in rows
    ]
    return "\n".join(lines)


def cpu_scaling(
    n: int = 120, workers: Sequence[int] = (1, 2, 4), exact_limit: int = 16
) -> list[tuple[int, float]]:
    """CPU-bound: same problem, growing process count.

    Small demands and a large van give ~15-stop clusters; exact Held-Karp on each
    is heavy (~0.3 s), so extra processes can pay for their start-up cost.
    Speed-up is capped by the machine's core count.
    """
    problem: Problem = generate_problem(n, seed=3, capacity=40, max_demand=2)
    results = []
    for w in workers:
        solver = ClusterFirstSolver(exact_limit=exact_limit, workers=w)
        with Timer() as t:
            solver.solve(problem)
        results.append((w, t.elapsed))
    return results


def io_scaling(files: int = 8, latency: float = 0.05) -> dict[str, float]:
    """I/O-bound: sequential vs threads vs asyncio over slow sources."""
    import time

    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for i in range(files):
            path = Path(tmp) / f"orders_{i}.csv"
            write_orders_csv(path, generate_orders(20, seed=i))
            paths.append(path)

        def slow_read(path: Path) -> int:
            time.sleep(latency)  # simulated network delay
            return len(list(read_orders_csv(path)))

        out: dict[str, float] = {}
        with Timer() as t:
            [slow_read(p) for p in paths]
        out["sequential"] = t.elapsed
        with Timer() as t:
            thread_map(slow_read, paths, workers=files)
        out["threads"] = t.elapsed
        with Timer() as t:
            asyncio.run(fetch_orders(paths, concurrency=files, latency=latency))
        out["asyncio"] = t.elapsed
        return out


def run_all(sizes: Sequence[int]) -> str:
    parts = ["== Solver comparison ==", format_table(compare_solvers(sizes))]
    parts.append("\n== CPU-bound scaling (processes) ==")
    base = None
    for w, secs in cpu_scaling():
        base = base or secs
        parts.append(f"workers={w}: {secs:.3f}s  speed-up x{base / secs:.2f}")
    parts.append("\n== I/O-bound loading ==")
    parts += [f"{name:<11}{secs:.3f}s" for name, secs in io_scaling().items()]
    return "\n".join(parts)
