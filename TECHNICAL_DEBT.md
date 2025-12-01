# Technical Debt Report

## Overview
This document outlines the technical debt identified in the SeqQuests project. The debt is categorized by type and prioritized.

## Priority 2: Medium (Cleanup & Documentation)

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
