# Getting Started

## 1. Prerequisites
*   macOS (for Metal acceleration) - *Optional if only using Python/C++ fallback components*
*   Python 3.8+
*   C++ Compiler (Clang/GCC) with C++17 support

## 2. Installation
1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -e .
    ```
    (Dependencies are managed via `pyproject.toml`)

3.  Compile the C++/Metal components:
    ```bash
    ./compile.sh
    ```
    *Note: This requires `metal-cpp` to be available. See `TECHNICAL_DEBT.md` if you encounter path issues.*

## 3. Running the Server
Start the web dashboard to manage jobs:
```bash
python py/web_server.py
```
Access the dashboard at `http://localhost:8000`.

## 4. Running Tools via CLI
You can also run individual tools directly. Ensure you are in the project root.

*   **Prepare Binary Data (Required for SW Search):**
    ```bash
    python py/prepare_binary_data.py
    ```

*   **Tree Builder:**
    ```bash
    python py/tree_builder.py --help
    ```

*   **Data Integrity Check:**
    ```bash
    python py/check_fasta_integrity.py
    ```

## 5. Development
*   Tests are embedded in the modules. Run with `--test` flag or use specific verification scripts (e.g., `py/verify_tree_builder.py`).
*   Frontend files are in `static/`.
*   Python source is in `py/`.
