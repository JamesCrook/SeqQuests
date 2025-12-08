#!/usr/bin/env python3
"""
Maximum Spanning Tree Builder for Protein Similarity Networks

This tool builds a maximum spanning tree from protein similarity links,
processing them in streaming fashion without requiring pre-sorting.
"""

import argparse
import sys
import json
import subprocess
import os
import tempfile
from pathlib import Path
import numpy as np
import sequences
from config import DATA_DIR, PROJECT_ROOT


"""
Most of the same functionality is now performed faster in the cpp version. 
This is both a wrapper for the fast version and also a reference implementation, 
in python, which we may later elaborate. 

We may also use the python version in educational code that explains the algorithm.
"""

class MaxSpanningTree:
    # Class-level variable to store the inverse index (shared across instances)
    _inverse_index = None
    _inverse_index_path = None
    
    def __init__(self, num_nodes):
        self.num_nodes = num_nodes
        self.max_seen_id = 0 # Track the maximum node ID encountered
        self.parents = [0] * num_nodes
        self.scores = [-1] * num_nodes
        self.raw_scores = [-1] * num_nodes
        self.locations = [-1] * num_nodes
        self.lengths = [-1] * num_nodes

        self.links_processed = 0
        self.links_added = 0
        self.links_rejected = 0

        # Pre-computed structures from C++ backend (optional)
        self.precomputed_twilight_nodes = None
        self.precomputed_children = None
        self.precomputed_root = None

        # Traversal optimization: Arrays instead of dicts for visited tracking
        # visited_indices[node_id] = index_in_path
        # visited_search_ids[node_id] = search_id
        self.visited_a_indices = [-1] * num_nodes
        self.visited_b_indices = [-1] * num_nodes
        self.visited_a_search_ids = [0] * num_nodes
        self.visited_b_search_ids = [0] * num_nodes
        self.search_id = 0
    
    @classmethod
    def load_inverse_index(cls, inv_index_path):
        """
        Load the inverse index from binary file.
        This is called once and cached at the class level.
        
        Args:
            inv_index_path: Path to the fasta_inv_index.bin file
        """
        inv_index_path = Path(inv_index_path)
        
        # Only load if not already loaded or if path has changed
        if cls._inverse_index is None or cls._inverse_index_path != inv_index_path:
            if not inv_index_path.exists():
                print(f"Warning: Inverse index file not found at {inv_index_path}")
                print(f"Assuming sequences are not sorted (using ID as-is)")
                cls._inverse_index = None
                cls._inverse_index_path = None
                return
            
            print(f"Loading inverse index from {inv_index_path}...")
            with open(inv_index_path, "rb") as f:
                data = f.read()
            
            cls._inverse_index = np.frombuffer(data, dtype=np.int32)
            cls._inverse_index_path = inv_index_path
            print(f"Loaded inverse index with {len(cls._inverse_index):,} entries")
    
    @classmethod
    def get_original_id(cls, sorted_id):
        """
        Map from sorted sequence ID back to original sequence ID.
        
        Args:
            sorted_id: The ID in the sorted sequence file
            
        Returns:
            The original sequence ID before sorting
        """
        if cls._inverse_index is None:
            # No inverse index loaded, assume sequences are not sorted
            return sorted_id
        
        if sorted_id < 0 or sorted_id >= len(cls._inverse_index):
            print(f"Warning: ID {sorted_id} out of range for inverse index")
            return sorted_id
        
        return int(cls._inverse_index[sorted_id])

    def load_from_json(self, json_file):
        with open(json_file, 'r') as f:
            data = json.load(f)

        self.parents = data['parents']
        self.scores = data['scores']
        self.raw_scores = data['raw_scores']
        self.locations = data['locations']
        self.lengths = data['lengths']

        self.links_processed = data['links_processed']
        self.links_added = data['links_added']
        self.links_rejected = data['links_rejected']
        self.max_seen_id = data['max_seen_id']

        if 'twilight_nodes' in data:
            self.precomputed_twilight_nodes = data['twilight_nodes']

        if 'children' in data:
            self.precomputed_children = data['children']

        if 'root' in data:
            self.precomputed_root = data['root']

    def set_link(self, node_id, parent, score, raw_score, location, length):
        self.parents[node_id] = parent
        self.scores[node_id] = score
        self.raw_scores[node_id] = raw_score
        self.locations[node_id] = location
        self.lengths[node_id] = length

        # Track max ID seen
        if node_id > self.max_seen_id:
            self.max_seen_id = node_id
        if parent > self.max_seen_id:
            self.max_seen_id = parent

    def find_meeting_point(self, node_a, node_b):
        self.search_id += 1
        # To avoid creating new lists for paths, we could traverse twice,
        # but to match original logic and return paths, we keep path lists.
        # path lists are usually short (log N), so list overhead is small compared to dicts/objects.
        path_a = []
        path_b = []
        current_a = node_a
        current_b = node_b

        # Local cache for speed
        parents = self.parents
        search_id = self.search_id
        vis_a_ids = self.visited_a_search_ids
        vis_b_ids = self.visited_b_search_ids
        vis_a_idxs = self.visited_a_indices
        vis_b_idxs = self.visited_b_indices

        while True:
            if current_a is not None:
                # Check if b visited this node in this search
                if vis_b_ids[current_a] == search_id:
                    meeting_index = vis_b_idxs[current_a]
                    path_b = path_b[:meeting_index]
                    return current_a, path_a, path_b

                # Mark as visited by a
                vis_a_ids[current_a] = search_id
                vis_a_idxs[current_a] = len(path_a)

                if current_a == 0:
                    current_a = None
                else:
                    path_a.append(current_a)
                    current_a = parents[current_a]

            if current_b is not None:
                # Check if a visited this node
                if vis_a_ids[current_b] == search_id:
                    meeting_index = vis_a_idxs[current_b]
                    path_a = path_a[:meeting_index]
                    return current_b, path_a, path_b

                # Mark as visited by b
                vis_b_ids[current_b] = search_id
                vis_b_idxs[current_b] = len(path_b)

                if current_b == 0:
                    current_b = None
                else:
                    path_b.append(current_b)
                    current_b = parents[current_b]

            if current_a is None and current_b is None:
                raise Exception("Paths didn't meet")

    def find_weakest_link_in_cycle(self, path_a, path_b, new_score):
        min_score = new_score
        min_location = ('new', -1)
        scores = self.scores

        for i, node_id in enumerate(path_a):
            link_score = scores[node_id]
            if link_score < min_score:
                min_score = link_score
                min_location = ('a', i)

        for i, node_id in enumerate(path_b):
            link_score = scores[node_id]
            if link_score < min_score:
                min_score = link_score
                min_location = ('b', i)

        return min_score, min_location[0], min_location[1]

    def reverse_path(self, path, up_to_index):
        parents = self.parents
        scores = self.scores
        raw_scores = self.raw_scores
        locations = self.locations
        lengths = self.lengths

        for i in range(up_to_index, 0, -1):
            current_node_id = path[i]
            prev_node_id = path[i-1]

            # Set current node's link to point to prev node, using prev node's link properties
            self.set_link(
                current_node_id,
                prev_node_id,
                scores[prev_node_id],
                raw_scores[prev_node_id],
                locations[prev_node_id],
                lengths[prev_node_id]
            )

        # path[0] points nowhere (becomes root of this subtree temporarily or new connection point)
        start_node_id = path[0]
        self.set_link(start_node_id, start_node_id, -1, -1, -1, -1) # Matches default/root state

    def add_link(self, node_a, node_b, score, raw_score, location, length):
        self.links_processed += 1

        if node_a > self.max_seen_id:
            self.max_seen_id = node_a
        if node_b > self.max_seen_id:
            self.max_seen_id = node_b

        if node_a == node_b:
            return False

        meeting_point, path_a, path_b = self.find_meeting_point(node_a, node_b)
        min_score, which_path, position = self.find_weakest_link_in_cycle(
            path_a, path_b, score
        )

        if which_path == 'new':
            self.links_rejected += 1
            return False

        # Accept the link
        if which_path == 'a':
            self.reverse_path(path_a, position)
            self.set_link(node_a, node_b, score, raw_score, location, length)
        else:
            self.reverse_path(path_b, position)
            self.set_link(node_b, node_a, score, raw_score, location, length)

        self.links_added += 1
        return True

    def build_children_map(self):
        if self.precomputed_children:
            return self.precomputed_children

        # Optimization: Use list of lists instead of dict of lists
        children = [[] for _ in range(self.num_nodes)]
        parents = self.parents
        scores = self.scores

        # Safe to iterate up to max_seen_id + 1 because any node > max_seen_id
        # hasn't been touched, so score is -1 (invalid) and it's not a child of anyone.
        limit = min(self.max_seen_id + 1, self.num_nodes)

        for i in range(limit):
            if scores[i] >= 0:
                children[parents[i]].append(i)
        return children

    def find_root(self):
        if self.precomputed_root is not None:
            return self.precomputed_root

        roots = []
        parents = self.parents
        scores = self.scores

        limit = min(self.max_seen_id + 1, self.num_nodes)

        for i in range(limit):
            if scores[i] < 0 or parents[i] == i:
                roots.append(i)

        if not roots:
            return 0

        children = self.build_children_map()

        def count_descendants(node_id):
            count = len(children[node_id])
            for child in children[node_id]:
                count += count_descendants(child)
            return count

        best_root = roots[0]
        max_descendants = count_descendants(best_root)

        for root in roots[1:]:
            desc_count = count_descendants(root)
            if desc_count > max_descendants:
                max_descendants = desc_count
                best_root = root

        return best_root

    # The search worked with renumbered proteins.
    # We must get the true number before doing the look up.
    @classmethod
    def get_renumbered_protein( cls, id ):
        # Map from sorted ID back to original ID using inverse index
        original_id = cls.get_original_id(id)
        return sequences.get_protein( original_id )

    def report_twilight(self, f):

        def should_skip(r1, r2):
            return false
            if 'toxin' in r1.name.lower() and 'toxin' in r2.name.lower():
                return 'toxins'
            if ('uncharacterized' in r1.name.lower() or 'uncharacterized' in r2.name.lower() or
                'putative' in r1.name.lower() or 'putative' in r2.name.lower()):
                return 'uncharacterized'
            if 'seed storage' in r1.name.lower() and 'seed storage' in r2.name.lower():
                return 'seed storage'
            if r1.name.lower()[:11] == r2.name.lower()[:11]:
                return 'similar names'
            return None

        finds = 0

        scores = self.scores
        parents = self.parents

        if self.precomputed_twilight_nodes is not None:
            sorted_twilight_indices = self.precomputed_twilight_nodes
            finds = len(sorted_twilight_indices)
        else:
            twilight_indices = []
            limit = min(self.max_seen_id + 1, self.num_nodes)
            for i in range(limit):
                if scores[i] >= 0:
                    twilight_indices.append(i)
                    finds += 1
            sorted_twilight_indices = sorted(twilight_indices, key=lambda i: scores[i], reverse=True)

        f.write(f"found {finds} finds\n")

        skip_counts = {'toxins': 0, 'uncharacterized': 0, 'seed storage':0, 'similar names':0}
        total_skip_counts = {'toxins': 0, 'uncharacterized': 0, 'seed storage':0, 'similar names':0}

        for node_id in sorted_twilight_indices:
            parent_id = parents[node_id]
            r1 = self.get_renumbered_protein(node_id)
            r2 = self.get_renumbered_protein(parent_id)

            skip_reason = should_skip(r1, r2)
            if skip_reason:
                skip_counts[skip_reason] += 1
                total_skip_counts[skip_reason] += 1
                continue

            skip_string = ""
            if any(skip_counts.values()):
                skip_parts = [f"{count} {reason}" for reason, count in skip_counts.items() if count > 0]
                skip_string = f" [...skipped {' and '.join(skip_parts)}]"
                skip_counts = {key: 0 for key in skip_counts}

            f.write(f"{r1.number}-{r2.number} s({scores[node_id]}) {r1.id}-{r2.id} Length: {r1.sequence_length}/{r2.sequence_length}{skip_string}\n")
            f.write(f" {r1.number}: {r1.name}\n")
            f.write(f" {r2.number}: {r2.name}\n")

        grand_total = sum(total_skip_counts.values())
        if grand_total > 0:
            f.write("\n" + "=" * 80 + "\n")
            f.write("TOTAL SKIPPED:\n")
            for reason, count in total_skip_counts.items():
                if count > 0:
                    f.write(f"  {reason}: {count}\n")
            f.write(f"  Grand total: {grand_total}\n")
            f.write(f"  Leaving: {finds-grand_total} finds to check\n")

    def write_ascii_tree(self, output_file, score_threshold=0, show_isolated=True):
        with open(output_file, 'w') as f:
            root = self.find_root()
            children = self.build_children_map()
            written_nodes = set()

            f.write(f"Maximum Spanning Tree (root: node {root})\n")
            f.write(f"Total links: {self.links_added}\n")
            f.write("=" * 80 + "\n\n")

            def get_sorted_children(parent_id):
                # If we have precomputed children (which are sorted), just return them
                if self.precomputed_children:
                    return children[parent_id]

                child_list = children[parent_id][:]
                child_list.sort(key=lambda c: self.scores[c], reverse=True)
                return child_list

            def write_subtree(node_id, prefix="", is_last=True, depth=0, component=0):
                written_nodes.add(node_id)

                if depth == 0:
                    connector = ""
                    branch = ""
                else:
                    connector = "└─ " if is_last else "├─ "
                    branch = "   " if is_last else "│  "

                adjusted_len = max(0, len(prefix) - 40)
                start_index = adjusted_len - (adjusted_len % 40)
                short_prefix = f"{start_index}:{prefix[start_index:]}"

                record = self.get_renumbered_protein(node_id)
                if node_id%1000 == 0:
                    print(f"tree: {node_id}")

                if depth == 0:
                    f.write(f"{short_prefix}{connector}Node {record.number} {record.id} Length:{record.sequence_length} [ROOT {component}] {record.name} \n")
                else:
                    f.write(f"{short_prefix}{connector}Node {record.number} {record.id} Length:{record.sequence_length} (s:{self.scores[node_id]}) {record.name}\n")

                sorted_children = get_sorted_children(node_id)

                for i, child_id in enumerate(sorted_children):
                    is_last_child = (i == len(sorted_children) - 1)

                    if score_threshold > 0 and self.scores[child_id] < score_threshold:
                        stub_prefix = prefix + branch
                        stub_connector = "└── " if is_last_child else "├── "
                        f.write(f"{stub_prefix}{stub_connector}[STUB: Node {child_id}, score {self.scores[child_id]} < threshold]\n")
                        continue

                    new_prefix = prefix + branch
                    write_subtree(child_id, new_prefix, is_last_child, depth + 1)

            write_subtree(root, component=0)

            if show_isolated:
                # Optimized: Only check nodes up to max_seen_id for isolation
                limit = min(self.max_seen_id + 1, self.num_nodes)
                unwritten = [i for i in range(limit) if i not in written_nodes]

                if unwritten:
                    other_roots = []
                    for node_id in unwritten:
                        if self.scores[node_id] < 0 or self.parents[node_id] == node_id:
                            other_roots.append(node_id)

                    for component_num, component_root in enumerate(other_roots, start=2):
                        if component_root in written_nodes: continue
                        write_subtree(component_root, component=component_num)

                    isolated = [i for i in range(limit)
                               if i not in written_nodes and self.scores[i] < 0]

                    if isolated:
                        f.write("\n" + "=" * 80 + "\n")
                        f.write(f"ISOLATED NODES (no connections): {len(isolated)}\n")
                        f.write("-" * 80 + "\n")
                        for node_id in isolated:
                            record = self.get_renumbered_protein(node_id)
                            f.write(f"Node {node_id}: {record.name}\n")

