import sys
import os
import time
import itertools
import argparse

from pathlib import Path

script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))


import sequences

"""
The 'integrity' we are checking here is that the reduced FastA formatted version of the 
protein database matches the SwissProt data base on accession numbers and sequences.
"""

def test_data_integrity():
    print("Starting Data Integrity Test (Streaming Mode)...")

    # 1. Get Iterators
    print("Initializing FASTA iterator...")
    # This might still load the file into memory depending on PickledSequenceCache impl,
    # but we avoid creating a second list of it.
    fasta_iter = sequences.read_fasta_sequences()

    print("Initializing Swiss-Prot iterator (Index)...")
    swiss_iter = sequences.read_swissprot_sequences(file_format='swiss_index')

    mismatches = 0
    index = 0

    # Use zip_longest to detect length differences
    # fillvalue=None is default, we can check for it
    for f_rec, s_rec in itertools.zip_longest(fasta_iter, swiss_iter):

        # Check for length mismatch
        if f_rec is None:
            print(f"Mismatch at index {index}: FASTA ended, but Swiss-Prot has more records.")
            print(f"  Swiss-Prot ID: {s_rec.accessions[0]}")
            mismatches += 1
            break
        if s_rec is None:
            print(f"Mismatch at index {index}: Swiss-Prot ended, but FASTA has more records.")
            print(f"  FASTA ID: {f_rec.id}")
            mismatches += 1
            break

        # Parse FASTA ID
        f_id_parts = f_rec.id.split('|')
        if len(f_id_parts) >= 2:
            f_accession = f_id_parts[1]
        else:
            f_accession = f_rec.id

        # SwissProt Record
        s_accession = s_rec.accessions[0]

        # Progress update
        if index % 1000 == 0:
            print(f"Processing index {index}: {s_accession}")

        # Compare Accessions
        if f_accession != s_accession:
            print(f"Mismatch at index {index}:")
            print(f"  FASTA ID: {f_rec.id} (Accession extracted: {f_accession})")
            print(f"  Swiss ID: {s_accession}")
            mismatches += 1

        # Compare Sequences
        f_seq = str(f_rec.seq).strip()
        s_seq = s_rec.sequence.strip()

        if f_seq != s_seq:
            print(f"Sequence mismatch at index {index} (Accession: {f_accession}):")
            print(f"  FASTA len: {len(f_seq)}")
            print(f"  Swiss len: {len(s_seq)}")
            mismatches += 1

        if index == 10:
             print(f"Check index 10: FASTA ID={f_rec.id}, Swiss Accession={s_accession}. Match={f_accession==s_accession and f_seq==s_seq}")

        if mismatches >= 10:
            print("Too many mismatches, stopping comparison.")
            break

        index += 1

    if mismatches == 0:
        print(f"SUCCESS: All {index} compared records match in ID and Sequence.")
    else:
        print(f"FAILURE: Found {mismatches} mismatches.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check FASTA data integrity")
    parser.add_argument("--test", action="store_true", help="Run self-test (checks data integrity)")
    args = parser.parse_args()

    if args.test:
        test_data_integrity()
    else:
        # Default behavior is to run the check
        test_data_integrity()
