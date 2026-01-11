# Technical Debt Report

## Overview
This document outlines the technical debt identified in the SeqQuests project. The debt is categorized by type and prioritized.

## Priority 2: Medium (Cleanup & Documentation)

- [ ] **Clunky Indexing Step:**
    - The current code for creating indexed protein data, sorted by size descending, and easily binary readable amino acid similarity tables is clunky. For example it reads and indexes from the FastA format derived data rather than using the 'single source of truth' Swiss-Prot file. The preparation needs to be organised to handle more choices of similarity tables, and choice of database, e.g. local database or collection of epitopes vs Swiss-Prot in both all-on-all and database vs database mode.
