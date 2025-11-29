#!/usr/bin/env python3
"""
Prepares binary data files for the C version of the SW search.
- pam250.bin: A 32x32 int16 matrix.
- fasta.bin: A sequence of records, each containing the description and sequence.
"""

import numpy as np
import sys
import os
import struct

import pam_converter as pam
import sequences

def create_pam_binary():
    """Generates pam250.bin"""
    print("--- Creating pam250.bin ---")
    pam_32x32, _ = pam.convert_pam_to_32x32()

    # Ensure the data type is int16, as expected by the C code
    pam_array = np.array(pam_32x32, dtype=np.int16)

    with open("pam250.bin", "wb") as f:
        f.write(pam_array.tobytes())

    print("pam250.bin created successfully.")
    print(f"Shape: {pam_array.shape}, Dtype: {pam_array.dtype}, Size: {os.path.getsize('pam250.bin')} bytes")

def create_fasta_binary():
    """
    Generates fasta.bin
    Format for each record:
    - Description length (int32)
    - Description (bytes)
    - Sequence length (int32)
    - Sequence (bytes, prefixed with '@')
    """
    print("\n--- Creating fasta.bin ---")
    fasta_iter = sequences.read_fasta_sequences()

    count = 0
    with open("fasta.bin", "wb") as f:
        for record in fasta_iter:
            description = record.description.encode('utf-8')

            # Postfix sequence with '@' - end of sequence.
            if isinstance(record.seq, bytes):
                sequence = record.seq + b'@'
            else:
                # biopython Seq objects are not strings, convert to str first
                sequence = (str(record.seq) + '@').encode('latin-1')

            # Write description length and data
            f.write(struct.pack('<I', len(description)))
            f.write(description)

            # Write sequence length and data
            f.write(struct.pack('<I', len(sequence)))
            f.write(sequence)

            count += 1
            if count % 10000 == 0:
                print(f"  ... processed {count} sequences")

    print(f"fasta.bin created successfully with {count} sequences.")
    print(f"Size: {os.path.getsize('fasta.bin')} bytes")

def main():

    create_pam_binary()
    create_fasta_binary()

if __name__ == "__main__":
    main()
