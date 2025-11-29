# Technical Debt Report

## Overview
This document outlines the technical debt identified in the SeqQuests project. The debt is categorized by type and prioritized.

## Priority 1: High (Critical/Blocking)

- [ ] **Dependency Management (Metal):** `compile.sh` hardcodes the path to `metal-cpp` as `$HOME/metal-cpp`. This breaks the build for any user who doesn't have this exact directory structure.
    - *Action:* Make the path configurable via environment variable or include `metal-cpp` as a submodule/vendor directory.
- [ ] **Python Package Structure:** The project relies on manually setting `PYTHONPATH=py`. This is fragile and non-standard.
    - *Action:* Create a `pyproject.toml` or `setup.py` to make the package installable (e.g., `pip install -e .`).
- [ ] **Inconsistent Requirements:** `REQUIREMENTS.txt` and `REQUIREMENTS_METAL.txt` exist. It is unclear if they are synced or mutually exclusive.
    - *Action:* Consolidate into `pyproject.toml` with optional groups (e.g., `[project.optional-dependencies] metal = [...]`).

## Priority 2: Medium (Code Quality & Maintainability)

- [ ] **Project Organization (c_src):** `c_src/prepare_binary_data.py` is a Python script located in the C source directory. It imports from the parent directory using `sys.path` manipulation.
    - *Action:* Move this script to `py/` or a `tools/` directory and use proper relative imports.
- [ ] **Frontend Separation of Concerns:** `static/lcars.html` contains a large block of inline CSS and JavaScript. This violates the project's own guidelines.
    - *Action:* Extract CSS to `static/lcars.css` (or merge into `style.css`) and JS to `static/lcars_ui.js`.
- [ ] **Code Duplication (Tree Builder):** There are parallel implementations of the Tree Builder in Python (`py/tree_builder.py`) and C++ (`c_src/tree_builder.cpp`).
    - *Action:* Establish a strict verification test that runs both on the same data and asserts identical output to prevent logic drift.
- [ ] **Global State:** `py/sequences.py` uses a global variable `_swissprot_cache` which persists state. This makes unit testing difficult and prone to side effects.
    - *Action:* Refactor to use a class-based approach or dependency injection for the cache.

## Priority 3: Low (Cleanup & Documentation)

- [ ] **Unused Code:** `py/dev_sw_search_metal.py` appears to be a development artifact.
    - *Action:* Delete or move to a `dev/` or `archive/` directory.
- [ ] **Ad-hoc Testing:** Tests are scattered as `verify_*.py` and `check_*.py` scripts.
    - *Action:* Consolidate these into a `tests/` directory and consider using `pytest` to run them standardly.
- [ ] **Hardcoded Paths in Compile Script:** `compile.sh` has logic for specific Apple Silicon chips but defaults to M1. It lacks flexibility for other architectures or manual overrides.
    - *Action:* Allow command-line arguments to override `THREADS` and `UNROLL`.

## Priority 4: Documentation

- [ ] **Missing API Docs:** While `fastapi` provides auto-docs, there is no explicit documentation for the internal Python API (e.g., `job_manager` classes).
- [ ] **Testing Strategy:** `specs/test_strategy.md` exists but the actual tests are bespoke scripts. The docs should align with the reality or vice versa.
