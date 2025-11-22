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
import sequences

class TreeNode:
    def __init__(self, node_id):
        self.node_id = node_id
        self.parent = 0
        self.score = -1
        self.raw_score = -1
        self.location = -1
        self.length = -1
    
    def set_link(self, parent, score, raw_score, location, length):
        self.parent = parent
        self.score = score
        self.raw_score = raw_score
        self.location = location
        self.length = length

class MaxSpanningTree:
    def __init__(self, num_nodes):
        self.nodes = [TreeNode(i) for i in range(num_nodes)]
        self.links_processed = 0
        self.links_added = 0
        self.links_rejected = 0
    
    def find_meeting_point(self, node_a, node_b):
        visited_from_a = {}
        visited_from_b = {}
        path_a = []
        path_b = []
        current_a = node_a
        current_b = node_b
        
        while True:
            if current_a is not None:
                if current_a in visited_from_b:
                    # Paths meet at current_a
                    # Trim path_b to not include nodes after meeting point
                    meeting_index = visited_from_b[current_a]
                    path_b = path_b[:meeting_index]
                    return current_a, path_a, path_b
                visited_from_a[current_a] = len(path_a)
                
                # Stop at node 0 without adding it to path
                if current_a == 0:
                    current_a = None
                else:
                    path_a.append(current_a)
                    current_a = self.nodes[current_a].parent
            
            if current_b is not None:
                if current_b in visited_from_a:
                    # Paths meet at current_b
                    # Trim path_a to not include nodes after meeting point
                    meeting_index = visited_from_a[current_b]
                    path_a = path_a[:meeting_index]
                    return current_b, path_a, path_b
                visited_from_b[current_b] = len(path_b)
                
                # Stop at node 0 without adding it to path
                if current_b == 0:
                    current_b = None
                else:
                    path_b.append(current_b)
                    current_b = self.nodes[current_b].parent
            
            if current_a is None and current_b is None:
                raise Exception("Paths didn't meet")
    
    def find_weakest_link_in_cycle(self, path_a, path_b, new_score):
        min_score = new_score
        min_location = ('new', -1)
        
        for i, node_id in enumerate(path_a):
            link_score = self.nodes[node_id].score
            if link_score < min_score:
                min_score = link_score
                min_location = ('a', i)
        
        for i, node_id in enumerate(path_b):
            link_score = self.nodes[node_id].score
            if link_score < min_score:
                min_score = link_score
                min_location = ('b', i)
        
        return min_score, min_location[0], min_location[1]
    
    def reverse_path(self, path, up_to_index):
        # Reverse from up_to_index down to 1
        for i in range(up_to_index, 0, -1):
            current_node_id = path[i]
            prev_node_id = path[i-1]
            current_node = self.nodes[current_node_id]
            prev_node = self.nodes[prev_node_id]
            
            current_node.set_link(
                prev_node_id,
                prev_node.score,
                prev_node.raw_score,
                prev_node.location,
                prev_node.length
            )
        
        # path[0] points nowhere
        start_node = self.nodes[path[0]]
        start_node.parent = path[0]
        start_node.score = -1
        start_node.raw_score = -1
        start_node.location = -1
        start_node.length = -1
    
    def add_link(self, node_a, node_b, score, raw_score, location, length):
        self.links_processed += 1
        
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
            self.nodes[node_a].set_link(node_b, score, raw_score, location, length)
        else:
            self.reverse_path(path_b, position)
            self.nodes[node_b].set_link(node_a, score, raw_score, location, length)
        
        self.links_added += 1
        return True
    
    def build_children_map(self):
        """Build a map from parent to list of children."""
        children = {i: [] for i in range(len(self.nodes))}
        for node in self.nodes:
            if node.score >= 0:  # Valid link
                children[node.parent].append(node.node_id)
        return children
    
    def find_root(self):
        """Find the root node (node pointing to itself or with score -1)."""
        roots = []
        for node in self.nodes:
            if node.score < 0 or node.parent == node.node_id:
                roots.append(node.node_id)
        
        if not roots:
            return 0
        
        # Find the root with the most descendants
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

    def report_twilight(self,f):

        def should_skip(r1, r2):
            """Check if this pair should be skipped and return the reason."""
            # Check if both contain "toxin"
            if 'toxin' in r1.name.lower() and 'toxin' in r2.name.lower():
                return 'toxins'
            
            # Check if either contains "uncharacterized" or "putative"
            if ('uncharacterized' in r1.name.lower() or 'uncharacterized' in r2.name.lower() or
                'putative' in r1.name.lower() or 'putative' in r2.name.lower()):
                return 'uncharacterized'
            
            if 'seed storage' in r1.name.lower() and 'seed storage' in r2.name.lower():
                return 'seed storage'

            return None

        finds = 0
        
        twilight_nodes = []
        for node in self.nodes:
            if 170 > node.score >= 0:
                twilight_nodes.append(node)
                finds += 1
                
        f.write(f"found {finds} finds\n")
        sorted_twilight_nodes = sorted(twilight_nodes, key=lambda node: node.score, reverse=True)
        
        skip_counts = {
            'toxins': 0,
            'uncharacterized': 0,
            'seed storage':0
        }
        
        total_skip_counts = {
            'toxins': 0,
            'uncharacterized': 0,
            'seed storage':0
        }

        for node in sorted_twilight_nodes:
            r1 = sequences.get_protein( node.node_id )
            r2 = sequences.get_protein( node.parent )
            
            # Check if we should skip this pair
            skip_reason = should_skip(r1, r2)
            if skip_reason:
                skip_counts[skip_reason] += 1
                total_skip_counts[skip_reason] += 1
                continue
            
            skip_string = ""
            # f.write skip message if we have skipped items, then reset
            if any(skip_counts.values()):
                skip_parts = [f"{count} {reason}" for reason, count in skip_counts.items() if count > 0]
                skip_string = f" [...skipped {' and '.join(skip_parts)}]"
                skip_counts = {key: 0 for key in skip_counts}
            
            # f.write the node information
            f.write(f"{node.node_id}-{node.parent} s({node.score}) {r1.id}-{r2.id} Length: {r1.sequence_length}/{r2.sequence_length}{skip_string}\n")
            f.write(f" {node.node_id}: {r1.name}\n")
            f.write(f" {node.parent}: {r2.name}\n")
            
        # f.write final totals at the end
        grand_total = sum(total_skip_counts.values())
        if grand_total > 0:
            f.write("\n" + "=" * 80)
            f.write("TOTAL SKIPPED:")
            for reason, count in total_skip_counts.items():
                if count > 0:
                    f.write(f"  {reason}: {count}")
            f.write(f"  Grand total: {grand_total}")
            f.write(f"  Leaving: {finds-grand_total} finds to check")

    
    def get_sorted_links(self):
        """Get all links sorted by score (descending)."""
        links = []
        for node in self.nodes:
            if node.score >= 0:
                links.append({
                    'child': node.node_id,
                    'parent': node.parent,
                    'score': node.score,
                    'raw_score': node.raw_score,
                    'location': node.location,
                    'length': node.length
                })
        links.sort(key=lambda x: x['score'], reverse=True)
        return links
    
    def write_ascii_tree(self, output_file, score_threshold=0, show_isolated=True):
        """
        Write ASCII tree to file.
        
        Args:
            output_file: File path to write to
            score_threshold: Stop descending branches below this score
            show_isolated: If True, also list nodes with no connections
        """
        with open(output_file, 'w') as f:
            root = self.find_root()
            children = self.build_children_map()
            
            # Track which nodes we've written
            written_nodes = set()
            
            # Write header
            f.write(f"Maximum Spanning Tree (root: node {root})\n")
            f.write(f"Total links: {self.links_added}\n")
            f.write("=" * 80 + "\n\n")
            
            # Sort children by link score for consistent ordering
            def get_sorted_children(parent_id):
                child_list = children[parent_id][:]
                child_list.sort(key=lambda c: self.nodes[c].score, reverse=True)
                return child_list
            
            # Recursive DFS to write tree
            def write_subtree(node_id, prefix="", is_last=True, depth=0, component=0):
                written_nodes.add(node_id)  # Track this node                
                node = self.nodes[node_id]
                
                # Determine tree graphics
                if depth == 0:
                    connector = ""
                    branch = ""
                else:
                    connector = "└─ " if is_last else "├─ "
                    branch = "   " if is_last else "│  "
                
                adjusted_len = max(0, len(prefix) - 40)
                start_index = adjusted_len - (adjusted_len % 40)
                short_prefix = f"{start_index}:{prefix[start_index:]}"
                # Write node info
                record = sequences.get_protein( node_id )
                if depth == 0:
                    f.write(f"{short_prefix}{connector}Node {node_id} [ROOT {component}] {record.name} \n")
                else:
                    f.write(f"{short_prefix}{connector}Node {node_id} (s:{node.score}) {record.name}\n")
                    #       f"(score={node.score}, raw={node.raw_score}, "
                    #       f"loc={node.location}, len={node.length})\n")
                
                # Get children of this node
                sorted_children = get_sorted_children(node_id)
                
                for i, child_id in enumerate(sorted_children):
                    child = self.nodes[child_id]
                    is_last_child = (i == len(sorted_children) - 1)
                    
                    # Check threshold
                    if score_threshold > 0 and child.score < score_threshold:
                        # Note the stub but don't descend
                        stub_prefix = prefix + branch
                        stub_connector = "└── " if is_last_child else "├── "
                        f.write(f"{stub_prefix}{stub_connector}[STUB: Node {child_id}, score {child.score} < threshold]\n")
                        continue
                    
                    new_prefix = prefix + branch
                    write_subtree(child_id, new_prefix, is_last_child, depth + 1)
            
            write_subtree(root, component=0)
            
            # After main tree, optionally show isolated nodes
            if show_isolated:
                # Find all nodes that haven't been written yet
                unwritten = [i for i in range(len(self.nodes)) if i not in written_nodes]
                
                if unwritten:
                    # Find roots of other components
                    other_roots = []
                    for node_id in unwritten:
                        node = self.nodes[node_id]
                        # Check if this is a root (points to itself or has no valid parent)
                        if node.score < 0 or node.parent == node_id:
                            other_roots.append(node_id)
                    
                    # Write each component
                    for component_num, component_root in enumerate(other_roots, start=2):
                        if component_root in written_nodes:
                            continue
            
                        write_subtree(component_root, component=component_num)
                    
                    # Check for truly isolated nodes (no links at all)
                    isolated = [i for i in range(len(self.nodes)) 
                               if i not in written_nodes and self.nodes[i].score < 0]
                    
                    if isolated:
                        f.write("\n" + "=" * 80 + "\n")
                        f.write(f"ISOLATED NODES (no connections): {len(isolated)}\n")
                        f.write("-" * 80 + "\n")
                        for node_id in isolated:
                            name = sequences.get_protein(node_id)
                            f.write(f"Node {node_id}: {name}\n")    

