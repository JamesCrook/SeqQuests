# Getting Started

SeqQuests data processing can be used entirely from the command line. Python scripts calling on C++ executables read and write text files. There is a web based interface that can decorate these files, providing richer navigation than a text editor can provide. The principle that everything can be done in text is maintained. This makes building automated pipelines using the SeqQuests tools more straightforward.

SeqQuests was written with AI assistance. User interface features that would take a lot of time and effort to write if enitrely written by hand are widely used in SeqQuests. This doesn't change the nature of the science, but does change the ease of use.

A very early part of SeqQuests was a strongly accelerated implementation of the sensitive smith-waterman protein comparison algorithm. This depends on using Apple silicon, and has been run and tested on Mac M1, M2 and M4. The fast implementation will not run on Windows PCs. The fast algorithm is fast enough to compare 570,000 swissprot proteins all-on-all in a couple of days. Subsequent parts of a pipeline then reduce this data. 

Most users will want to install the web user interface and some users will want to use the command line tools directly.

The system can be set up without the fast C++ algorithms and without a protein database. This may be useful for a 'first look' to get a sense of what is in the repository. However, any serious use will require both. 

Users who have IT support staff may be able to skip over the installation steps below, and just connect to a URL that IT support provide. For such users, refer to documentation provided at your site. SeqQuests itself does not have log ins and separate user accounts. It is designed for local use first, for user-developers who will be running the software on their own machines.

# Installation

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
    ./compile_wasm.sh
    ```
    *Note: This requires `metal-cpp` to be available, see prerequisites 1a*

5. (Optional) Install the Uniprot protein data files.
    ```bash
    ./get_uniprot.sh
    ```
    This step is essential for searching, but isn't needed if just browsing 
    already computed results. 

## 3. Running the Server
Start the web dashboard to manage jobs:
```bash
python py/web_server.py
```
Access the dashboard at `http://localhost:8006`.

## 4. Running Tools via CLI

SeqQuests is built on top of command line tools. See /docs/tutorials/cli for more details.
A typical SeqQuests command can be run from the top level of the repository using:

```bash
python py/tree_builder.py --help
```

# First Session

Access the dashboard at `http://localhost:8006`.

You will be presented with a dashboard like the one below.

...figure...

There are two panels with star-trek themed buttons around them. There is a main panel which typically has detailed results in it, and a secondary panel that typically has a list or configuration set up.

When you start, the secondary panel shows information about your current set up - whether you have a protein database, whether you have the fast smith-waterman executable.

## Tree Browser

Since you have this repo, you have the sample results, and you can browse them. Click on the button 'Tree'. You will be shown the protein relatedness tree. You can scroll up and down in it, and search for text strings. Here is what different parts of an entry in the tree mean:

...figure...

Background on how the tree was formed and why some links are shown and not others can be found at /docs/explanations/tree.md. This is a protein relatedness tree, not an evolutionary tree.

At the top of the panel are 'breadcrumbs' for navigating the tree. The last not-dimmed sequence identifier in it is the currently selected sequence. You can click on other items to move up and down the breadcrumbs. Additionally between the sequences are chevrons, which when you hover over them show the two sequences and the strength of their link.

## List Browser

Lorem Ipsum delores

