# pandas GH#66522 — Independent validation by KIRA Ω

This directory records an independent reproduction and validation of pandas issue GH#66522: `DataFrame.ewm(...).online().mean()` ignored exponential decay for one-column DataFrames.

## Important status

The upstream implementation was already submitted by another contributor in pandas PR #66541 before this package could be published. This repository does **not** claim authorship of that pull request or its implementation. It preserves the independently produced analysis, regression tests, patch candidate, and local validation evidence requested by Arisnachy Gómez Díaz.

- Upstream issue: https://github.com/pandas-dev/pandas/issues/66522
- Existing upstream PR: https://github.com/pandas-dev/pandas/pull/66541
- GitHub account: https://github.com/arisnachy

## Independent findings

Two dimension mistakes caused the defect:

1. `update_deltas` was sized from the number of columns rather than the number of observations passed to the online kernel.
2. `online_ewma` selected a temporal delta using the column index `j` instead of the row index `i`.

## Executed validation

Environment:

```text
Python 3.13.5
pandas 2.2.3
NumPy 2.3.5
Numba 0.65.1
Linux x86-64
```

Results:

```text
Regression tests against original code: 5 failed as expected
Regression tests after correction:       5 passed
Related smoke tests:                      3 passed
Selected existing tests:                  6 passed
Syntax compilation:                       passed
```

The executable validation was performed on pandas 2.2.3, whose affected implementation matched the faulty path inspected on current `main`. The patch context was checked against current upstream files, but a complete current-main test suite was not executed in the available environment.

## Files

- `pandas-main-GH66522.patch` — candidate patch generated from inspected upstream contexts.
- `MISSION_REPORT.md` — detailed reproduction, cause analysis, evidence, limitations, and regression risk.
- `test_issue_66522_regression.py` — independent regression tests.

## AI disclosure

This investigation and repository update were produced with OpenAI Codex/ChatGPT assistance at the explicit request of Arisnachy Gómez Díaz. Results and limitations are documented rather than presented as unverified human-only work.
