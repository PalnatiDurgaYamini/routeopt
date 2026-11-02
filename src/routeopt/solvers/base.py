"""Solver abstraction: Template Method + Strategy + Registry.

``BaseSolver.solve`` fixes the workflow (build matrix -> search -> validate);
subclasses only implement ``_solve``. Solvers are interchangeable strategies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from routeopt.distance import Matrix, build_matrix
from routeopt.models import Problem, Solution, validate_solution
from routeopt.registry import Registry
from routeopt.utils import timed


class BaseSolver(ABC):
    name: str = "base"

    @timed
    def solve(self, problem: Problem) -> Solution:
        matrix = build_matrix(problem)
        solution = self._solve(problem, matrix)
        validate_solution(problem, solution)  # never trust a solver's output
        return solution

    @abstractmethod
    def _solve(self, problem: Problem, matrix: Matrix) -> Solution: ...


SOLVERS: Registry[BaseSolver] = Registry()
