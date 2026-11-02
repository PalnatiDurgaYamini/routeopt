# Technical defence: likely questions and where the answers live

**Why is this problem hard?** CVRP is NP-hard: the number of route plans grows factorially. Exact search is
only feasible for about 10 orders, so heuristics are needed at scale.

**Why four solvers?** They show the trade-off curve: greedy (fastest, roughest), greedy + 2-opt (cheap
improvement), cluster (divide and conquer + exact DP per route, parallelisable), branch-and-bound (optimal,
slow). The exact solver is also the oracle that shows how far the heuristics are from optimal.

**Where is dynamic programming?** `dp.held_karp`: subproblem = (set of visited stops, last stop), with
overlapping subproblems. O(k²2ᵏ) instead of O(k!).

**Why is the branch-and-bound bound valid?** Every unvisited order must be entered by exactly one edge, and
each such edge costs at least that order's cheapest incoming edge. Summing those, plus the final return to
the depot, never exceeds the true remaining cost. So pruning never discards the optimum. (Verified against
brute force in `test_exact_matches_brute_force`.)

**Why processes and not threads for optimisation?** The work is pure-Python CPU-bound, so the GIL lets only
one thread run bytecode at a time. Processes each have their own interpreter and GIL. For file loading the
threads spend their time waiting, and the GIL is released while waiting, so threads/asyncio are enough and
cheaper.

**Why is parallel speed-up sometimes below 1?** Process start-up and pickling cost more than tiny jobs save.
`parallel_map` avoids the pool for one worker or one job; the benchmark uses heavy jobs to show real gains.

**Which design patterns and why?** Template Method (`BaseSolver.solve` fixes build -> solve -> validate),
Strategy (interchangeable solvers), Factory/Registry (`Registry[T]`, generic), decorators for cross-cutting
timing.

**Where is functional programming?** `functional.py`: pure functions on immutable tuples, `compose` built
with `reduce`, `map` in cost calculation, `partial` to specialise functions for workers.

**How do you know it is correct?** Unit tests, brute-force oracles, Hypothesis properties (every order once,
capacity respected, exact <= heuristics, 2-opt never worsens), end-to-end CLI tests, and a validator that
checks every returned solution.

**Weaknesses?** See README "Known limitations".

**How did you use AI responsibly?** See `docs/AI_LOG.md`.
