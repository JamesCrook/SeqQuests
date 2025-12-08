#!/usr/bin/env python3
"""
Script to process substitution matrices (e.g., Dayhoff 250 PAM) and create a lookup table for a sequence.
If the aa sequence has 200 amino acids, this creates a 200x32 lut table.
"""

import numpy as np
from Bio import SeqIO
from Bio.Align import substitution_matrices
import sequences
import argparse

def convert_pam_to_32x32(matrix_name="PAM250"):
    """
    Read substitution matrix and convert to 32x32 array.
    Values are scaled to max_value and rounded to integers.
    Indexes are amino acid letters mod 32.
    
    Args:
        matrix_name: Name of the substitution matrix (e.g., "PAM250", "BLOSUM62")
    """
    # Load the substitution matrix
    try:
        matrix = substitution_matrices.load(matrix_name)
    except Exception as e:
        print(f"Error loading matrix '{matrix_name}': {e}")
        print("\nAvailable matrices:")
        for name in sorted(substitution_matrices.load()):
            print(f"  {name}")
        raise
    
    # Initialize 32x32 array with zeros
    pam_32x32 = np.zeros((32, 32), dtype=int)
    
    # Get the amino acid alphabet from the matrix
    aa_letters = list(matrix.alphabet)
    
    # Find min and max values in the original matrix for scaling
    values = []
    for aa1 in aa_letters:
        for aa2 in aa_letters:
            values.append(matrix[aa1, aa2])
    
    min_val = min(values)
    max_val = max(values)
    
    print(f"Original {matrix_name} range: [{min_val}, {max_val}]")
    
    # Fill the 32x32 array
    for aa1 in aa_letters:
        for aa2 in aa_letters:
            # Get indices mod 32 using ASCII values
            idx1 = ord(aa1) % 32
            idx2 = ord(aa2) % 32
            
            # Scale and round the value
            original_val = matrix[aa1, aa2]
            rounded_val = int(round(original_val))
            
            pam_32x32[idx1, idx2] = rounded_val

    # For stop char @, huge penalty.
    for i in range(32):
        pam_32x32[0, i] = -32767
        pam_32x32[i, 0] = -32767
    
    return pam_32x32, aa_letters


def make_fasta_lut(fasta_rec, pam_32x32):
    """
    Read first sequence from FASTA file and create PamLut array.
    """
    
    sequence = str(fasta_rec.seq)
    seq_length = len(sequence)
    
    print(f"\nSearching with: {fasta_rec.id}")
    print(f"Description: {fasta_rec.description}")
    print(f"Sequence length: {seq_length}")
    print(f"First 50 characters: {sequence[:50]}...")
    
    # Create array with each entry as amino acid mod 32
    seq_mod32 = np.array([ord(aa) % 32 for aa in sequence], dtype=int)
    
    # Create PamLut array 32 x seq_length)
    pam_lut = np.zeros((32, seq_length), dtype=int)
    
    # Fill PamLut by looking up each sequence position against all 32 possible AA values
    for col in range(32):
        for i, aa_idx in enumerate(seq_mod32):
            pam_lut[col, i] = pam_32x32[col, aa_idx]
    
    return pam_lut, sequence


def list_available_matrices():
    """List all available substitution matrices."""
    print("Available substitution matrices:")
    for name in sorted(substitution_matrices.load()):
        print(f"  {name}")


def main():
    parser = argparse.ArgumentParser(
        description="Substitution matrix converter utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  %(prog)s --matrix PAM250\n"
               "  %(prog)s --matrix BLOSUM62\n"
               "  %(prog)s --list-matrices\n"
    )
    parser.add_argument('--matrix', '-m', type=str, default='PAM250',
                        help='Substitution matrix name (default: PAM250)')
    parser.add_argument('--list-matrices', '-l', action='store_true',
                        help='List all available substitution matrices and exit')
    parser.add_argument('--no-test', action='store_false', dest='test',
                        help='Disable test mode')
    parser.add_argument('--test', action='store_true', dest='test',
                        help='Enable test mode (default)')
    parser.set_defaults(test=True)
    
    args = parser.parse_args()

    # Handle list matrices request
    if args.list_matrices:
        list_available_matrices()
        return

    if not args.test:
        parser.print_help()
        return

    """ Smoke test - will subroutines run? """
    # Convert substitution matrix table to 32x32
    print(f"Running in test mode...")
    print("=" * 60)
    print(f"Converting {args.matrix} substitution matrix to 32x32 array")
    print("=" * 60)
    
    pam_32x32, aa_letters = convert_pam_to_32x32(args.matrix)
    
    print("Converted 32x32 array (diagnostic):")
    print("Shape:", pam_32x32.shape)
    print("\nFull array:")
    print(pam_32x32)
    print()
    
    # Show mapping of amino acids to indices
    print("\nAmino acid to index (mod 32) mapping:")
    for aa in sorted(aa_letters):
        idx = ord(aa) % 32
        print(f"  {aa} -> {idx}")
    
    iter = sequences.read_fasta_sequences()
    first_record = next(iter)
    
    print("\n" + "=" * 60)
    print("Processing FASTA sequence")
    print("=" * 60)
    
    pam_lut, sequence = make_fasta_lut(first_record, pam_32x32)
    
    print("\nPamLut array shape:", pam_lut.shape)
    print("\nTop 5x5 corner of PamLut array:")
    print(pam_lut[:5, :5])
    
    print("\nFor reference, first 5 amino acids of sequence:")
    for i in range(min(5, len(sequence))):
        aa = sequence[i]
        aa_idx = ord(aa) % 32
        print(f"  Position {i}: {aa} (index {aa_idx})")


if __name__ == "__main__":
    main()