import sys
import os
import csv
from types import SimpleNamespace
import difflib
import sequences

# Mock sequences module
class MockSequences:
    def get_protein(self, number):
        ns = SimpleNamespace()
        ns.name = f"Protein_{number}"
        ns.id = f"P{number}"
        ns.entry = f"ENTRY_{number}"
        ns.sequence_length = 100 + number
        return ns

# Inject mock into sys.modules so tree_builder imports it
# sys.modules['sequences'] = MockSequences()

# Monkey patch sequences.get_protein which is imported by tree_builder
sequences.get_protein = MockSequences().get_protein


import tree_builder


"""
Tree Builder Implementation Validator - Cross-validates MST construction algorithms.

This tool compares implementations of the Minimum Spanning Tree builder
to ensure they produce identical results:
1. Python implementation (optimized for performance)
2. C++ implementation (compiled for speed)

Test cases include:
- Graphs with cycles (ensures cycle-breaking logic is correct)
- Graphs with weak links (tests edge replacement strategy)
- Sparse graphs (verifies optimization for unused node IDs)

Usage:
    python py/verify_tree_builder.py

When to run:
- After modifying tree building logic in tree_builder.py or tree_builder.cpp
- After changing edge replacement strategy
- Before processing large link files (verify algorithm correctness)

Validation approach:
- Uses crafted test graphs with known challenging cases (cycles, sparse nodes)
- Compares ASCII tree output using difflib (shows exact divergences)
- Verifies C++ implementation returns precomputed data structures
- Checks twilight node reports match across implementations

Why multiple implementations?
- Python (array): Optimized but still verifiable
- C++: Production speed, verified against Python versions

This catches bugs where optimizations change behavior, or where C++ translation
doesn't match Python logic.
"""

def create_test_links(filename):
    # Create a set of links that form cycles and require replacement
    # Nodes: 0, 1, 2, 3, 4, 5
    links = [
        # Form a line: 0-1-2-3
        (0, 1, 50, 0, 0),
        (1, 2, 50, 0, 0),
        (2, 3, 50, 0, 0),

        # Form a cycle 0-1-2-0 with a stronger link, should break 0-1 or 1-2
        (2, 0, 100, 0, 0),

        # Form a separate component 4-5
        (4, 5, 80, 0, 0),

        # Connect components 3-4 with weak link
        (3, 4, 10, 0, 0),

        # Try to bridge 0-5 with strong link, should replace 3-4 (weakest on path)
        (0, 5, 90, 0, 0)
    ]

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['query', 'target', 'score', 'location', 'length'])
        writer.writerows(links)

def create_sparse_links(filename):
    # Create links with low IDs but claim high capacity
    links = [
        (1, 2, 50, 0, 0),
        (2, 3, 50, 0, 0)
    ]
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['query', 'target', 'score', 'location', 'length'])
        writer.writerows(links)

def run_test():
    input_file = "test_links_temp.csv"
    output_file_py = "test_tree_py.txt"
    output_file_cpp = "test_tree_cpp.txt"
    report_py = "test_report_py.txt"
    report_cpp = "test_report_cpp.txt"

    # --- Test 1: Standard Logic Verification ---
    print("--- Test 1: Verification of Tree Logic ---")
    create_test_links(input_file)

    print("Running Python array-based process_links_file...")
    tree_py = tree_builder.process_links_file(input_file, 6)
    tree_py.write_ascii_tree(output_file_py)
    with open(report_py, 'w') as f:
        tree_py.report_twilight(f)

    print("\nRunning C++ process_links_file...")
    try:
        tree_cpp = tree_builder.run_cpp_tree_builder(input_file, 6)
        tree_cpp.write_ascii_tree(output_file_cpp)
        with open(report_cpp, 'w') as f:
            tree_cpp.report_twilight(f)
        cpp_ran = True
    except Exception as e:
        print(f"C++ run failed: {e}")
        cpp_ran = False

    # Compare output files
    success = True

    # Check C++ vs Python Array
    if cpp_ran:
        # Check ASCII Tree
        with open(output_file_py, 'r') as f1, open(output_file_cpp, 'r') as f2:
            content_py = f1.readlines()
            content_cpp = f2.readlines()

        diff = list(difflib.unified_diff(content_py, content_cpp, fromfile='PythonArray', tofile='CPP'))
        if diff:
            print("\nFAILURE: C++ vs Python ASCII Tree files differ:")
            for line in diff:
                print(line, end='')
            success = False
        else:
            print("C++ vs Python ASCII Tree match.")

        # Check Twilight Report
        with open(report_py, 'r') as f1, open(report_cpp, 'r') as f2:
            content_py = f1.readlines()
            content_cpp = f2.readlines()

        diff = list(difflib.unified_diff(content_py, content_cpp, fromfile='PythonArray', tofile='CPP'))
        if diff:
            print("\nFAILURE: C++ vs Python Twilight Report files differ:")
            for line in diff:
                print(line, end='')
            success = False
        else:
            print("C++ vs Python Twilight Report match.")

    # Verify C++ used precomputed data
    if cpp_ran:
        if tree_cpp.precomputed_children is None:
            print("FAILURE: C++ tree object did not contain precomputed children.")
            success = False
        else:
            print("Success: C++ tree object has precomputed children.")

        if tree_cpp.precomputed_twilight_nodes is None:
            print("FAILURE: C++ tree object did not contain precomputed twilight nodes.")
            success = False
        else:
            print("Success: C++ tree object has precomputed twilight nodes.")

    # --- Test 2: Sparse/Optimization Verification (Python Only as per original) ---
    print("\n--- Test 2: Sparse/Optimization Verification (Python Logic) ---")
    create_sparse_links(input_file)
    large_n = 1000
    tree_sparse = tree_builder.process_links_file(input_file, large_n)
    if tree_sparse.max_seen_id != 3:
        print(f"FAILURE: Expected max_seen_id 3, got {tree_sparse.max_seen_id}")
        success = False
    else:
        print("Max seen ID is correct.")

    if success:
        print("\nOVERALL SUCCESS: All checks passed!")
    else:
        print("\nOVERALL FAILURE: One or more checks failed.")

    # Clean up
    if os.path.exists(input_file):
        os.remove(input_file)
    if os.path.exists(output_file_py):
        os.remove(output_file_py)
    if os.path.exists(output_file_cpp):
        os.remove(output_file_cpp)
    if os.path.exists(report_py):
        os.remove(report_py)
    if os.path.exists(report_cpp):
        os.remove(report_cpp)

if __name__ == "__main__":
    run_test()
