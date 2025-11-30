from ete3 import NCBITaxa
import argparse
import os
from pathlib import Path

# Default database location
PROJECT_ROOT = Path(__file__).resolve().parent.parent
#DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "ncbi_taxonomy.db"
DEFAULT_DB_PATH = Path.home() / 'BigData' / 'bio_sequence_data' / 'ncbi_taxonomy.db'

# Initialize once (downloads database on first run)
# We'll initialize this in main() or when first needed
ncbi = None

# Define "Boring" Housekeeping Keywords
# If both proteins have any of these, we downgrade the "Surprise" score.
HOUSEKEEPING_KW = {
    'ribosom', 'histone', 'ubiquitin', 'actin', 'tubulin', 
    'chaperon', 'heat shock', 'polymerase', 'kinase', 'atpase',
    'elongation factor', 'dehydrogenase', 'synthase'
}


def initialize_ncbi(db_path=None):
    """Initialize the NCBI taxonomy database with a custom path."""
    global ncbi
    if ncbi is None:
        if db_path:
            # Ensure parent directory exists
            db_path = Path(db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            ncbi = NCBITaxa(dbfile=str(db_path))
        else:
            # Use default location
            DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            ncbi = NCBITaxa(dbfile=str(DEFAULT_DB_PATH))
        print(f"NCBI taxonomy database initialized at: {ncbi.dbfile}")
    return ncbi


def classify_pair(taxid_a, taxid_b, desc_a, desc_b):
    """
    Returns a tuple: (Category_Tag, Priority_Score, Human_Readable_Reason)
    Priority Score: 1 (High/Novel) to 5 (Low/Boring)
    """
    
    if ncbi is None:
        raise RuntimeError("NCBI taxonomy database not initialized. Call initialize_ncbi() first.")
    
    # 1. Check for Housekeeping (Text-based filter)
    is_housekeeping = False
    desc_combined = (desc_a + " " + desc_b).lower()
    if any(kw in desc_combined for kw in HOUSEKEEPING_KW):
        is_housekeeping = True

    # 2. Calculate Taxonomic Depth
    try:
        lineage_a = ncbi.get_lineage(taxid_a)
        lineage_b = ncbi.get_lineage(taxid_b)
        
        # Find Lowest Common Ancestor (LCA)
        common = set(lineage_a) & set(lineage_b)
        if not common:
            # Disconnected trees (e.g. Synthetic vs Natural or Viral vs Cell)
            lca_rank = "no rank"
            lca_distance = 0  # Most distant
        else:
            # Get the taxid of the LCA (the one deepest in the tree)
            lca_id = sorted(list(common), key=lambda x: len(ncbi.get_lineage(x)))[-1]
            ranks = ncbi.get_rank([lca_id])
            lca_rank = ranks[lca_id]
            
            # Calculate distance as the depth of the LCA in the tree
            # Higher depth = more recent common ancestor = closer organisms
            lca_distance = len(ncbi.get_lineage(lca_id))
            
    except (ValueError, KeyError) as e:
        return ("TaxID Error", 5, f"Invalid TaxID: {e}")

    # Define rank hierarchy from most distant to most specific
    # Using a numerical distance score is more robust than string matching
    RANK_HIERARCHY = {
        'no rank': 0,
        'root': 1,
        'cellular organisms': 2,
        'superkingdom': 3,
        'kingdom': 4,
        'subkingdom': 4,
        'phylum': 5,
        'subphylum': 5,
        'superclass': 6,
        'class': 7,
        'subclass': 7,
        'infraclass': 7,
        'cohort': 8,
        'superorder': 8,
        'order': 9,
        'suborder': 9,
        'infraorder': 9,
        'parvorder': 9,
        'superfamily': 10,
        'family': 11,
        'subfamily': 11,
        'tribe': 12,
        'subtribe': 12,
        'genus': 13,
        'subgenus': 13,
        'species group': 14,
        'species subgroup': 14,
        'species': 15,
        'subspecies': 16,
        'varietas': 17,
        'forma': 18
    }
    
    # Get rank level (default to 0 if unknown)
    rank_level = RANK_HIERARCHY.get(lca_rank, 0)
    
    print(f"LCA rank: '{lca_rank}' (level {rank_level}, distance {lca_distance})")
    
    # 3. Assign Category based on Rank Level & Housekeeping
    if rank_level <= 3:  # root, cellular organisms, superkingdom
        if is_housekeeping:
            return ("Deep Housekeeping", 4, f"Deep divergence ({lca_rank}) but likely ortholog")
        else:
            return ("Deep Novelty", 1, f"Major Discovery: {lca_rank} separation, non-housekeeping")
            
    elif rank_level <= 5:  # kingdom, phylum
        if is_housekeeping:
            return ("Distant Homolog", 4, "Common metabolic/structural gene")
        else:
            return ("High Value", 2, f"Inter-Phylum match ({lca_rank})")
            
    elif rank_level <= 11:  # class through family
        return ("Moderate Distance", 3, f"Same {lca_rank}")
        
    else:  # genus, species, and below
        return ("Close Relative", 5, "Likely paralog or recent speciation")


def test(db_path=None):
    """Smoke test - Multiple LCA calculations"""
    initialize_ncbi(db_path)
    
    print("=" * 60)
    print("Taxonomic Classification Test")
    print("=" * 60)
    print()
    
    # Test cases: (taxid_a, taxid_b, desc_a, desc_b, test_name)
    test_cases = [
        (9606, 562, "Hemoglobin subunit alpha", "Cytochrome oxidase", 
         "Human vs E. coli (Very distant)"),
        
        (9606, 10090, "Beta-actin", "Beta-actin", 
         "Human vs Mouse (Housekeeping, close)"),
        
        (7227, 6239, "Developmental protein", "Developmental protein", 
         "Fruit fly vs Roundworm (Moderate)"),
        
        (9606, 4932, "Ribosomal protein", "Ribosomal protein", 
         "Human vs Yeast (Distant, housekeeping)"),
    ]
    
    for i, (taxid_a, taxid_b, desc_a, desc_b, test_name) in enumerate(test_cases, 1):
        print(f"Test {i}: {test_name}")
        print(f"  Organism A: TaxID {taxid_a} - {desc_a}")
        print(f"  Organism B: TaxID {taxid_b} - {desc_b}")
        
        result = classify_pair(taxid_a, taxid_b, desc_a, desc_b)
        
        print(f"  Result: {result[0]} (Priority: {result[1]})")
        print(f"  Reason: {result[2]}")
        print()
    
    print("=" * 60)
    print(f"All {len(test_cases)} tests completed successfully!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Taxa LCA module - classifies protein pairs by taxonomic distance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  %(prog)s --test\n"
               "  %(prog)s --test --db-path /custom/path/taxonomy.db\n"
    )
    
    # Database location
    parser.add_argument('--db-path', type=Path, default=None,
                        help=f'Path to NCBI taxonomy database (default: {DEFAULT_DB_PATH})')
    
    # Test mode
    parser.add_argument('--no-test', action='store_false', dest='test',
                        help='Disable test mode')
    parser.add_argument('--test', action='store_true', dest='test',
                        help='Enable test mode (default)')
    parser.set_defaults(test=True)
    
    args = parser.parse_args()

    if not args.test:
        parser.print_help()
        exit(0)

    """ Smoke test - One LCA calculation """
    print(f"Running in test mode...")
    test(db_path=args.db_path)