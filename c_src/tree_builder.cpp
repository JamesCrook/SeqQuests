#include <iostream>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <stdexcept>
#include <map>

class MaxSpanningTree {
public:
    int num_nodes;
    int max_seen_id;

    std::vector<int> parents;
    std::vector<int> scores;
    std::vector<int> raw_scores;
    std::vector<int> locations;
    std::vector<int> lengths;

    long long links_processed;
    long long links_added;
    long long links_rejected;

    // Traversal optimization
    std::vector<int> visited_a_indices;
    std::vector<int> visited_b_indices;
    std::vector<int> visited_a_search_ids;
    std::vector<int> visited_b_search_ids;
    int search_id;

    MaxSpanningTree(int n) : num_nodes(n) {
        max_seen_id = 0;
        parents.assign(n, 0);
        scores.assign(n, -1);
        raw_scores.assign(n, -1);
        locations.assign(n, -1);
        lengths.assign(n, -1);

        links_processed = 0;
        links_added = 0;
        links_rejected = 0;

        visited_a_indices.assign(n, -1);
        visited_b_indices.assign(n, -1);
        visited_a_search_ids.assign(n, 0);
        visited_b_search_ids.assign(n, 0);
        search_id = 0;
    }

    void set_link(int node_id, int parent, int score, int raw_score, int location, int length) {
        parents[node_id] = parent;
        scores[node_id] = score;
        raw_scores[node_id] = raw_score;
        locations[node_id] = location;
        lengths[node_id] = length;

        if (node_id > max_seen_id) max_seen_id = node_id;
        if (parent > max_seen_id) max_seen_id = parent;
    }

    // Returns meeting_node, path_a, path_b
    // path_a and path_b are vectors of node IDs
    bool find_meeting_point(int node_a, int node_b, int& meeting_node, std::vector<int>& path_a, std::vector<int>& path_b) {
        search_id++;
        path_a.clear();
        path_b.clear();

        int current_a = node_a;
        int current_b = node_b;
        bool a_active = true;
        bool b_active = true;

        // Since 0 can be a valid node ID but the loop condition in Python was complicated by 0 checks,
        // let's look at the Python logic closely:
        // if current_a == 0: current_a = None (stops traversal)
        // This implies node 0 is a stopper or root.
        // In Python: `parents = [0] * num_nodes`, so default parent is 0.
        // If we reach 0, we stop adding to path, but we do mark 0 as visited?
        // Python:
        //   if current_a is not None:
        //     ... mark visited ...
        //     if current_a == 0: current_a = None
        //     else: path_a.append(current_a); current_a = parents[current_a]

        // In C++, we use -1 or a flag to indicate None. Let's use -1 for 'active' check.

        while (true) {
            if (a_active) {
                // Check if b visited this node
                if (visited_b_search_ids[current_a] == search_id) {
                    meeting_node = current_a;
                    // Trim path_b to meeting index
                    int meeting_index = visited_b_indices[current_a];
                    if (meeting_index < path_b.size()) {
                        path_b.resize(meeting_index);
                    }
                    return true;
                }

                // Mark as visited by a
                visited_a_search_ids[current_a] = search_id;
                visited_a_indices[current_a] = (int)path_a.size();

                if (current_a == 0) {
                    a_active = false;
                } else {
                    path_a.push_back(current_a);
                    current_a = parents[current_a];
                }
            }

            if (b_active) {
                // Check if a visited this node
                if (visited_a_search_ids[current_b] == search_id) {
                    meeting_node = current_b;
                    // Trim path_a to meeting index
                    int meeting_index = visited_a_indices[current_b];
                    if (meeting_index < path_a.size()) {
                        path_a.resize(meeting_index);
                    }
                    return true;
                }

                // Mark as visited by b
                visited_b_search_ids[current_b] = search_id;
                visited_b_indices[current_b] = (int)path_b.size();

                if (current_b == 0) {
                    b_active = false;
                } else {
                    path_b.push_back(current_b);
                    current_b = parents[current_b];
                }
            }

            if (!a_active && !b_active) {
                // Exception: Paths didn't meet
                return false;
            }
        }
    }

