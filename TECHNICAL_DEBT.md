# Technical Debt Report

## Overview
This document outlines the technical debt identified in the SeqQuests project. The debt is categorized by type and prioritized.

## Priority 1: High (Critical/Blocking)

- [ ] **Documentation Drift (CONTENTS.md):**
    - `CONTENTS.md` refers to `c_src/prepare_data.py` but the file is located at `py/prepare_binary_data.py`.
    - `CONTENTS.md` structure section is slightly out of sync with the actual file layout.
    - *Action:* Update `CONTENTS.md` to reflect the current file structure and paths.

- [ ] **Broken Test Code (swiss_to_pdb.py):**
    - `py/swiss_to_pdb.py` contains pseudo-code in its `test()` function (`indices_A = [10, 11, 12, ...]`) which will cause a syntax error or runtime error if executed.
    - *Action:* Fix or remove the broken `test()` function.

## Priority 2: Medium (Code Quality & Maintainability)

- [ ] **Empty Test Stubs:**
    - Many Python modules have a `--test` argument that merely prints a message ("test stub") and performs no validation. This gives a false sense of security.
    - Affected modules: `py/command_runner.py`, `py/sw_align.py`, `py/computation.py`, `py/pam_converter.py`, `py/web_server.py`, `py/sw_search.py`.
    - *Action:* Implement meaningful smoke tests (checking imports, basic function calls) or remove the `--test` argument if `tests/IMPORTANT_tests.py` policy prohibits them.

- [ ] **Tree Builder Test Dependencies:**
    - `py/tree_builder.py` test function relies on `test_links.txt` which may not be present, leading to skipped tests.
    - *Action:* Generate test data programmatically within the test function or ensure test files are versioned.

## Priority 3: Low (Cleanup & Documentation)

- [ ] **Frontend TODOs:**
    - `static/lcars.js` contains a `TODO` regarding server updates for `dcolist`.
    - *Action:* Resolve the server-side requirement or remove the TODO if obsolete.

- [ ] **Frontend Markdown Handling:**
    - `static/lcars.js` uses a custom `asHtml` method which is a hacky implementation of Markdown rendering.
    - *Action:* Evaluate if a lightweight Markdown library is needed or if the current solution is sufficient (and document it).

- [ ] **Compile Script Defaults:**
    - `compile.sh` defaults `METAL_CPP_PATH` to `$HOME/metal-cpp`. While overridable, this assumes a specific environment.
    - *Action:* Document this prerequisite clearly or include `metal-cpp` as a submodule.

## Completed Items (Archived)

The following items were previously identified as technical debt and have been addressed:

- [x] **Project Organization (c_src):** `c_src/prepare_binary_data.py` was moved to `py/prepare_binary_data.py`.
- [x] **Python Package Structure:** `pyproject.toml` has been introduced to manage dependencies and package structure, replacing `PYTHONPATH` hacks.
- [x] **Global State:** `py/sequences.py` refactored to use `DataManager` class instead of global variables.
- [x] **Unused Code:** `dev_sw_search_metal.py` moved to `dev/` directory.
- [x] **Tree Builder Verification:** `validation/verify_tree_builder.py` exists to compare Python and C++ implementations.
