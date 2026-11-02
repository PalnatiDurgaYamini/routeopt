# routeopt: Delivery Route Optimizer

A small delivery business has one depot, identical vans with a fixed load capacity, and a list of customer
orders. **Goal: serve every order exactly once while minimising total distance driven.**
This is the *Capacitated Vehicle Routing Problem* (CVRP), which is NP-hard, so the project compares
exact and heuristic strategies and shows where each one wins.

## Quick start

```bash
pip install -e ".[dev]"           # Python 3.11+
routeopt generate --n 40 --seed 1 --out orders.csv
routeopt solve --orders orders.csv --capacity 30 --solver cluster --workers 2
routeopt benchmark                # performance evaluation
make check                        # ruff + mypy + pytest with coverage

docker build -t routeopt .
docker run --rm -v "$PWD":/data routeopt solve --orders orders.csv --capacity 30
```

## Web interface

```bash
routeopt serve                  # then open http://127.0.0.1:8000
docker run --rm -p 8000:8000 routeopt serve --host 0.0.0.0
```
Generate random orders or upload a CSV (`id,x,y,demand`), pick a solver, see each van's route drawn on a
map, and use **Compare all solvers** for a side-by-side table (click a row to redraw that plan).
Built with only the standard library (`http.server`) plus one HTML page; all logic lives in the pure
function `web.solve_request`, which is unit-tested without a network.

Solvers (`--solver`): `greedy`, `greedy-2opt`, `cluster`, `exact` (exact is practical up to about 10 orders).

## Workflow to rubric map

| Rubric stage | Where |
|---|---|
| Problem identification, decomposition | `docs/SPEC.md` |
| Abstraction | `models.py` (Point, Order, Problem, Solution) |
| Greedy | `solvers/greedy.py` nearest-neighbour |
| Divide and conquer | `solvers/cluster.py` `bisect_clusters` |
| Dynamic programming | `dp.py` Held-Karp |
| Backtracking + branch-and-bound | `solvers/exact.py` |
| Data structures | matrix (tuple of tuples), sets, dicts, bitmasks, heap-free DFS |
| Iterators, generators, comprehensions | `fileio.read_orders_csv`, `utils.batched`, matrix builders |
| Decorators, context managers | `utils.timed`, `utils.Timer`, `Registry.register` |
| OOP, patterns, generics | `BaseSolver` (Template Method), Strategy, `Registry[T]` (Factory) |
| Functional | `functional.py` pure functions, `compose`, `reduce`, `map` |
| Concurrency | `concurrency.py` processes (CPU) and asyncio/threads (I/O) |
| Testing | `tests/` unit, property-based (Hypothesis), integration/e2e (CLI) |
| Quality tooling | ruff, mypy `--strict`, pytest-cov, GitHub Actions |
| Containerisation | `Dockerfile`, CI docker job |
| AI-assisted engineering | `docs/AI_LOG.md` |

## Complexity summary

| Component | Time | Space | Notes |
|---|---|---|---|
| Distance matrix | O(n²) | O(n²) | built once |
| Nearest neighbour | O(n²) | O(n) | greedy, no optimality guarantee |
| 2-opt polish | O(k³) per pass | O(k) | k = stops on one route |
| `bisect_clusters` | O(n log² n) | O(n) | T(n)=2T(n/2)+O(n log n) |
| Held-Karp (per cluster) | O(k²·2ᵏ) | O(k·2ᵏ) | vs O(k!) brute force |
| Branch and bound | O(n!) worst case | O(n) | pruning makes n ≲ 10 practical |

Amortized: `set.remove` and `list.append` are amortized O(1). Expected: hash-based `set`/`dict` lookups are
expected O(1).

## Concurrency choices

* **CPU-bound** (Held-Karp on many clusters): `ProcessPoolExecutor`, because threads would serialise on the GIL.
  Only pays off when each job is heavy; for tiny jobs process start-up costs more than it saves
  (`parallel_map` falls back to a loop for one worker).
* **I/O-bound** (loading many order sources): `asyncio` + `to_thread` (or a thread pool). The GIL is released
  while waiting, so waits overlap. Expect roughly `files x` speed-up over sequential loading.

## Known limitations (say these in the defence)

* Cluster solver optimises route *order* well but its clusters are only about half full, so it uses more vans
  than greedy. At large n greedy can travel less; at mid n clustering wins. The benchmark shows both.
* Branch-and-bound uses a simple lower bound (cheapest entering edge); stronger bounds (1-trees, LP) would
  scale further.
* Straight-line distances, identical vans, no time windows. Natural extensions listed in `docs/SPEC.md`.
