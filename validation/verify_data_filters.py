from data_munger import filter_proteins
from sequences import read_swissprot_sequences

"""
Data Filter Validator - Verifies protein filtering logic on real Swiss-Prot data.

This tool checks that the data_munger filtering functions correctly extract
subsets of proteins based on biological criteria (organism, GO terms, etc.).

Usage:
    python validation/verify_data_filters.py

When to run:
- After modifying filtering logic in data_munger.py
- When setting up a new filtered dataset for analysis
- To verify biological filtering criteria work as expected

Example validation:
- Filters for mouse proteins (organism='Mus musculus')
- Confirms returned proteins actually match the criteria

Note: Uses real Swiss-Prot database, not mock data. This catches edge cases
in real biological data that synthetic tests would miss.

Double-duty potential: This could be extended into a data exploration tool
for querying "show me all proteins matching criteria X".
"""

def test_filter_for_mouse_proteins():
    all_records = read_swissprot_sequences()

    # Correctly call the generator and convert to a list
    mouse_proteins = list(filter_proteins(all_records, organisms=['mouse']))

    # Assert that at least one mouse protein is found
    assert len(mouse_proteins) > 0, "No mouse proteins found"

    # Optional: Check if all returned proteins are actually from mouse
    for protein in mouse_proteins:
        assert "Mus musculus" in protein.organism, f"Protein {protein.accessions[0]} is not a mouse protein"

if __name__ == "__main__":
    test_filter_for_mouse_proteins()
    print("Test passed: filter_proteins correctly filters for mouse proteins.")
