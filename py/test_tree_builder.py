import sys
import os
import csv
from types import SimpleNamespace
import difflib

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
sys.modules['sequences'] = MockSequences()

import tree_builder

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
    output_file_orig = "test_tree_orig.txt"
    output_file_py = "test_tree_py.txt"
    output_file_cpp = "test_tree_cpp.txt"
    report_py = "test_report_py.txt"
    report_cpp = "test_report_cpp.txt"

    # --- Test 1: Standard Logic Verification ---
    print("--- Test 1: Verification of Tree Logic ---")
    create_test_links(input_file)

    print("Running legacy process_links_file_legacy...")
    tree_orig = tree_builder.process_links_file_legacy(input_file, 6)
    tree_orig.write_ascii_tree(output_file_orig)

    print("\nRunning Python array-based process_links_file...")
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

    # Check Python Array vs Original
    with open(output_file_orig, 'r') as f1, open(output_file_py, 'r') as f2:
        content_orig = f1.readlines()
        content_py = f2.readlines()

    diff = list(difflib.unified_diff(content_orig, content_py, fromfile='Original', tofile='PythonArray'))
    if diff:
        print("\nFAILURE: Python Array vs Legacy ASCII Tree files differ:")
        for line in diff:
            print(line, end='')
        success = False
    else:
        print("Python Array vs Legacy match.")

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

if __name__ == "__main__":
    run_test()