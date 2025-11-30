# Technical Debt Report

## Overview
This document outlines the technical debt identified in the SeqQuests project. The debt is categorized by type and prioritized.

## Priority 1: High (Critical/Blocking)

- [ ] **Data Path Hardcoding:**
    - `py/sequences.py` and `py/taxa_lca.py` contain hardcoded paths like `~/BigData/bio_sequence_data`.
    - *Action:* Refactor `get_data_path` to use a configuration file or environment variables (e.g., `SEQQUESTS_DATA_DIR`) with a sane default, rather than hardcoding a specific user's home directory path.

- [ ] **Documentation Drift (CONTENTS.md):**
    - `CONTENTS.md` refers to `c_src/prepare_data.py` but the file is located at `py/prepare_binary_data.py`.
    - `CONTENTS.md` structure section is slightly out of sync with the actual file layout.
    - *Action:* Update `CONTENTS.md` to reflect the current file structure and paths.

- [ ] **Broken/Mixed Test Code:**
    - `py/swiss_to_pdb.py` contains a `test()` function that runs by default if no arguments are provided.
    - `py/sequences.py` contains `test_swiss_index_access`, `verify_sequences`, and `benchmark` functions mixed with core logic.
    - *Action:* Move these "Operational Validation" scripts into the `validation/` directory or a dedicated `tests/` module, keeping the production code clean.

## Priority 2: Medium (Code Quality & Maintainability)

- [ ] **Code Duplication (Tree Builder):**
    - `py/tree_builder.py` and `c_src/tree_builder.cpp` implement the same logic (MST, cycle breaking).
    - *Action:* Validate that the C++ version is fully equivalent (using `py/verify_tree_builder.py`) and consider deprecating the Python implementation for heavy lifting, keeping it only as a wrapper/fallback.

- [ ] **Hardcoded Metal Compiler Logic:**
    - `compile.sh` has logic to detect M1/M2/M3 chips. This is brittle (e.g., M5, Ultra variants).
    - *Action:* Refactor to allow passing `THREADS` and `UNROLL` as environment variables or arguments, using the detection only as a hint/default.

- [ ] **Inline CSS:**
    - `static/lcars.html` contains inline styles.
    - *Action:* Move all styles to `static/style.css` or `static/lcars.css` to maintain separation of concerns.

## Priority 3: Low (Cleanup & Documentation)

- [ ] **Frontend TODOs:**
    - `static/lcars.js` contains a `TODO` regarding server updates for doclist.
    - *Action:* Fix the disconnect between doclist.js and the dynamically created py/web_server.py /Api/docs endpoint. That endpoint should update doclist.js, if it has changed.

- [N/A] **Frontend Markdown Handling:**
    - `static/lcars.js` uses a custom `asHtml` method which is a hacky implementation of Markdown rendering.
    - *Action:* [Not for AI assistant] Import the mature extended markdown system from the monorepo.

- [ ] **Compile Script Defaults:**
    - `compile.sh` defaults `METAL_CPP_PATH` to `$HOME/metal-cpp`. While overridable, this assumes a specific environment.
    - *Action:* Document this prerequisite more clearly in getting_started.md (Already partly done in specs/paths.md).

- [ ] **Global Singleton in Sequences:**
    - `DataManager` in `py/sequences.py` is a thread-safe singleton, but it complicates testing (state persistence).
    - *Action:* Ensure `reset()` is used correctly in all validation scripts.

- [ ] **Magic Constants:**
    - `py/sw_align.py` and `c_src/sw.metal` rely on constants like `THREADS` and `UNROLL`.
    - *Action:* Ensure these match or are passed dynamically to avoid mismatches between host and device code.
