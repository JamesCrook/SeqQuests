#!/usr/bin/env python3
"""
Script to process Dayhoff 250 PAM table and create a PAM lookup table for a sequence.
"""

import numpy as np
from Bio import SeqIO
from Bio.Align import substitution_matrices
import sequences

def convert_pam_to_32x32():
    """
    Read Dayhoff 250 PAM table and convert to 32x32 array.
    Values are scaled to max_value and rounded to integers.
    Indexes are amino acid letters mod 32.
    """
    # Load the Dayhoff 250 PAM matrix
    pam250 = substitution_matrices.load("PAM250")
    
    # Initialize 32x32 array with zeros
    pam_32x32 = np.zeros((32, 32), dtype=int)
    
    # Get the amino acid alphabet from the matrix
    aa_letters = list(pam250.alphabet)
    
    # Find min and max values in the original matrix for scaling
    values = []
    for aa1 in aa_letters:
        for aa2 in aa_letters:
            values.append(pam250[aa1, aa2])
    
    min_val = min(values)
    max_val = max(values)
    
    print(f"Original PAM250 range: [{min_val}, {max_val}]")
    print(f"Amino acids in matrix: {aa_letters}\n")
    
    # Fill the 32x32 array
    for aa1 in aa_letters:
        for aa2 in aa_letters:
            # Get indices mod 32 using ASCII values
            idx1 = ord(aa1) % 32
            idx2 = ord(aa2) % 32
            
            # Scale and round the PAM value
            original_val = pam250[aa1, aa2]
            rounded_val = int(round(original_val))
            
            pam_32x32[idx1, idx2] = rounded_val

    # For stop char @, huge penalty.
    for i in range(32):
        pam_32x32[0, i] = -30000
        pam_32x32[i, 0] = -30000
    
    return pam_32x32, aa_letters


def make_fasta_lut(fasta_rec, pam_32x32):
    """
    Read first sequence from FASTA file and create PamLut array.
    """
    
    sequence = "MMMMM"+str(fasta_rec.seq)
    seq_length = len(sequence)
    
    print(f"\nSequence ID: {fasta_rec.id}")
    print(f"Sequence length: {seq_length}")
    print(f"First 50 characters: {sequence[:50]}...\n")
    
    # Create array with each entry as amino acid mod 32
    seq_mod32 = np.array([ord(aa) % 32 for aa in sequence], dtype=int)
    
    # Create PamLut array 32 x seq_length)
    pam_lut = np.zeros((32, seq_length), dtype=int)
    
    # Fill PamLut by looking up each sequence position against all 32 possible AA values
    for col in range(32):
        for i, aa_idx in enumerate(seq_mod32):
            pam_lut[col, i] = pam_32x32[col, aa_idx]
    
    return pam_lut, sequence


def main():
    # Convert PAM table to 32x32
    print("=" * 60)
    print("Converting Dayhoff 250 PAM table to 32x32 array")
    print("=" * 60)
    
    pam_32x32, aa_letters = convert_pam_to_32x32()
    
    print("Converted 32x32 PAM array (diagnostic):")
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
    first_record = next( iter )
    
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