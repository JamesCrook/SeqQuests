# Getting Started

## 1. Prerequisites
*   macOS (for Metal acceleration) - *Optional if only using Python/C++ fallback components*
*   Python 3.8+
*   C++ Compiler (Clang/GCC) with C++17 support

## 1a. Apple Metal (Required for speed)
For accelerated Smith-Waterman searches on Apple Silicon (M1/M2/M3/M4):
*   **Xcode Command Line Tools:** Ensure `clang` and `xcrun` are available.
*   **metal-cpp:** The project expects the `metal-cpp` headers to be located at `$HOME/metal-cpp` or METAL_CPP_PATH to be defined. You can download the headers from the [Apple Developer website](https://developer.apple.com/metal/cpp/).

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
    *Note: This requires `metal-cpp` to be available, see prerequisites 1a*

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
    python validation/check_fasta_integrity.py
    ```

## 5. Development
*   Tests are embedded in the modules. Run with `--test` flag or use specific verification scripts (e.g., `validation/verify_tree_builder.py`).
*   Frontend files are in `static/`.
*   Python source is in `py/`.