    // Returns min_score, which_path ('a', 'b', or 'n' for new), position
    void find_weakest_link_in_cycle(const std::vector<int>& path_a, const std::vector<int>& path_b, int new_score,
                                   int& min_score, char& which_path, int& position) {
        min_score = new_score;
        which_path = 'n'; // 'new'
        position = -1;

        for (size_t i = 0; i < path_a.size(); i++) {
            int node_id = path_a[i];
            int link_score = scores[node_id];
            if (link_score < min_score) {
                min_score = link_score;
                which_path = 'a';
                position = (int)i;
            }
        }

        for (size_t i = 0; i < path_b.size(); i++) {
            int node_id = path_b[i];
            int link_score = scores[node_id];
            if (link_score < min_score) {
                min_score = link_score;
                which_path = 'b';
                position = (int)i;
            }
        }
    }

    void reverse_path(const std::vector<int>& path, int up_to_index) {
        for (int i = up_to_index; i > 0; i--) {
            int current_node_id = path[i];
            int prev_node_id = path[i-1];

            // Set current node's link to point to prev node
            // using prev node's link properties
            set_link(
                current_node_id,
                prev_node_id,
                scores[prev_node_id],
                raw_scores[prev_node_id],
                locations[prev_node_id],
                lengths[prev_node_id]
            );
        }

        // path[0] points nowhere (becomes root of subtree or new connection)
        int start_node_id = path[0];
        set_link(start_node_id, start_node_id, -1, -1, -1, -1);
    }

    bool add_link(int node_a, int node_b, int score, int raw_score, int location, int length) {
        links_processed++;

        if (node_a > max_seen_id) max_seen_id = node_a;
        if (node_b > max_seen_id) max_seen_id = node_b;

        if (node_a == node_b) return false;

        int meeting_node;
        std::vector<int> path_a, path_b;
        if (!find_meeting_point(node_a, node_b, meeting_node, path_a, path_b)) {
            // Should not happen if logic is correct
            return false;
        }

        int min_score, position;
        char which_path;
        find_weakest_link_in_cycle(path_a, path_b, score, min_score, which_path, position);

        if (which_path == 'n') {
            links_rejected++;
            return false;
        }

        if (which_path == 'a') {
            reverse_path(path_a, position);
            set_link(node_a, node_b, score, raw_score, location, length);
        } else {
            reverse_path(path_b, position);
            set_link(node_b, node_a, score, raw_score, location, length);
        }

        links_added++;
        return true;
    }

    // Post-processing methods

    // Returns sorted list of indices
    std::vector<int> get_twilight_nodes() {
        std::vector<int> twilight;
        int limit = std::min(max_seen_id + 1, num_nodes);
        for (int i = 0; i < limit; i++) {
            if (scores[i] >= 0 && scores[i] < 300) {
                twilight.push_back(i);
            }
        }
        std::sort(twilight.begin(), twilight.end(), [this](int a, int b) {
            return scores[a] > scores[b];
        });
        return twilight;
    }

    std::vector<std::vector<int>> build_children_map() {
        int limit = std::min(max_seen_id + 1, num_nodes);
        std::vector<std::vector<int>> children(limit);

        for (int i = 0; i < limit; i++) {
            if (scores[i] >= 0) {
                int p = parents[i];
                if (p < limit) {
                    children[p].push_back(i);
                }
            }
        }

        // Sort children by score descending
        for (auto& list : children) {
            std::sort(list.begin(), list.end(), [this](int a, int b) {
                return scores[a] > scores[b];
            });
        }
        return children;
    }

    int find_root() {
        std::vector<int> roots;
        int limit = std::min(max_seen_id + 1, num_nodes);

        for (int i = 0; i < limit; i++) {
            if (scores[i] < 0 || parents[i] == i) {
                roots.push_back(i);
            }
        }

        if (roots.empty()) return 0;
        if (roots.size() == 1) return roots[0];

        // With multiple components, find the one with most descendants
        // This requires a temporary children map (unsorted is fine)
        std::vector<std::vector<int>> children(limit);
        for (int i = 0; i < limit; i++) {
            if (scores[i] >= 0) {
                children[parents[i]].push_back(i);
            }
        }

        int best_root = roots[0];
        int max_desc = -1;

        for (int r : roots) {
            int count = count_descendants(r, children);
            if (count > max_desc) {
                max_desc = count;
                best_root = r;
            }
        }

        return best_root;
    }

    int count_descendants(int node, const std::vector<std::vector<int>>& children) {
        int count = (int)children[node].size();
        for (int child : children[node]) {
            count += count_descendants(child, children);
        }
        return count;
    }
};

