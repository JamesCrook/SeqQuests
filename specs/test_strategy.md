# Testing Strategy

SeqQuests uses operational validation:
- UI serves as integration test
- Example pipelines verify modules
- CLI can be run independent of web UI
- Web UI can run with reduced functionality without the API endpoints to verify UI
- Static file fallback validates API contracts
- No mocking framework; We have fallbacks instead.
- Small example data is in the rep (for test) larger data found by configured path, if present.
- Real workloads (570K sequence runs) stress test the system
- Core routines collect memory/speed benchmark data, more actionable than pass/fail
- Python and C versions of core routines; Python easier to reason about and debug

Do not create separate test harnesses or frameworks.
Focus on making examples and tools that have independent value.

## For LLMs
Do not create separate test harnesses or frameworks.
Focus on making examples and tools that have independent value.
Prefer benchmarking and cross-implementation validation over pass/fail testing.

## Performance Validation
- Platform-specific Metal kernel parameters (THREADS, UNROLL) currently tuned manually
- Future: Auto-tuning tool to benchmark kernel variants and find optimal parameters
- Benchmark data should be tracked over time to detect performance regressions

## Architectural Principles
The testing strategy is enabled by architectural principles in `/specs/specs.md`:
- Thin web server wrapper enables CLI testing
- Abstraction layers (sequences.py) enable fallback validation
- Separation of concerns reduces need for mocking