def process_links_file(filename, num_nodes):
    tree = MaxSpanningTree(num_nodes)

    with open(filename, 'r') as f:
        next(f)  # Skip header
        old_query = 0;
        for line in f:
            parts = line.strip().split(',')
            if len(parts) != 5:
                continue
            query = int(parts[0])
            target = int(parts[1])
            if query != old_query:
                old_query = query
                if query %100 == 0:
                    print(f"{query}\t{target}")
            if query >= num_nodes:
                continue
            if target >= num_nodes:
                continue
            score = int(parts[2])
            location = int(parts[3])
            length = int(parts[4])
            tree.add_link(query, target, score, score, location, length)

    return tree

def run_cpp_tree_builder(input_file, num_nodes=None):
    """Run the C++ implementation and return a MaxSpanningTree object."""
    temp_json = "temp_tree_output.json"

    executable = PROJECT_ROOT / "bin/tree_builder_cpp"
    cmd = [
        str(executable), 
        "--data-dir", str(DATA_DIR), 
        "-i", input_file, 
        "-o", temp_json]
    if num_nodes is not None:
        cmd.extend(["-n", str(num_nodes)])

    try:
        print("Running C++ tree builder...")
        subprocess.run(cmd, check=True)

        # If num_nodes was not provided, we need to peek at the JSON to know how big of an object to create.
        # Actually, load_from_json will overwrite the arrays anyway, but we need an initial size for the constructor.
        # Let's just peek at the file first or modify the class to handle dynamic sizing.
        # Or we can just load the JSON fully here.

        with open(temp_json, 'r') as f:
            data = json.load(f)

        # Determine size from arrays
        actual_num_nodes = len(data['parents'])

        tree = MaxSpanningTree(actual_num_nodes)
        # We can reload from file or just use the data we loaded.
        # But to keep method clean, let's just call tree.load_from_json
        # Wait, we can just populate it manually here since we have 'data'

        tree.parents = data['parents']
        tree.scores = data['scores']
        tree.raw_scores = data['raw_scores']
        tree.locations = data['locations']
        tree.lengths = data['lengths']

        tree.links_processed = data['links_processed']
        tree.links_added = data['links_added']
        tree.links_rejected = data['links_rejected']
        tree.max_seen_id = data['max_seen_id']

        if 'twilight_nodes' in data:
            tree.precomputed_twilight_nodes = data['twilight_nodes']
        if 'children' in data:
            tree.precomputed_children = data['children']
        if 'root' in data:
            tree.precomputed_root = data['root']

    finally:
        #pass
        if os.path.exists(temp_json):
            os.remove(temp_json)

    return tree

