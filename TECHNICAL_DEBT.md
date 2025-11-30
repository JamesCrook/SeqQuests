# Technical Debt Report

## Overview
This document outlines the technical debt identified in the SeqQuests project. The debt is categorized by type and prioritized.

## Priority 1: High (Critical/Blocking)

- [ ] **Documentation Drift (CONTENTS.md):**
    - `CONTENTS.md` refers to `c_src/prepare_data.py` but the file is located at `py/prepare_binary_data.py`.
    - `CONTENTS.md` structure section is slightly out of sync with the actual file layout.
    - *Action:* Update `CONTENTS.md` to reflect the current file structure and paths.

## Priority 2: Medium (Code Quality & Maintainability)

## Priority 3: Low (Cleanup & Documentation)

- [ ] **Frontend TODOs:**
    - `static/lcars.js` contains a `TODO` regarding server updates for doclist.
    - *Action:* Fix the disconnect between doclist.js and the dynamically created py/web_server.py /Api/docs endpoint. That endpoint should update doclist.js, if it has changed.

- [N/A] **Frontend Markdown Handling:**
    - `static/lcars.js` uses a custom `asHtml` method which is a hacky implementation of Markdown rendering.
    - *Action:* [Not for AI assistant] Import the mature extended markdown system from the monorepo.

- [ ] **Compile Script Defaults:**
    - `compile.sh` defaults `METAL_CPP_PATH` to `$HOME/metal-cpp`. While overridable, this assumes a specific environment.
    - *Action:* Document this prerequisite more clearly in getting_started.md

