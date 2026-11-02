"""Importing this package registers every solver in SOLVERS."""

from routeopt.solvers import cluster, exact, greedy  # noqa: F401
from routeopt.solvers.base import SOLVERS, BaseSolver
from routeopt.solvers.cluster import ClusterFirstSolver
from routeopt.solvers.exact import BranchAndBoundSolver
from routeopt.solvers.greedy import NearestNeighbourSolver

__all__ = [
    "SOLVERS",
    "BaseSolver",
    "BranchAndBoundSolver",
    "ClusterFirstSolver",
    "NearestNeighbourSolver",
]
