"""Distance matrix: precompute once, O(1) lookups afterwards."""

from __future__ import annotations

from collections.abc import Sequence

from routeopt.models import Problem

Matrix = tuple[tuple[float, ...], ...]


def build_matrix(problem: Problem) -> Matrix:
    """Symmetric Euclidean matrix; index 0 = depot, index i = order i.

    Time O(n^2), space O(n^2).
    """
    points = [problem.depot, *(o.location for o in problem.orders)]
    return tuple(tuple(a.distance_to(b) for b in points) for a in points)


def submatrix(matrix: Matrix, indices: Sequence[int]) -> Matrix:
    """Restrict a matrix to the given indices (re-indexed 0..len-1)."""
    return tuple(tuple(matrix[i][j] for j in indices) for i in indices)