class MaxSpanningTreeArrays:
    def __init__(self, num_nodes):
        # Replaces TreeNode objects with parallel arrays
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

        # Iterate over all nodes, or just up to max_seen_id?
        # The arrays are full size, but valid nodes are likely concentrated.
        # But if we have sparse nodes, we must iterate to find them.
        # However, parent of any node must be valid.

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

    # Compatibility methods for reporting
    def report_twilight(self, f):

        def should_skip(r1, r2):
            if 'toxin' in r1.name.lower() and 'toxin' in r2.name.lower():
                return 'toxins'
            if ('uncharacterized' in r1.name.lower() or 'uncharacterized' in r2.name.lower() or
                'putative' in r1.name.lower() or 'putative' in r2.name.lower()):
                return 'uncharacterized'
            if 'seed storage' in r1.name.lower() and 'seed storage' in r2.name.lower():
                return 'seed storage'
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
                if 170 > scores[i] >= 0:
                    twilight_indices.append(i)
                    finds += 1
            sorted_twilight_indices = sorted(twilight_indices, key=lambda i: scores[i], reverse=True)

        f.write(f"found {finds} finds\n")

        skip_counts = {'toxins': 0, 'uncharacterized': 0, 'seed storage':0}
        total_skip_counts = {'toxins': 0, 'uncharacterized': 0, 'seed storage':0}

        for node_id in sorted_twilight_indices:
            parent_id = parents[node_id]
            r1 = sequences.get_protein(node_id)
            r2 = sequences.get_protein(parent_id)

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

            f.write(f"{node_id}-{parent_id} s({scores[node_id]}) {r1.id}-{r2.id} Length: {r1.sequence_length}/{r2.sequence_length}{skip_string}\n")
            f.write(f" {node_id}: {r1.name}\n")
            f.write(f" {parent_id}: {r2.name}\n")

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

                record = sequences.get_protein(node_id)
                if depth == 0:
                    f.write(f"{short_prefix}{connector}Node {node_id} [ROOT {component}] {record.name} \n")
                else:
                    f.write(f"{short_prefix}{connector}Node {node_id} (s:{self.scores[node_id]}) {record.name}\n")

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
                            record = sequences.get_protein(node_id)
                            f.write(f"Node {node_id}: {record.name}\n")

