# Tree Builder Documentation

## Overview
`tree_builder.py` builds a Maximum Spanning Tree (MST) from protein similarity links produced by the Smith-Waterman search. It reduces the O(N^2) web of connections to a O(N) tree structure, highlighting the strongest relationships.

## Usage

```bash
python py/tree_builder.py [options]
```

## Command Line Arguments
| Argument | Default | Description |
|----------|---------|-------------|
| `-i`, `--input` | `sw_results/sw_results.csv` | Input CSV file with links. |
| `-o`, `--output` | `sw_results/sw_tree.txt` | Output file for the ASCII tree. |
| `-n`, `--nodes` | Auto-detect | Number of nodes (proteins). |
| `-t`, `--threshold` | -3 | Score threshold to stop descending. |
| `-v`, `--verbose` | True | Print statistics and progress. |
| `--cpp` | True | Use the C++ backend for faster processing. |
| `--test` | N/A | Run a test function. |

## C++ Backend (`tree_builder_cpp`)
The Python script wraps a C++ executable (`bin/tree_builder_cpp`) for performance. The C++ backend accepts similar arguments (`-i`, `-o`, `-n`).
