from ete3 import NCBITaxa
import argparse

# Initialize once (downloads database on first run)
# ncbi = NCBITaxa()

# Define "Boring" Housekeeping Keywords
# If both proteins have any of these, we downgrade the "Surprise" score.
HOUSEKEEPING_KW = {
    'ribosom', 'histone', 'ubiquitin', 'actin', 'tubulin', 
    'chaperon', 'heat shock', 'polymerase', 'kinase', 'atpase',
    'elongation factor', 'dehydrogenase', 'synthase'
}

def classify_pair(taxid_a, taxid_b, desc_a, desc_b):
    """
    Returns a tuple: (Category_Tag, Priority_Score, Human_Readable_Reason)
    Priority Score: 1 (High/Novel) to 5 (Low/Boring)
    """
    
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
            lca_rank = "No Common Ancestor"
        else:
            # Get the taxid of the LCA (the one with the longest lineage list in the intersection)
            # A simple heuristic is sorting by lineage length implies specificity
            lca_id = sorted(list(common), key=lambda x: len(ncbi.get_lineage(x)))[-1]
            ranks = ncbi.get_rank([lca_id])
            lca_rank = ranks[lca_id]
    except ValueError:
        return ("TaxID Error", 5, "Invalid TaxID")

    # 3. Assign Category based on Rank & Housekeeping
    # Ranks: superkingdom, kingdom, phylum, class, order, family, genus, species
    
    if lca_rank in ['cellular organisms', 'root', 'superkingdom']:
        if is_housekeeping:
            return ("Deep Housekeeping", 4, f"Deep divergence ({lca_rank}) but likely ortholog")
        else:
            return ("Deep Novelty", 1, f"Major Discovery: {lca_rank} separation, non-housekeeping")
            
    elif lca_rank in ['kingdom', 'phylum']:
        if is_housekeeping:
            return ("Distant Homolog", 4, "Common metabolic/structural gene")
        else:
            return ("High Value", 2, f"Inter-Phylum match ({lca_rank})")
            
    elif lca_rank in ['class', 'order', 'family']:
        return ("Moderate Distance", 3, f"Same {lca_rank}")
        
    else: # Genus, Species
        return ("Close Relative", 5, "Likely paralog or recent speciation")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Taxa LCA module")
    parser.add_argument("--test", action="store_true", help="Run test stub")
    args = parser.parse_args()

    if args.test:
        print("Taxa LCA module test stub")
