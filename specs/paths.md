# Path Handling Specifications

This document outlines how file paths are handled in the SeqQuests project, specifically regarding the separation of project code, sample data, and large external datasets.

## Core Principle

The project is designed to be portable while supporting large external datasets.
- **Code and Small Data:** Contained within the repository.
- **Large Data:** Stored externally, avoiding repository bloat.

## Data Directory Strategy

The project uses a fallback mechanism for locating data files.

1.  **User Data Directory:** The system first checks for a user-specific data directory.
    It uses env variables, which can be set in .env (and are not stored in git)
    - **Path:** SEQQUESTS_DATA_DIR=~/data/seqquests by default
    - **Usage:** This allows developers to keep Swiss-Prot files outside the source tree.

2.  **Default Data Directory:** If the file is not found in the user directory, the system falls back to the local repository data.
    - **Path:** `./data/` (relative to the project root)
    - **Usage:** This directory contains small sample files (`swissprot.dat.txt`, `swissprot.fasta.txt`) suitable for development, testing, and CI/CD.

### Implementation Details
*   **Python (`py/sequences.py`):** The `get_data_path()` function implements this logic. It maps internal filenames (e.g., `swissprot.fasta.txt`) to external filenames (e.g., `uniprot_sprot.fasta`) if found in the external path.
*   **Python (`py/taxa_lca.py`):** Uses NCBI_TAXONOMY_DB for the taxonomy database, falling back only if not specified via arguments.

## Compiler and Toolchain Paths

External tools and libraries, specifically for Apple Metal development, are also path-dependent.

*   **Metal CPP:** The build script `compile.sh` needs the `metal-cpp` headers.
    *   **Default:** `$HOME/metal-cpp`
    *   **Override:** Set the `METAL_CPP_PATH` environment variable.
    *   **Example:** `export METAL_CPP_PATH=/opt/metal-cpp && ./compile.sh`

## Recommendations for Developers

To configure your environment for "Big Data" development without modifying the code:

1.  **Data Storage:**
    *   Create the directory: `mkdir -p ~/BigData/bio_sequence_data`
    *   Place your full `uniprot_sprot.fasta` and `uniprot_sprot.dat` files there.
    *   The application will automatically prioritize these files over the samples in `./data/`.

2.  **Metal Development:**
    *   Install `metal-cpp` to `~/metal-cpp`.
    *   Alternatively, install it anywhere and set `METAL_CPP_PATH` in your shell profile (e.g., `.zshrc`):
        ```bash
        export METAL_CPP_PATH="/path/to/your/metal-cpp"
        ```

3.  **Path Resolution in Code:**
    *   Always use `pathlib.Path` for path manipulations.
    *   Use `PROJECT_ROOT` (derived from `__file__`) to anchor paths relative to the source code.
    *   Never assume the current working directory (`os.getcwd()`) is the project root.
