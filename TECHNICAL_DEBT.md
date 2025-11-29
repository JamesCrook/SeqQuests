# Technical Debt Report

## Prioritised Action Items

### High Priority
- [ ] **Create Missing UI Tests:** `py/test_ui.py` is referenced in project knowledge as a critical component for verifying frontend changes but is missing from the codebase.
- [ ] **Fix Broken Tree Builder Test:** `py/test_tree_builder.py` fails because it relies on a missing file `test_links2.txt`. The test should be updated to use a generated temporary file or the missing file should be restored.
- [ ] **Remove Unused Dependencies:** `REQUIREMENTS.txt` lists `torch`, but a grep of the codebase confirms it is unused. This increases the installation footprint unnecessarily.
- [ ] **Fix Hardcoded User Paths:** `py/sequences.py` contains a hardcoded path `/Users/jamescrook/BigData/bio_sequence_data`. This should be replaced with a configuration variable or an environment variable check.

### Medium Priority
- [ ] **Consolidate Tests:** Tests are currently scattered across `py/`, `test/`, and `metal/`. Moving them to a dedicated `tests/` directory would improve organization and discoverability.
- [ ] **Resolve Obsolete Code:** The `metal/` directory is marked as obsolete, but `metal/metal_sw.py` contains a Python reference implementation (`sw_step`) used by `py/test_sw_comparison.py`. This code should be moved to a `tests/reference/` or `py/` module, and the `metal/` directory should be removed to avoid confusion with the active `c_src/` implementation.
- [ ] **Rename/Fix Data Integrity Script:** Project knowledge refers to `py/test_data_integrity.py`, but the file is actually `py/check_fasta_data.py`. Standardizing the name would reduce confusion.
- [ ] **Clean Up Deprecated Methods:** `py/sequences.py` contains a deprecated method `iter_sequences` that should be removed or updated.

### Low Priority
- [ ] **Improve Compilation Script:** `compile.sh` uses manual `if-elif` blocks for Apple Silicon chip detection (M1, M2, M3, M4). This is fragile and will require constant updates. It should be refactored to be more generic or feature-based.
- [ ] **Refactor Frontend Script Execution:** `static/lcars.js` uses a manual script execution method (`executeScripts`) for loaded partials. While functional for this local tool, it is a non-standard pattern that could be improved by using a lightweight framework or a more robust loading mechanism.
- [ ] **Legacy Frontend Code:** `static/job_monitor.js` contains fallback code for `iframe` usage (`parent.apiCall`), which appears to be legacy since the move to `lcars.js` partials.

## Detailed Analysis

### 1. Testing Gaps & Organization
The testing strategy is currently fragmented. The user prefers avoiding standard frameworks (like `pytest`), relying on standalone scripts (`if __name__ == "__main__": test_...()`). However, critical tests like `test_ui.py` are missing entirely. The existing tests are scattered:
*   `py/test_sw_comparison.py` (Tests SW logic)
*   `py/test_tree_builder.py` (Broken, missing dependency)
*   `metal/test_metal_exists.py` (Checks for Metal support)
*   `test/test_data_munger.py` (Tests data munging)

### 2. Dependency Management
`biopython` is a core dependency and is correctly listed. However, `torch` is listed in `REQUIREMENTS.txt` but not imported or used anywhere in the python source files.

### 3. Architecture & Code Quality
*   **Hardcoded Paths:** `py/sequences.py` has a specific user's home directory path, which limits portability.
*   **Obsolete Directory:** The `metal/` directory exists alongside `c_src/`, but `c_src/` contains the active C++/Metal implementation. The `metal/` directory is described as "obsolete" in its own docstrings but is still relied upon by tests.
*   **Frontend:** The frontend uses vanilla JavaScript with a custom "partials" loading system (`lcars.js`). While simple and effective for this use case, `lcars.js`'s `executeScripts` method (manually `eval`-ing scripts) is a potential maintenance headache.
