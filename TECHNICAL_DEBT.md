# Technical Debt Report

## Overview
This document outlines the technical debt identified in the SeqQuests project. The debt is categorized by type and prioritized.

## Priority 1: High (Critical/Blocking)

- [x] **Data Path Hardcoding:**
    - `py/sequences.py` and `py/taxa_lca.py` contain hardcoded paths like `~/BigData/bio_sequence_data`.
    - *Action:* Check that this is now fixed

- [ ] **Documentation Drift (CONTENTS.md):**
    - `CONTENTS.md` refers to `c_src/prepare_data.py` but the file is located at `py/prepare_binary_data.py`.
    - `CONTENTS.md` structure section is slightly out of sync with the actual file layout.
    - *Action:* Update `CONTENTS.md` to reflect the current file structure and paths.

- [x] **Test Code:**
    - `py/sequences.py` contains `test_swiss_index_access` and `benchmark` functions mixed with core logic.
    - *Action:* This is OK per policy.

## Priority 2: Medium (Code Quality & Maintainability)

- [ ] **Code Duplication (Tree Builder):**
    - `py/tree_builder.py` and `c_src/tree_builder.cpp` implement the same logic (MST, cycle breaking).
    - *Action:* Validate that the C++ version is fully equivalent (using `py/verify_tree_builder.py`). Document the python version's role better - as a wrapper and as a python reference implementation. 

- [ ] **Hardcoded Metal Compiler Logic:**
    - `compile.sh` has logic to detect M1/M2/M3 chips. This is brittle (e.g., M5, Ultra variants).
    - *Action:* Refactor to allow passing `THREADS` and `UNROLL` as environment variables or arguments, using the detection only as a hint/default.

## Priority 3: Low (Cleanup & Documentation)

- [ ] **Frontend TODOs:**
    - `static/lcars.js` contains a `TODO` regarding server updates for doclist.
    - *Action:* The is actually in web_server.py. Fix the disconnect between doclist.js and the dynamically created py/web_server.py /Api/docs endpoint. That endpoint should update doclist.js, if it has changed. lcars.js should ask for ./docs/doclist.js and web_server.py should intercept it. That way the doclist will be used when the API is unavailable.

- [ ] **Compile Script Defaults:**
    - `compile.sh` defaults `METAL_CPP_PATH` to `$HOME/metal-cpp`. While overridable, this assumes a specific environment.
    - *Action:* This may have been addressed. Check the instructions in getting_started.md. 

- [ ] **Global Singleton in Sequences:**
    - `DataManager` in `py/sequences.py` is a thread-safe singleton, but it complicates testing (state persistence).
    - *Action:* Ensure `reset()` is used correctly in all validation scripts. It may actually be correct to use reset() rarely, so as to check the cache is behaving correctly. May need a comment in the relevant test code.

- [ ] **Magic Constants:**
    - `py/sw_align.py` and `c_src/sw.metal` rely on constants like `THREADS` and `UNROLL`.
    - *Action:* Ensure these match or are passed dynamically to avoid mismatches between host and device code. Note that they ultimately come from compile.sh