def scan_for_max_node_id(filename):
    """
    Scan the input CSV file to find the maximum query ID (first column).
    """
    max_id = 0
    with open(filename, 'r') as f:
        next(f) # Skip header
        for line in f:
            # We only need the first part
            comma_index = line.find(',')
            if comma_index != -1:
                try:
                    query_id = int(line[:comma_index])
                    if query_id > max_id:
                        max_id = query_id
                except ValueError:
                    pass
    return max_id

def test():
    """Test the maximum spanning tree algorithm with inline data."""
    print("=" * 60)
    print("Maximum Spanning Tree Test")
    print("=" * 60)
    print()
    
    # Create test data inline
    # Format: query_seq,target_seq,score,location,length
    # This creates a simple tree:
    #   0 (root)
    #   ├─ 1 (score 500)
    #   │  └─ 2 (score 400)
    #   └─ 3 (score 450)
    #      └─ 4 (score 350)
    test_data = """query_seq,target_seq,score,location,length
0,1,500,0,100
1,2,400,50,80
0,3,450,20,90
3,4,350,30,70
2,3,300,10,60
1,4,250,40,55
"""
    
    # Write test data to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_file = f.name
        f.write(test_data)
    
    try:
        print("Building tree from test data...")
        print(f"Test data has 5 nodes (0-4) with 6 links")
        print()
        
        # Process the test file
        tree = process_links_file(temp_file, num_nodes=6)
        
        print(f"Statistics:")
        print(f"  Links processed: {tree.links_processed}")
        print(f"  Links added: {tree.links_added}")
        print(f"  Links rejected: {tree.links_rejected}")
        print()
        
        # Verify tree structure
        print("Tree structure verification:")
        print(f"  Node 0 (root): parent={tree.parents[0]}, score={tree.scores[0]}")
        print(f"  Node 1: parent={tree.parents[1]}, score={tree.scores[1]}")
        print(f"  Node 2: parent={tree.parents[2]}, score={tree.scores[2]}")
        print(f"  Node 3: parent={tree.parents[3]}, score={tree.scores[3]}")
        print(f"  Node 4: parent={tree.parents[4]}, score={tree.scores[4]}")
        print()
        
        # Write tree to temporary output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_output = f.name
        
        print(f"Writing tree visualization to {temp_output}...")
        tree.write_ascii_tree(temp_output, score_threshold=0, show_isolated=True)
        
        # Show the tree
        print("\nTree visualization:")
        print("-" * 60)
        with open(temp_output, 'r') as f:
            print(f.read())
        
        # Clean up
        os.remove(temp_output)
        
        print("=" * 60)
        print("Test completed successfully!")
        print()
        print("Expected behavior:")
        print("  - Should accept 5 highest-scoring links")
        print("  - Should reject 1 link that would create a cycle")
        print("  - Tree should be connected with node 0 as root")
        
    finally:
        # Clean up temp file
        os.remove(temp_file)


