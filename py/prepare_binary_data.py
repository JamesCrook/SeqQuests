#!/usr/bin/env python3
"""
Prepares binary data files for the C version of the SW search.
- <matrix>.bin: A 32x32 int16 matrix (e.g., pam250.bin, blosum62.bin).
- fasta.bin: A sequence of records, each containing the description and sequence.
"""
import numpy as np
import sys
import os
import struct
import argparse
from pathlib import Path
import pam_converter as pam
import sequences


def create_pam_binary(matrix_name="PAM250", output_path=None, data_dir=None):
    """
    Generates substitution matrix binary file.
    
    Args:
        matrix_name: Name of the substitution matrix (e.g., "PAM250", "BLOSUM62")
        output_path: Optional output file path (defaults to <matrix_lower>.bin)
        data_dir: Directory for output files
    """
    if output_path is None:
        output_path = f"{matrix_name.lower()}.bin"
    
    # Convert to Path and make it relative to data_dir if specified
    output_path = Path(output_path)
    if data_dir and not output_path.is_absolute():
        output_path = data_dir / output_path
    
    # Create parent directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"--- Creating {output_path} ---")
    pam_32x32, _ = pam.convert_pam_to_32x32(matrix_name)
    
    # Ensure the data type is int16, as expected by the C code
    pam_array = np.array(pam_32x32, dtype=np.int16)
    
    with open(output_path, "wb") as f:
        f.write(pam_array.tobytes())
    
    print(f"{output_path} created successfully.")
    print(f"Shape: {pam_array.shape}, Dtype: {pam_array.dtype}, Size: {output_path.stat().st_size} bytes")
    
    return output_path


def create_fasta_binary(output_path="fasta.bin", data_dir=None):
    """
    Generates fasta.bin
    Format for each record:
    - Description length (int32)
    - Description (bytes)
    - Sequence length (int32)
    - Sequence (bytes, prefixed with '@')
    
    Args:
        output_path: Output file path for the FASTA binary
        data_dir: Directory for output files
    
    Returns:
        Tuple of (output_path, num_sequences, total_length)
    """
    # Convert to Path and make it relative to data_dir if specified
    output_path = Path(output_path)
    if data_dir and not output_path.is_absolute():
        output_path = data_dir / output_path
    
    # Create parent directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n--- Creating {output_path} ---")
    fasta_iter = sequences.read_fasta_sequences()
    count = 0
    total_length = 0
    
    with open(output_path, "wb") as f:
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
            # -1 to not count the '@' terminator
            total_length += len(sequence) - 1
            
            if count % 10000 == 0:
                print(f"  ... processed {count} sequences")
    
    print(f"{output_path} created successfully with {count} sequences.")
    print(f"Total sequence length: {total_length:,} amino acids")
    print(f"Size: {output_path.stat().st_size:,} bytes")
    
    return output_path, count, total_length


def check_pam_binary(matrix_path):
    """
    Examine a substitution matrix binary file and print information.
    
    Args:
        matrix_path: Path to the matrix binary file
    """
    matrix_path = Path(matrix_path)
    
    if not matrix_path.exists():
        print(f"Error: File '{matrix_path}' not found.")
        return False
    
    print(f"\n--- Checking {matrix_path} ---")
    
    file_size = matrix_path.stat().st_size
    expected_size = 32 * 32 * 2  # 32x32 int16 = 2048 bytes
    
    print(f"File size: {file_size} bytes")
    print(f"Expected size: {expected_size} bytes")
    
    if file_size != expected_size:
        print(f"WARNING: File size mismatch! Expected {expected_size} bytes.")
        return False
    
    # Read the matrix
    with open(matrix_path, "rb") as f:
        data = f.read()
    
    pam_array = np.frombuffer(data, dtype=np.int16).reshape(32, 32)
    
    print(f"Matrix shape: {pam_array.shape}")
    print(f"Matrix dtype: {pam_array.dtype}")
    print(f"Value range: [{pam_array.min()}, {pam_array.max()}]")
    
    print("\nUpper-left 5x5 corner:")
    print(pam_array[:5, :5])
    
    return True