def process_links_file_legacy(filename, num_nodes):
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

def process_links_file(filename, num_nodes):
    tree = MaxSpanningTreeArrays(num_nodes)

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
    """Run the C++ implementation and return a MaxSpanningTreeArrays object."""
    temp_json = "temp_tree_output.json"

    cmd = ["bin/tree_builder_cpp", "-i", input_file, "-o", temp_json]
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

        tree = MaxSpanningTreeArrays(actual_num_nodes)
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

def main():
    parser = argparse.ArgumentParser(
        description='Build maximum spanning tree from protein similarity links',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -i links.csv -o tree.txt
  %(prog)s -i links.csv -o tree.txt --nodes 157000
  %(prog)s -i links.csv -o tree.txt --threshold 200
  %(prog)s -i links.csv -o tree.txt --threshold 200 --verbose
        """
    )
    
    parser.add_argument('-i', '--input', default="../nws_results/results.csv", help='Input CSV file with links (query_seq,target_seq,score,location,length)')
    parser.add_argument('-o', '--output', default="../nws_results/tree.txt",
                       help='Output file for ASCII tree')
    parser.add_argument('-n', '--nodes', type=int, default=None,
                       help='Number of nodes (proteins). If not specified, will be auto-detected from input file.')
    parser.add_argument('-t', '--threshold', type=int, default=-3,
                       help='Score threshold - stop descending below this (default: 0 = show all)')
    parser.add_argument('-v', '--verbose', action='store_true', default=True,
                       help='Print statistics and progress')
    parser.add_argument('--cpp', action='store_true', help='Use C++ backend for faster processing')
    
    args = parser.parse_args()
    
    if args.cpp:
        if args.verbose:
            print("Using C++ backend.")
        # C++ backend handles scanning if nodes not provided
        tree = run_cpp_tree_builder(args.input, args.nodes)
    else:
        num_nodes = args.nodes
        if num_nodes is None:
            if args.verbose:
                print(f"Scanning {args.input} to determine number of nodes...")
            max_id = scan_for_max_node_id(args.input)
            # Allocate enough space for max_id. Node IDs are 0-indexed, so we need max_id + 1
            num_nodes = max_id + 1
            if args.verbose:
                print(f"Detected {num_nodes} nodes.")

        if args.verbose:
            print(f"Building maximum spanning tree from {args.input}...")
            print(f"Number of nodes: {num_nodes}")

        # Use the new array-based implementation for the main CLI
        tree = process_links_file(args.input, num_nodes)
    
    if args.verbose:
        print(f"\nStatistics:")
        print(f"  Links processed: {tree.links_processed}")
        print(f"  Links added: {tree.links_added}")
        print(f"  Links rejected: {tree.links_rejected}")
        print(f"\nWriting ASCII tree to {args.output}...")
    
    with open("../nws_results/finds.txt", 'w') as f:    
        tree.report_twilight(f)
    tree.write_ascii_tree(args.output, args.threshold)
    
    if args.verbose:
        print("Done!")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sequences.get_protein( 5 )
        main()
        sys.exit()
        # No arguments provided - run test
        print("No arguments provided. Running test with test_links2.txt...\n")
        tree = process_links_file("test_links2.txt", num_nodes=6)
        print(f"Statistics:")
        print(f"  Links processed: {tree.links_processed}")
        print(f"  Links added: {tree.links_added}")
        print(f"  Links rejected: {tree.links_rejected}")
        print("\nWriting tree to test_tree.txt...")
        tree.write_ascii_tree("test_tree.txt")
        print("Done! Check test_tree.txt")
    else:
        main()