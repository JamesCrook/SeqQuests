import requests
import os
import numpy as np
from pathlib import Path
from Bio.PDB import PDBParser, Superimposer
import argparse
import json


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Cache directory to avoid re-downloading 150k structures
PDB_CACHE_DIR = PROJECT_ROOT / "pdb_cache"
PDB_CACHE_DIR.mkdir(exist_ok=True)


def get_alphafold_atoms(uniprot_id, aligned_indices):
    """
    1. Downloads AlphaFold PDB for uniprot_id (if not cached).
    2. Parses it.
    3. Extracts CA atoms corresponding to the aligned_indices (0-based).
    
    aligned_indices: List of integers [0, 1, 2, 10, 11...] representing 
                     positions in the SEQUENCE that matched.
    """
    
    # AlphaFold DB v6 uses the new format: AF-{UNIPROT_ID}-F1
    # For programmatic access, they recommend using the API to get the latest version
    alphafold_id = f"AF-{uniprot_id}-F1"
    
    # The URL format changed - now uses the alphafold_id directly
    # Latest version is v6, but for backwards compatibility, try v4 first, then v6
    pdb_filename = f"{alphafold_id}-model_v4.pdb"
    local_path = PDB_CACHE_DIR / pdb_filename
    
    # Try v4 URL first (most common)
    url_v4 = f"https://alphafold.ebi.ac.uk/files/{alphafold_id}-model_v4.pdb"
    # Fallback to v6 if v4 doesn't exist
    url_v6 = f"https://alphafold.ebi.ac.uk/files/{alphafold_id}-model_v6.pdb"
    
    # Fetch if missing
    if not local_path.exists():
        print(f"Fetching {uniprot_id} (AlphaFold ID: {alphafold_id})...")
        
        # Try v4 first
        response = requests.get(url_v4)
        if response.status_code != 200:
            # Try v6
            print(f"  v4 not found, trying v6...")
            response = requests.get(url_v6)
            pdb_filename = f"{alphafold_id}-model_v6.pdb"
            local_path = PDB_CACHE_DIR / pdb_filename
        
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(response.content)
            print(f"  Downloaded to {local_path}")
        else:
            # Handle 404 (No AlphaFold model exists or ID is secondary)
            print(f"Warning: No AlphaFold model for {uniprot_id} (HTTP {response.status_code})")
            print(f"  Tried: {url_v4}")
            print(f"  Tried: {url_v6}")
            return None
    else:
        print(f"Using cached {pdb_filename}")
    
    # Parse PDB
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure(uniprot_id, str(local_path))
    model = structure[0] # AlphaFold structures only have 1 model
    chain = model['A']   # AlphaFold structures only have Chain A
    
    atoms = []
    
    # Map Sequence Index (0-based) to PDB Residue ID (1-based)
    for seq_idx in aligned_indices:
        pdb_res_id = seq_idx + 1 
        
        # Safety check: Does this residue exist in the PDB?
        if pdb_res_id in chain:
            residue = chain[pdb_res_id]
            if 'CA' in residue:
                atoms.append(residue['CA'])
            else:
                # Should not happen in AlphaFold (all atoms present)
                print(f"Warning: CA atom missing for residue {pdb_res_id} in {uniprot_id}")
        else:
            # This happens if the SwissProt sequence was updated 
            # after AlphaFold generated the model (rare but possible)
            print(f"Warning: Index mismatch: seq_idx {seq_idx} (PDB res {pdb_res_id}) not found in {uniprot_id}")
    
    return atoms if atoms else None


def calculate_superposition(atoms_A, atoms_B):
    """
    Calculate superposition (rotation + translation) to align atoms_B onto atoms_A.
    
    Returns:
        dict with 'rotation' (3x3 matrix), 'translation' (3-vector), and 'rmsd'
    """
    if len(atoms_A) != len(atoms_B):
        raise ValueError(f"Atom count mismatch: {len(atoms_A)} vs {len(atoms_B)}")
    
    # Use BioPython's Superimposer
    sup = Superimposer()
    sup.set_atoms(atoms_A, atoms_B)
    
    rotation = sup.rotran[0]  # 3x3 rotation matrix
    translation = sup.rotran[1]  # 3-vector translation
    rmsd = sup.rms
    
    return {
        'rotation': rotation,
        'translation': translation,
        'rmsd': rmsd
    }