int scan_for_max_node_id(const std::string& filename) {
    std::ifstream infile(filename);
    if (!infile.is_open()) return 0;

    std::string line;
    if (!std::getline(infile, line)) return 0; // Skip header

    int max_id = 0;
    int old_id = 0;
    while (std::getline(infile, line)) {
        size_t comma_pos = line.find(',');
        if (comma_pos != std::string::npos) {
            try {
                int id = std::stoi(line.substr(0, comma_pos));
                if (id > max_id) max_id = id;

                if( id > old_id ){
                    old_id = id;
                    if (id % 1000 == 0) {
                        std::cout << "scanned: " << id <<  std::endl;
                    }
                }

            } catch (...) {}
        }
    }
    return max_id;
}

// Simple JSON writer
void write_json(std::ostream& out, MaxSpanningTree& tree) {
    out << "{\n";
    out << "  \"links_processed\": " << tree.links_processed << ",\n";
    out << "  \"links_added\": " << tree.links_added << ",\n";
    out << "  \"links_rejected\": " << tree.links_rejected << ",\n";
    out << "  \"max_seen_id\": " << tree.max_seen_id << ",\n";

    auto print_array = [&](const char* name, const std::vector<int>& arr) {
        out << "  \"" << name << "\": [";
        for (size_t i = 0; i < arr.size(); i++) {
            out << arr[i];
            if (i < arr.size() - 1) out << ",";
        }
        out << "],\n";
    };

    print_array("parents", tree.parents);
    print_array("scores", tree.scores);
    print_array("raw_scores", tree.raw_scores);
    print_array("locations", tree.locations);
    print_array("lengths", tree.lengths);

    // Computed data
    auto twilight = tree.get_twilight_nodes();
    print_array("twilight_nodes", twilight);

    out << "  \"root\": " << tree.find_root() << ",\n";

    auto children = tree.build_children_map();
    out << "  \"children\": [";
    for (size_t i = 0; i < children.size(); i++) {
        out << "[";
        for (size_t j = 0; j < children[i].size(); j++) {
            out << children[i][j];
            if (j < children[i].size() - 1) out << ",";
        }
        out << "]";
        if (i < children.size() - 1) out << ",";
    }
    out << "]\n";

    out << "}\n";
}

int main(int argc, char* argv[]) {
    std::string input_file;
    std::string output_file;
    int num_nodes = -1;

    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "-i" && i + 1 < argc) {
            input_file = argv[++i];
        } else if (arg == "-o" && i + 1 < argc) {
            output_file = argv[++i];
        } else if (arg == "-n" && i + 1 < argc) {
            num_nodes = std::stoi(argv[++i]);
        }
    }

    if (input_file.empty() || output_file.empty()) {
        std::cerr << "Usage: " << argv[0] << " -i <input_csv> -o <output_json> [-n <num_nodes>]" << std::endl;
        return 1;
    }

    if (num_nodes == -1) {
        std::cout << "Scanning for max node ID..." << std::endl;
        num_nodes = scan_for_max_node_id(input_file) + 1;
        std::cout << "Detected " << num_nodes << " nodes." << std::endl;
    }

    MaxSpanningTree tree(num_nodes);

    std::cout << "Processing " << input_file << "..." << std::endl;
    std::ifstream infile(input_file);
    if (!infile.is_open()) {
        std::cerr << "Error opening input file" << std::endl;
        return 1;
    }

    std::string line;
    // Skip header
    if (!std::getline(infile, line)) return 0;

    int old_query = -1;
    while (std::getline(infile, line)) {
        std::stringstream ss(line);
        std::string segment;
        std::vector<std::string> parts;

        while (std::getline(ss, segment, ',')) {
            parts.push_back(segment);
        }

        if (parts.size() < 5) continue;

        try {
            int query = std::stoi(parts[0]);
            int target = std::stoi(parts[1]);
            int score = std::stoi(parts[2]);
            int location = std::stoi(parts[3]);
            int length = std::stoi(parts[4]);

            if (query != old_query) {
                old_query = query;
                if (query % 1000 == 0) {
                    std::cout << "addlink: " << query << "\t" << target << std::endl;
                }
            }

            if (query >= num_nodes || target >= num_nodes) continue;

            tree.add_link(query, target, score, score, location, length);

        } catch (const std::exception& e) {
            continue;
        }
    }

    std::cout << "Writing JSON to " << output_file << "..." << std::endl;
    std::ofstream outfile(output_file);
    write_json(outfile, tree);

    std::cout << "Done." << std::endl;

    return 0;
}
