# AI-assisted development log

Fill this in honestly as you work. Examiners look for *critical review*, not for the absence of AI.

## Workflow used
1. **Specification first**: wrote `docs/SPEC.md` (requirements + acceptance tests) before asking for code.
2. **Context management**: gave the AI the spec, the module layout and the rubric, one module at a time.
3. **Generate small**: one module per prompt (models -> distance -> solvers -> concurrency -> CLI).
4. **Validate independently**: brute-force oracles in `tests/helpers.py` do not share code with the solvers.
5. **Review** using the checklist below, then record what you changed.

## Review checklist for AI-generated code
- [ ] Do I understand every line well enough to explain it in the defence?
- [ ] Is the algorithm's complexity what the docstring claims? (measure it with `routeopt benchmark`)
- [ ] Is the branch-and-bound bound *admissible* (never overestimates)? Test against brute force.
- [ ] Are edge cases handled: 0 orders, 1 order, demand == capacity, ties in distance?
- [ ] Is anything mutated that should be immutable? Any shared state passed to worker processes?
- [ ] Do type hints pass `mypy --strict`? Does `ruff` pass?
- [ ] Do the tests actually fail when the code is broken? (temporarily break a solver and check)

## Prompt / decision / outcome log (replace these rows with your own)
| # | Prompt (short) | AI output | What I checked | What I changed and why |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

## Limitations of AI assistance I observed
(e.g. plausible but wrong complexity claims, missing edge cases, over-engineered abstractions)
