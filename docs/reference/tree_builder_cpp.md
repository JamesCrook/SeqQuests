# Tree Builder C++ Documentation

## Overview
`tree_builder_cpp` is the C++ backend for the tree building process. It mirrors the logic of the Python `MaxSpanningTree` implementation but is optimized for performance when processing large link files. The performance is required because we are processing GB of link data from the csv, and reducing it down to the MST. The backend does not fill in the protein names or IDs. It works in terms of database index numbers.

## Usage

```bash
./bin/tree_builder_cpp -i <input_csv> -o <output_json> [-n <num_nodes>]
```

## Arguments
| Flag | Description |
|------|-------------|
| `-i` | Input CSV file path (links). |
| `-o` | Output JSON file path (serialized tree state). |
| `-n` | Number of nodes (optional). |

## Output
The program outputs a JSON file containing the state of the MST (parents array, scores array, etc.), which is then loaded by the Python wrapper to generate the final ASCII report.
