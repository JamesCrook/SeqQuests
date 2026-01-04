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

4.  Compile the C++/Metal components:
    ```bash
    ./compile.sh
    ```
    *Note: This requires `metal-cpp` to be available, see prerequisites 1a*

5.  Compile the in browser alignment component:
    ```bash
    ./compile_wasm.sh
    ```
    *Note: This gives fast in-browser alignment.*

6.  Install the Uniprot protein data files.
    ```bash
    ./get_uniprot.sh
    ```

## 3. Running Tools via CLI

SeqQuest is built on top of command line tools. See /docs/tutorials/cli for more details.
A typical SeqQuest command can be run from the top level of the repository using:

```bash
python py/tree_builder.py --help
```

## 4. Running the Server
Start the web user interface:
```bash
python py/web_server.py
```
Access the dashboard at `http://localhost:8006`.

To reproduce the results in /findings/ you will need to run the search job which takes about 30 hrs. You can run it from the command line:

```bash
python py/sw_search.py
```
It is designed to pick up where it left off, if it is stopped and restarted.

To monitor progress of this search, you can use:

```bash
tail sw_results/sw_results.csv
```

There is also a nicer way to run the search, via a web interface. You start the web dashboard and start a Smith-Waterman job. Running from the web dashboard has the advantage that you get clearer information about progress, and as with the CLI, you can stop it and start it again and it will pick up from where it left off.

## 5. Explore

There is more documentation at /docs/ though these docs and the software are very much a work in progress.

# Automated

There is a script py/ready_to_rock.py that attempts to automate these steps. It runs through a checklist of steps, and if one fails, reports on the failure with what (it believes) needs doing to fix it.

Here is a sample of what it may output.

```
============================================================
  🎸 Ready to Rock? - Environment Checker
============================================================


  [ENVIRONMENT]
  ✅ Python Version: Python 3.9.6
  ✅ Apple Silicon: Apple M4 Pro

  [CONFIGURATION]
  ✅ .env File: .env configured

  [DEPENDENCIES]
  ✅ metal-cpp: Found at /Users/james/metal-cpp
  ✅ Package Installed: Package installed (seqquests.egg-info)

  [COMPILATION]
  ✅ Metal Components: Found all binaries (THREADS=65536, UNROLL=40)
  ✅ WASM Components: Found sw_align_module.js (7.9 KB)

  [DATA]
  ✅ Uniprot Data: Found at /Users/james/BigData/bio_sequence_data
  ✅ Binary Data: Found pam250.bin (1.0 KB), fasta.bin (273.7 MB)

------------------------------------------------------------
  🎸 You're ready to rock! All checks passed.
------------------------------------------------------------
```

At this point, with all checks green, you can run the search.
```bash
python py/sw_search.py
```
See the 'Running the Server' section for details/alternatives. When it has completed the 'ready_to_rock.py' script, if run, will report additional steps:

```
============================================================
  📊 Post-Processing Checks (search job completed)
============================================================

  [RESULTS]
  ✅ SW Results: Found (3935.5 MB)
  ✅ Tree Builder: Found sw_tree.txt and sw_finds_raw.txt
  ✅ Filtered Finds: Found sw_finds_standard.txt and sw_finds_biased.txt

------------------------------------------------------------
  🔬 Analysis complete! Results ready for review in the web UI.
------------------------------------------------------------
```
