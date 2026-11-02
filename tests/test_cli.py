"""Integration / end-to-end: drive the real CLI against real files."""

import json
from pathlib import Path

import pytest

from routeopt.cli import main
from routeopt.registry import Registry


def test_end_to_end_generate_then_solve(tmp_path: Path) -> None:
    orders, out = tmp_path / "orders.csv", tmp_path / "plan.json"
    assert main(["generate", "--n", "25", "--seed", "3", "--out", str(orders)]) == 0
    code = main(["solve", "--orders", str(orders), "--capacity", "30", "--json", str(out)])
    assert code == 0
    plan = json.loads(out.read_text())
    assert sorted(i for r in plan["routes"] for i in r) == list(range(1, 26))
    assert plan["total_distance"] > 0


@pytest.mark.parametrize("solver", ["greedy", "greedy-2opt", "cluster", "exact"])
def test_cli_each_solver(tmp_path: Path, solver: str) -> None:
    orders = tmp_path / "o.csv"
    main(["generate", "--n", "7", "--out", str(orders)])
    assert main(["solve", "--orders", str(orders), "--capacity", "25", "--solver", solver]) == 0


def test_cli_reports_errors(tmp_path: Path) -> None:
    assert main(["solve", "--orders", str(tmp_path / "missing.csv"), "--capacity", "10"]) == 2
    orders = tmp_path / "o.csv"
    main(["generate", "--n", "5", "--out", str(orders)])
    assert main(["solve", "--orders", str(orders), "--capacity", "1"]) == 2  # demand > capacity


def test_cli_benchmark_runs() -> None:
    assert main(["benchmark", "--sizes", "6"]) == 0


def test_registry_rejects_duplicates() -> None:
    reg: Registry[int] = Registry()
    reg.register("a")(lambda: 1)
    with pytest.raises(ValueError):
        reg.register("a")(lambda: 2)
    assert reg.create("a") == 1
