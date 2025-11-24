from Bio.PDB import PDBParser, Superimposer
import numpy as np
import argparse

def calculate_superposition(pdb_file_a, pdb_file_b, align_a_indices, align_b_indices):
    """
    align_a_indices: list of residue numbers in A that match B (0-indexed or PDB-indexed)
    """
    parser = PDBParser(QUIET=True)
    struct_a = parser.get_structure("A", pdb_file_a)
    struct_b = parser.get_structure("B", pdb_file_b)
    
    # Extract CA atoms for the aligned region ONLY
    # Assumption: You have mapped your SW alignment to PDB residue numbers
    atoms_a = [struct_a[0]['A'][i]['CA'] for i in align_a_indices if 'CA' in struct_a[0]['A'][i]]
    atoms_b = [struct_b[0]['A'][i]['CA'] for i in align_b_indices if 'CA' in struct_b[0]['A'][i]]
    
    # Calculate Rotation/Translation
    sup = Superimposer()
    sup.set_atoms(atoms_a, atoms_b) # A is fixed, B moves
    sup.apply(struct_b.get_atoms()) # Optional: verify locally
    
    # Get the matrix to send to frontend
    rot, tran = sup.rotran
    
    # Convert to 4x4 transformation matrix for WebGL/3Dmol
    # [ R00 R01 R02 T0 ]
    # [ R10 R11 R12 T1 ]
    # [ R20 R21 R22 T2 ]
    # [  0   0   0   1 ]
    matrix_4x4 = np.identity(4)
    matrix_4x4[:3, :3] = rot
    matrix_4x4[:3, 3] = tran
    
    return matrix_4x4.flatten().tolist()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kabsch 3D Alignment module")
    parser.add_argument("--test", action="store_true", help="Run test stub")
    args = parser.parse_args()

    if args.test:
        print("Kabsch 3D Align module test stub")
