# Technical Debt Report

## Overview
This document outlines the technical debt identified in the SeqQuests project. The debt is categorized by type and prioritized.

## Priority 2: Medium (Cleanup & Documentation)

- [ ] **Compile Script Defaults:**
    - `compile.sh` defaults `METAL_CPP_PATH` to `$HOME/metal-cpp`. While overridable, this assumes a specific environment.
    - *Action:* This may have been addressed. Check the instructions in getting_started.md. 

- [ ] **Global Singleton in Sequences:**
    - `DataManager` in `py/sequences.py` is a thread-safe singleton, but it complicates testing (state persistence).
    - *Action:* Ensure `reset()` is used correctly in all validation scripts. It may actually be correct to use reset() rarely, so as to check the cache is behaving correctly. May need a comment in the relevant test code.

- [ ] **Magic Constants:**
    - `py/sw_align.py` and `c_src/sw.metal` rely on constants like `THREADS` and `UNROLL`.
    - *Action:* Ensure these match or are passed dynamically to avoid mismatches between host and device code. Note that they ultimately come from compile.sh

- [ ] **Clunky Indexing Step:**
    - The current code for creating indexed protein data, sorted by size descending, and easily binary readable amino acid similarity tables is clunky. For example it reads and indexes from the FastA format derived data rather than using the 'single source of truth' SwissProt file. The preparation needs to be organised to handle more choices of similarity tables, and choice of database, e.g. local database or collection of epitopes vs SwissProt in both all-on-all and database vs database mode.
