# Testing Strategy

## Operational Validation
SeqQuests uses operational validation:
- Example pipelines verify the underlying modules
- Documentation pipeline produces screenshot images that sanity-check the UI
- CLI can be run independent of web UI and this is mainstream for pipeline use
- Web UI can run (with reduced functionality) with static files, to verify the UI
- Small example data is in the rep (for test); larger data found by configured path, if present; Web UI can pull from uniprot endpoints.

The test strategy is based on being able to routinely run parts of the system independently, rather than a test harness framework to artificially test individual components. In general, code used for test should be load bearing for actual use, so that there is strong incentive to maintain and refine it. 

## Headroom, not Pass/Fail
- Core routines collect memory/speed benchmark data, more actionable than pass/fail

Tests tend to bitrot. Gathering metrics in context gives earlier warning of stressed components and it leads to a more informative test strategy. Meanwhile automated test generation tends to test and re-test what is already known to work, and they make working with the code more cumbersome.

## For AI Helpers
Do not create separate test harnesses or frameworks.
Focus on making examples and tools that have independent value.
Prefer benchmarking and cross-implementation validation over pass/fail testing.

## Performance Validation
- Platform-specific Metal kernel parameters (THREADS, UNROLL) currently tuned manually
- Future: Auto-tuning tool to benchmark kernel variants and find optimal parameters
- Benchmark data should be tracked over time to detect performance regressions

## Architectural Principles
The testing strategy is enabled by [architectural principles](./specs.md):
- Thin web server wrapper enables CLI testing
- Abstraction layers (sequences.py) enable fallback validation
- Separation of concerns reduces need for mocking