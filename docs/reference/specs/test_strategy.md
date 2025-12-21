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
- Playwright scripts to generate images for the documentation test/validates the web user-interface

Modules
- Python modules are additionally argparse functionality, so that they can be used from command line
- Python modules under development may have a --test option, possibly as the default, serving as a quick 'smoke test', i.e checks imports work and 

Do not create separate test harnesses or frameworks.
Focus on making examples and tools that have independent value.

## For AI
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