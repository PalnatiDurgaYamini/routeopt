# Specification (written before code: specification-first development)

## 1. Real-world problem
A local courier has one depot, vans that each carry at most `C` units, and `n` customer orders with a location
and a size. Each morning dispatch must decide which van takes which orders and in what sequence.

## 2. Computational thinking
| Step | Application |
|---|---|
| Decomposition | (a) read orders, (b) measure distances, (c) group orders into van loads, (d) sequence each load, (e) validate and report |
| Pattern recognition | Sequencing one van is the Travelling Salesman Problem; grouping is bin-packing; together CVRP |
| Abstraction | Ignore roads, traffic, driver breaks. Keep points, demands, one capacity, Euclidean distance |
| Algorithm design | Greedy (fast baseline), divide and conquer (grouping), DP (exact order per group), backtracking + branch-and-bound (exact whole problem) |

## 3. Requirements
* **R1** Every order is served exactly once.
* **R2** No route load exceeds capacity `C`.
* **R3** Minimise total distance (depot -> stops -> depot, summed over routes).
* **R4** Invalid input is rejected with a clear error, exit code 2.
* **R5** Solvers are interchangeable through one interface and selectable by name.
* **R6** Results are validated independently of the solver that produced them.

## 4. Architecture
```
cli -> fileio -> models.Problem -> BaseSolver.solve
                                   |- build_matrix (distance)
                                   |- _solve  (greedy | cluster | exact)   <- Strategy
                                   `- validate_solution                    <- R1, R2, R6
cluster -> bisect_clusters -> parallel_map(optimise_cluster) -> held_karp | NN+2-opt
```

## 5. Acceptance tests
| Req | Test |
|---|---|
| R1, R2 | `test_properties.py` (Hypothesis), `test_models.py` |
| R3 | `test_exact_matches_brute_force`, `test_heuristics_never_beat_exact`, Held-Karp vs brute force |
| R4 | `test_cli_reports_errors` |
| R5 | `test_every_solver_returns_valid_solution`, `test_unknown_solver_name` |
| R6 | `test_validate_rejects_bad_solutions` |

## 6. Possible extensions
Time windows, heterogeneous fleet, real road distances via an API (a natural asyncio use case),
Clarke-Wright savings heuristic, stronger branch-and-bound bounds.