def save_alignment_result(uniprot_A, uniprot_B, result, output_file):
    """Save alignment results for frontend use"""
    data = {
        'protein_A': uniprot_A,
        'protein_B': uniprot_B,
        'rmsd': float(result['rmsd']),
        'rotation_matrix': result['rotation'].tolist(),
        'translation_vector': result['translation'].tolist()
    }
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\nAlignment results saved to {output_file}")

def apply_transformation(atoms, rotation, translation):
    """Apply rotation and translation to a list of atoms"""
    transformed_coords = []
    for atom in atoms:
        # coord @ rotation.T + translation
        new_coord = np.dot(atom.coord, rotation.T) + translation
        transformed_coords.append(new_coord)
    return transformed_coords

def test():
    print(f"Running in test mode...")
    print("=" * 60)
    
    # Real test case: Two well-studied globins
    # These are smaller proteins that should download quickly
    
    # Human myoglobin (154 amino acids) - oxygen storage protein
    uniprot_A = "P02144"
    # Sperm whale myoglobin (154 amino acids) - the classic myoglobin structure
    uniprot_B = "P02185"
    
    # Test with a conserved helical region (residues 20-40)
    indices_A = list(range(20, 41))  # [20, 21, 22, ..., 40]
    indices_B = list(range(20, 41))  # Same positions in the aligned sequence
    
    print(f"\nTest proteins:")
    print(f"  Protein A: {uniprot_A} (Human myoglobin)")
    print(f"  Protein B: {uniprot_B} (Sperm whale myoglobin)")
    print(f"  Aligned region: residues {indices_A[0]}-{indices_A[-1]} ({len(indices_A)} residues)")
    print()
    
    atoms_A = get_alphafold_atoms(uniprot_A, indices_A)
    print()
    atoms_B = get_alphafold_atoms(uniprot_B, indices_B)
    print()
    
    if atoms_A is None or atoms_B is None:
        print("Error: Failed to fetch one or both structures")
        print("\nNote: AlphaFold DB recently updated to v6. Some protein IDs may have changed.")
        print("You can check if a protein exists at: https://alphafold.ebi.ac.uk/")
        return
    
    if len(atoms_A) != len(atoms_B):
        print(f"Error: Atom count mismatch: {len(atoms_A)} vs {len(atoms_B)}")
        return
    
    print(f"Successfully extracted {len(atoms_A)} CA atoms from each structure")
    
    # Calculate superposition
    print("\nCalculating superposition...")
    result = calculate_superposition(atoms_A, atoms_B)
    
    print("\nSuperposition Results:")
    print(f"  RMSD: {result['rmsd']:.3f} Å")
    print(f"  (Lower RMSD = better structural similarity)")
    print(f"\n  Rotation matrix:")
    for row in result['rotation']:
        print(f"    [{row[0]:7.4f} {row[1]:7.4f} {row[2]:7.4f}]")
    print(f"\n  Translation vector:")
    print(f"    [{result['translation'][0]:7.4f} {result['translation'][1]:7.4f} {result['translation'][2]:7.4f}]")
    
    # Some example coordinates
    print(f"\n  Example: First CA atom of protein A at {atoms_A[0].coord}")
    print(f"           First CA atom of protein B at {atoms_B[0].coord}")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("\nNote: You can save this matrix to DB/JSON for frontend visualization")
    print("The rotation matrix and translation can be used to transform protein B")
    print("coordinates to align with protein A in 3D visualization tools.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AlphaFold structure alignment tool",
        epilog="Fetches AlphaFold v4/v6 structures and calculates superposition matrices"
    )
    parser.add_argument('--no-test', action='store_false', dest='test',
                        help='Disable test mode')
    parser.add_argument('--test', action='store_true', dest='test',
                        help='Enable test mode (default)')
    # Use from command line currently only for testing, so is the default
    parser.set_defaults(test=True)    
    
    args = parser.parse_args()
    
    if not args.test:
        parser.print_help()
        exit(0)
    
    """ Smoke test - will the alignment work? """
    test()