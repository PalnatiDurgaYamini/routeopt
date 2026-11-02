"""Tiny web interface: standard-library HTTP server + one HTML page.

``solve_request`` is a pure function (JSON in, JSON out) so the logic is
testable without a network; the HTTP handler is a thin wrapper around it.
"""

from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from typing import Any

from routeopt.distance import build_matrix
from routeopt.fileio import parse_orders_csv, renumber
from routeopt.functional import path_length
from routeopt.generator import generate_orders
from routeopt.models import Point, Problem
from routeopt.solvers import SOLVERS
from routeopt.utils import Timer

log = logging.getLogger("routeopt.web")
MAX_ORDERS = 500
EXACT_MAX_ORDERS = 10
MAX_BODY_BYTES = 1_000_000


class RequestError(ValueError):
    """The client sent something we cannot solve (becomes HTTP 400)."""


def solve_request(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise RequestError("request body must be a JSON object")
    try:
        name = str(payload.get("solver", "cluster"))
        capacity = int(payload.get("capacity", 30))
        dx, dy = payload.get("depot", [50, 50])
        if payload.get("csv"):
            orders = renumber(parse_orders_csv(str(payload["csv"]).splitlines()))
        else:
            orders = generate_orders(int(payload.get("n", 30)), int(payload.get("seed", 1)))
        if name not in SOLVERS.names():
            raise RequestError(f"unknown solver {name!r}")
        if len(orders) > MAX_ORDERS:
            raise RequestError(f"at most {MAX_ORDERS} orders are allowed")
        if name == "exact" and len(orders) > EXACT_MAX_ORDERS:
            raise RequestError(f"exact solver is limited to {EXACT_MAX_ORDERS} orders")
        problem = Problem(Point(float(dx), float(dy)), tuple(orders), capacity)
        with Timer() as timer:
            solution = SOLVERS.create(name).solve(problem)
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        if isinstance(exc, RequestError):
            raise
        raise RequestError(str(exc)) from exc

    matrix = build_matrix(problem)
    demand = {o.id: o.demand for o in problem.orders}
    return {
        "solver": name,
        "capacity": capacity,
        "depot": [problem.depot.x, problem.depot.y],
        "orders": [
            {"id": o.id, "x": o.location.x, "y": o.location.y, "demand": o.demand}
            for o in problem.orders
        ],
        "routes": [list(r) for r in solution.routes],
        "loads": [sum(demand[i] for i in r) for r in solution.routes],
        "lengths": [round(path_length(matrix, r), 2) for r in solution.routes],
        "distance": round(sum(path_length(matrix, r) for r in solution.routes), 2),
        "seconds": round(timer.elapsed, 4),
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, data: dict[str, Any]) -> None:
        self._send(status, json.dumps(data).encode(), "application/json")

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            page = resources.files("routeopt").joinpath("static/index.html").read_bytes()
            self._send(200, page, "text/html; charset=utf-8")
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/api/solve":
            self._json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        if length > MAX_BODY_BYTES:
            self._json(413, {"error": "request too large"})
            return
        try:
            self._json(200, solve_request(json.loads(self.rfile.read(length) or b"{}")))
        except (json.JSONDecodeError, RequestError) as exc:
            self._json(400, {"error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        log.info(format, *args)


def make_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), Handler)


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = make_server(host, port)
    print(f"routeopt web interface: http://{host}:{port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()
