import requests
import os
from Bio.PDB import PDBParser

# Cache directory to avoid re-downloading 150k structures
PDB_CACHE_DIR = "./pdb_cache"
if not os.path.exists(PDB_CACHE_DIR):
    os.makedirs(PDB_CACHE_DIR)

def get_alphafold_atoms(uniprot_id, aligned_indices):
    """
    1. Downloads AlphaFold PDB for uniprot_id (if not cached).
    2. Parses it.
    3. Extracts CA atoms corresponding to the aligned_indices (0-based).
    
    aligned_indices: List of integers [0, 1, 2, 10, 11...] representing 
                     positions in the SEQUENCE that matched.
    """
    
    # 1. Construct Path & URL
    # Note: v4 is current best practice. 'F1' covers 98% of proteins.
    pdb_filename = f"AF-{uniprot_id}-F1-model_v4.pdb"
    local_path = os.path.join(PDB_CACHE_DIR, pdb_filename)
    url = f"https://alphafold.ebi.ac.uk/files/{pdb_filename}"

    # 2. Fetch if missing
    if not os.path.exists(local_path):
        print(f"Fetching {uniprot_id}...")
        response = requests.get(url)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(response.content)
        else:
            # Handle 404 (No AlphaFold model exists or ID is secondary)
            print(f"Warning: No AlphaFold model for {uniprot_id}")
            return None

    # 3. Parse PDB
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure(uniprot_id, local_path)
    model = structure[0] # AlphaFold structures only have 1 model
    chain = model['A']   # AlphaFold structures only have Chain A
    
    atoms = []
    
    # 4. Map Sequence Index (0-based) to PDB Residue ID (1-based)
    for seq_idx in aligned_indices:
        pdb_res_id = seq_idx + 1 
        
        # Safety check: Does this residue exist in the PDB?
        if pdb_res_id in chain:
            residue = chain[pdb_res_id]
            if 'CA' in residue:
                atoms.append(residue['CA'])
            else:
                # Should not happen in AlphaFold (all atoms present)
                pass 
        else:
            # This happens if the SwissProt sequence was updated 
            # after AlphaFold generated the model (rare but possible)
            print(f"Index mismatch: {seq_idx} not found in {uniprot_id}")

    return atoms

# Example usage:
indices_A = [10, 11, 12, ...] 
indices_B = [45, 46, 47, ...] 
atoms_A = get_alphafold_atoms("P12345", indices_A)
atoms_B = get_alphafold_atoms("Q98765", indices_B)

if atoms_A and atoms_B and len(atoms_A) == len(atoms_B):
    # Calculate rotation matrix (using the Bio.PDB code from previous turn)
    matrix = calculate_superposition(atoms_A, atoms_B)
    # Save matrix to DB/JSON for the frontend to read    