def main():
    parser = argparse.ArgumentParser(
        description='Build maximum spanning tree from protein similarity links',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --test
  %(prog)s -i links.csv -o sw_tree.txt
  %(prog)s -i links.csv -o sw_tree.txt --nodes 157000
  %(prog)s -i links.csv -o sw_tree.txt --threshold 200
  %(prog)s -i links.csv -o sw_tree.txt --threshold 200 --verbose
  %(prog)s -i links.csv -o sw_tree.txt --inv-index-file ../data/fasta_inv_index.bin
        """
    )
    
    default_input = PROJECT_ROOT / "sw_results/sw_results.csv"
    default_output = PROJECT_ROOT / "sw_results/sw_tree.txt"
    default_inv_index = PROJECT_ROOT / "data/fasta_inv_index.bin"
    finds_file = PROJECT_ROOT / "sw_results/sw_raw_finds.txt"

    parser.add_argument('-i', '--input', default=str(default_input), 
                       help='Input CSV file with links (query_seq,target_seq,score,location,length)')
    parser.add_argument('-o', '--output', default=str(default_output),
                       help='Output file for ASCII tree')
    parser.add_argument('-n', '--nodes', type=int, default=None,
                       help='Number of nodes (proteins). If not specified, will be auto-detected from input file.')
    parser.add_argument('-t', '--threshold', type=int, default=-3,
                       help='Score threshold - stop descending below this (default: -3)')
    parser.add_argument('-v', '--verbose', action='store_true', default=True,
                       help='Print statistics and progress')
    parser.add_argument('--cpp', action='store_true', help='Use C++ backend for faster processing', default=True)
    parser.add_argument('--test', action='store_true', help='Run test function')
    parser.add_argument('--no-test', action='store_false', dest='test', help='Disable test mode')
    parser.add_argument('--inv-index-file', type=str, default=str(default_inv_index),
                       help=f'Path to inverse index binary file (default: {default_inv_index}). '
                            'Used to map sorted sequence IDs back to original IDs.')
    parser.set_defaults(test=False)
    
    args = parser.parse_args()

    if args.test:
        test()
        return
    
    # Load the inverse index if provided
    if args.inv_index_file:
        MaxSpanningTree.load_inverse_index(args.inv_index_file)
    
    if args.cpp:
        if args.verbose:
            print("Using C++ backend.")
        tree = run_cpp_tree_builder(args.input, args.nodes)
    else:
        num_nodes = args.nodes
        if num_nodes is None:
            if args.verbose:
                print(f"Scanning {args.input} to determine number of nodes...")
            max_id = scan_for_max_node_id(args.input)
            num_nodes = max_id + 1
            if args.verbose:
                print(f"Detected {num_nodes} nodes.")

        if args.verbose:
            print(f"Building maximum spanning tree from {args.input}...")
            print(f"Number of nodes: {num_nodes}")

        tree = process_links_file(args.input, num_nodes)
    
    if args.verbose:
        print(f"\nStatistics:")
        print(f"  Links processed: {tree.links_processed}")
        print(f"  Links added: {tree.links_added}")
        print(f"  Links rejected: {tree.links_rejected}")
        print(f"\nWriting ASCII tree to {args.output}...")
    
    with open(finds_file, 'w') as f:
        tree.report_twilight(f)
    tree.write_ascii_tree(args.output, args.threshold)
    
    if args.verbose:
        print("Done!")

if __name__ == "__main__":
    main()