def check_fasta_binary(fasta_path):
    """
    Examine a FASTA binary file and print information.
    
    Args:
        fasta_path: Path to the FASTA binary file
    """
    fasta_path = Path(fasta_path)
    
    if not fasta_path.exists():
        print(f"Error: File '{fasta_path}' not found.")
        return False
    
    print(f"\n--- Checking {fasta_path} ---")
    
    file_size = fasta_path.stat().st_size
    print(f"File size: {file_size:,} bytes")
    
    count = 0
    total_length = 0
    
    with open(fasta_path, "rb") as f:
        while True:
            # Read description length
            desc_len_bytes = f.read(4)
            if not desc_len_bytes:
                break  # End of file
            
            desc_len = struct.unpack('<I', desc_len_bytes)[0]
            description = f.read(desc_len).decode('utf-8')
            
            # Read sequence length
            seq_len = struct.unpack('<I', f.read(4))[0]
            sequence = f.read(seq_len)
            
            count += 1
            # -1 to not count the '@' terminator
            total_length += seq_len - 1
            
            # Show first few sequences
            if count <= 3:
                print(f"\nSequence {count}:")
                print(f"  Description: {description[:80]}{'...' if len(description) > 80 else ''}")
                print(f"  Length: {seq_len - 1} amino acids")
                print(f"  First 50 chars: {sequence[:50]}")
    
    print(f"\nTotal sequences: {count:,}")
    print(f"Total sequence length: {total_length:,} amino acids")
    print(f"Average sequence length: {total_length / count if count > 0 else 0:.1f} amino acids")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Converts substitution matrix and FASTA data to binary format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  %(prog)s --data-dir ../data --matrix BLOSUM62\n"
               "  %(prog)s -d ../data --matrix PAM250 --matrix-output custom_pam.bin\n"
               "  %(prog)s --data-dir ../data --no-matrix --fasta-output sequences.bin\n"
               "  %(prog)s -d ../data --check\n"
    )
    
    # Output directory
    parser.add_argument('--data-dir', '-d', type=Path, default=None,
                        help='Directory for input/output files (default: current directory)')
    
    # Matrix options
    parser.add_argument('--matrix', '-m', type=str, default='PAM250',
                        help='Substitution matrix name (default: PAM250)')
    parser.add_argument('--matrix-output', type=str, default=None,
                        help='Output path for matrix binary file (default: <matrix_lower>.bin)')
    parser.add_argument('--no-matrix', action='store_false', dest='create_matrix',
                        help='Skip matrix binary generation')
    parser.add_argument('--create-matrix', action='store_true', dest='create_matrix',
                        help='Generate matrix binary (default)')
    
    # FASTA options
    parser.add_argument('--fasta-output', type=str, default='fasta.bin',
                        help='Output path for FASTA binary file (default: fasta.bin)')
    parser.add_argument('--no-fasta', action='store_false', dest='create_fasta',
                        help='Skip FASTA binary generation')
    parser.add_argument('--create-fasta', action='store_true', dest='create_fasta',
                        help='Generate FASTA binary (default)')
    
    # Check options
    parser.add_argument('--check', action='store_true',
                        help='Check existing binary files instead of creating them')
    parser.add_argument('--matrix-file', type=str, default=None,
                        help='Matrix file to check (used with --check)')
    parser.add_argument('--fasta-file', type=str, default='fasta.bin',
                        help='FASTA file to check (used with --check, default: fasta.bin)')
    
    parser.set_defaults(create_matrix=True, create_fasta=True)
    
    args = parser.parse_args()
    
    # Convert data_dir to Path if specified
    data_dir = Path(args.data_dir) if args.data_dir else None
    
    # Check mode
    if args.check:
        print("=" * 60)
        print("CHECKING BINARY FILES")
        print("=" * 60)
        
        # Determine matrix file to check
        if args.matrix_file:
            matrix_file = Path(args.matrix_file)
        else:
            matrix_file = Path(f"{args.matrix.lower()}.bin")
        
        if data_dir and not matrix_file.is_absolute():
            matrix_file = data_dir / matrix_file
        
        fasta_file = Path(args.fasta_file)
        if data_dir and not fasta_file.is_absolute():
            fasta_file = data_dir / fasta_file
        
        check_pam_binary(matrix_file)
        check_fasta_binary(fasta_file)
        return
    
    # Creation mode
    print("=" * 60)
    print("CREATING BINARY FILES")
    print("=" * 60)
    
    if data_dir:
        print(f"Output directory: {data_dir.resolve()}")
    
    if args.create_matrix:
        create_pam_binary(args.matrix, args.matrix_output, data_dir)
    else:
        print("Skipping matrix binary generation (--no-matrix)")
    
    if args.create_fasta:
        create_fasta_binary(args.fasta_output, data_dir)
    else:
        print("\nSkipping FASTA binary generation (--no-fasta)")
    
    if not args.create_matrix and not args.create_fasta:
        print("\nNothing to do. Use --create-matrix or --create-fasta, or see --help")


if __name__ == "__main__":
    main()