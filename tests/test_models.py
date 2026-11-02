import pytest

from routeopt.models import InfeasibleError, Order, Point, Problem, Solution, validate_solution


def make_problem() -> Problem:
    orders = (Order(1, Point(1, 1), 4), Order(2, Point(2, 2), 5))
    return Problem(Point(0, 0), orders, capacity=8)


def test_point_distance() -> None:
    assert Point(0, 0).distance_to(Point(3, 4)) == pytest.approx(5.0)


@pytest.mark.parametrize("capacity", [0, -3])
def test_capacity_must_be_positive(capacity: int) -> None:
    with pytest.raises(InfeasibleError):
        Problem(Point(0, 0), (), capacity)


def test_ids_must_be_consecutive() -> None:
    with pytest.raises(InfeasibleError):
        Problem(Point(0, 0), (Order(2, Point(1, 1), 1),), 5)


def test_demand_cannot_exceed_capacity() -> None:
    with pytest.raises(InfeasibleError):
        Problem(Point(0, 0), (Order(1, Point(1, 1), 9),), 5)


def test_max_vehicles_positive() -> None:
    with pytest.raises(InfeasibleError):
        Problem(Point(0, 0), (), 5, max_vehicles=0)


def test_validate_accepts_good_solution() -> None:
    validate_solution(make_problem(), Solution(((1,), (2,))))


@pytest.mark.parametrize(
    "routes",
    [((1,),), ((1, 1), (2,)), ((1, 2),), ((1,), (), (2,)), ((1,), (2,), (3,))],
)
def test_validate_rejects_bad_solutions(routes: tuple[tuple[int, ...], ...]) -> None:
    with pytest.raises(InfeasibleError):
        validate_solution(make_problem(), Solution(routes))


def test_validate_rejects_too_many_vehicles() -> None:
    orders = (Order(1, Point(1, 1), 4), Order(2, Point(2, 2), 5))
    problem = Problem(Point(0, 0), orders, capacity=8, max_vehicles=1)
    with pytest.raises(InfeasibleError):
        validate_solution(problem, Solution(((1,), (2,))))
