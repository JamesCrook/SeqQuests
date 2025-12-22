# Getting Started

This is a condensed versions of /docs/tutorials/getting-started.md

## 1. Prerequisites
*   macOS (for Metal acceleration)
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

3.  Copy .env.example to .env and customise it for where you want/expect files
    See the comments in the file for what the paths are for.

4.  (Optional) Compile the C++/Metal components:
    ```bash
    ./compile.sh
    ```
    *Note: This requires `metal-cpp` to be available, see prerequisites 1a*
    If you skip the compilation step, everything will be done in python and will
    be very slow, so although 'optional' a lot is lost by skipping this step.

5. (Optional) Install the Uniprot protein data files.
    ```bash
    ./get_uniprot.sh
    ```
    Although this step is 'optional', the cross referencing of results to 
    datafiles requires these, as does search, so SeqQuest will be limping along
    without this step. 

## 3. Running the Server
Start the web dashboard to manage jobs:
```bash
python py/web_server.py
```
Access the dashboard at `http://localhost:8006`.

## 4. Running Tools via CLI

SeqQuest is built on top of command line tools. See /docs/tutorials/cli for more details.
A typical SeqQuest command can be run from the top level of the repository using:

```bash
python py/tree_builder.py --help
```

## 5. Explore

There is much more documentation at /docs/

