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

def run_test():
    input_file = "test_links_temp.csv"
    output_file_orig = "test_tree_orig.txt"
    output_file_new = "test_tree_new.txt"

    create_test_links(input_file)

    print("Running legacy process_links_file_legacy...")
    tree_orig = tree_builder.process_links_file_legacy(input_file, 6)
    tree_orig.write_ascii_tree(output_file_orig)
    print(f"Original Tree Stats: Added={tree_orig.links_added}, Rejected={tree_orig.links_rejected}")

    print("\nRunning new array-based process_links_file...")
    tree_new = tree_builder.process_links_file(input_file, 6)
    tree_new.write_ascii_tree(output_file_new)
    print(f"New Tree Stats: Added={tree_new.links_added}, Rejected={tree_new.links_rejected}")

    # Compare output files
    with open(output_file_orig, 'r') as f1, open(output_file_new, 'r') as f2:
        content_orig = f1.readlines()
        content_new = f2.readlines()

    diff = list(difflib.unified_diff(content_orig, content_new, fromfile='Original', tofile='New'))

    if not diff:
        print("\nSUCCESS: Output files are identical!")
    else:
        print("\nFAILURE: Output files differ:")
        for line in diff:
            print(line, end='')

    # Clean up
    if os.path.exists(input_file):
        os.remove(input_file)
    # if os.path.exists(output_file_orig):
    #     os.remove(output_file_orig)
    # if os.path.exists(output_file_new):
    #     os.remove(output_file_new)

if __name__ == "__main__":
    run_test()
