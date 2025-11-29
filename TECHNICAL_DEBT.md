# Technical Debt Report

## Overview
This document outlines the technical debt identified in the SeqQuests project. The debt is categorized by type and prioritized.

## Priority 1: High (Critical/Blocking)

- [x] **Dependency Management (Metal):** `compile.sh` hardcodes the path to `metal-cpp` as `$HOME/metal-cpp`. This breaks the build for any user who doesn't have this exact directory structure.
    - *Action:* Make the path configurable via environment variable or include `metal-cpp` as a submodule/vendor directory.
- [ ] **Python Package Structure:** The project used to rely on manually setting `PYTHONPATH=py`. This is fragile and non-standard. Now it has a .toml file.
    - *Action:* Check this is implemented correctly and that there aren't unneeded remnants of the old system.

## Priority 2: Medium (Code Quality & Maintainability)

- [x] **Project Organization (c_src):** `c_src/prepare_binary_data.py` is a Python script located in the C source directory. It imports from the parent directory using `sys.path` manipulation.
    - *Action:* Move this script to `py/` directory and use proper relative imports.
- [x] **Frontend Separation of Concerns:** `static/lcars.html` contains a large block of inline CSS and JavaScript. This violates the project's own guidelines.
    - *Action:* Extract CSS to `static/lcars.css` and JS to `static/lcars_ui.js`.
- [ ] **Code Duplication (Tree Builder):** There are parallel implementations of the Tree Builder in Python (`py/tree_builder.py`) and C++ (`c_src/tree_builder.cpp`).
    - *Action:* Establish a strict verification test that runs both on the same data and asserts identical output to prevent logic drift. verify_tree_builder.py may be a useful starting point.
- [ ] **Global State:** `py/sequences.py` uses a global variable `_swissprot_cache` which persists state. This makes unit testing difficult and prone to side effects.
    - *Action:* Refactor to use a class-based approach or dependency injection for the cache.

## Priority 3: Low (Cleanup & Documentation)

- [ ] **Unused Code:** `py/dev_sw_search_metal.py` is a development artifact, yet still useful for development.
    - *Action:* Move to a `dev/` directory and update the tree in README.txt
- [x] **Hardcoded Paths in Compile Script:** `compile.sh` has logic for specific Apple Silicon chips but defaults to M1. It lacks flexibility for other architectures or manual overrides.
    - *Action:* Allow command-line arguments to override `THREADS` and `UNROLL`.

## Priority 4: Documentation

- [ ] **Missing API Docs:** While `fastapi` provides auto-docs, there is no explicit documentation for the internal Python API (e.g., `job_manager` classes).
