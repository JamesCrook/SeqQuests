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
    output_file_new = "test_tree_new.txt"
    report_orig = "test_report_orig.txt"
    report_new = "test_report_new.txt"

    # --- Test 1: Standard Logic Verification ---
    print("--- Test 1: Verification of Tree Logic ---")
    create_test_links(input_file)

    print("Running legacy process_links_file_legacy...")
    tree_orig = tree_builder.process_links_file_legacy(input_file, 6)
    tree_orig.write_ascii_tree(output_file_orig)
    with open(report_orig, 'w') as f:
        tree_orig.report_twilight(f)

    print(f"Original Tree Stats: Added={tree_orig.links_added}, Rejected={tree_orig.links_rejected}")

    print("\nRunning new array-based process_links_file...")
    tree_new = tree_builder.process_links_file(input_file, 6)
    tree_new.write_ascii_tree(output_file_new)
    with open(report_new, 'w') as f:
        tree_new.report_twilight(f)

    print(f"New Tree Stats: Added={tree_new.links_added}, Rejected={tree_new.links_rejected}")

    # Compare output files
    success = True

    # Check ASCII Tree
    with open(output_file_orig, 'r') as f1, open(output_file_new, 'r') as f2:
        content_orig = f1.readlines()
        content_new = f2.readlines()

    diff = list(difflib.unified_diff(content_orig, content_new, fromfile='Original', tofile='New'))
    if diff:
        print("\nFAILURE: ASCII Tree files differ:")
        for line in diff:
            print(line, end='')
        success = False
    else:
        print("ASCII Tree files match.")

    # Check Twilight Report
    with open(report_orig, 'r') as f1, open(report_new, 'r') as f2:
        content_orig = f1.readlines()
        content_new = f2.readlines()

    diff = list(difflib.unified_diff(content_orig, content_new, fromfile='Original', tofile='New'))
    if diff:
        print("\nFAILURE: Twilight Report files differ:")
        for line in diff:
            print(line, end='')
        success = False
    else:
        print("Twilight Report files match.")

    # --- Test 2: Sparse/Optimization Verification ---
    print("\n--- Test 2: Sparse/Optimization Verification ---")
    create_sparse_links(input_file)
    # Use large number of nodes (e.g., 1000) but only data up to 3
    large_n = 1000

    print(f"Running new array-based process_links_file with {large_n} nodes (but only small IDs)...")
    tree_sparse = tree_builder.process_links_file(input_file, large_n)

    # Verify max_seen_id
    print(f"Max seen ID: {tree_sparse.max_seen_id}")
    if tree_sparse.max_seen_id != 3:
        print(f"FAILURE: Expected max_seen_id 3, got {tree_sparse.max_seen_id}")
        success = False
    else:
        print("Max seen ID is correct.")

    tree_sparse.write_ascii_tree(output_file_new)

    # Verify output does not contain info for node 999 (which would exist if iterated fully without check)
    with open(output_file_new, 'r') as f:
        content = f.read()
        if "Node 999" in content:
            print("FAILURE: Sparse tree output contains high index empty node (optimization failed).")
            success = False
        else:
            print("Sparse tree output correctly ignores high index empty nodes.")

    if success:
        print("\nOVERALL SUCCESS: All checks passed!")
    else:
        print("\nOVERALL FAILURE: One or more checks failed.")

    # Clean up
    if os.path.exists(input_file):
        os.remove(input_file)
    # Keep output files for inspection if needed

if __name__ == "__main__":
    run_test()