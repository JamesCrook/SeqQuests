from py.data_munger import filter_proteins
from py.sequences import read_dat_records

def test_filter_for_mouse_proteins():
    all_records = read_dat_records()

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
