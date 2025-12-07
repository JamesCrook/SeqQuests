from Bio.Align import substitution_matrices
import numpy as np
import argparse
import ctypes
import os
import sys
from pathlib import Path

# Load shared library
def load_sw_lib():
    """Load the shared library for Smith-Waterman alignment."""
    # Determine extension based on platform
    if sys.platform == 'darwin':
        lib_name = 'libsw_align.dylib'
    else:
        lib_name = 'libsw_align.so'
    
    # Look for bin directory relative to this file
    # py/sw_align.py -> py/ -> root/ -> bin/
    current_dir = Path(__file__).parent.resolve()
    project_root = current_dir.parent
    lib_path = project_root / 'bin' / lib_name
    
    try:
        lib = ctypes.CDLL(str(lib_path))
        
        # Define argtypes
        # void align_local_core(const char* seq_a, int len_a, const char* seq_b, int len_b, 
        #                       const float* matrix, float gap_extend, 
        #                       float* out_score, int* out_len, 
        #                       int* out_indices_a, int* out_indices_b)
        lib.align_local_core.argtypes = [
            ctypes.c_char_p, ctypes.c_int,
            ctypes.c_char_p, ctypes.c_int,
            ctypes.POINTER(ctypes.c_float), ctypes.c_float,
            ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
        ]
        return lib
    except OSError as e:
        print(f"Warning: Could not load C library at {lib_path}: {e}")
        return None

_SW_LIB = load_sw_lib()

def get_matrix_32(weights="PAM250"):
    """
    Convert a Biopython substitution matrix (or name) to a flattened 32x32 float array.
    Uses index = char & 31.
    """
    # Load substitution matrix if string
    if isinstance(weights, str):
        sub_matrix = substitution_matrices.load(weights)
    else:
        sub_matrix = weights
        
    # Create 32x32 array (1024 floats)
    matrix_32 = np.zeros(1024, dtype=np.float32)
    
    # The alphabet usually contains standard amino acids + 'Z', 'B', '*', 'X'
    # We iterate over the alphabet provided by Biopython and map to the 32x32 grid
    alphabet = sub_matrix.alphabet
    
    # We need to fill the whole 32x32 matrix?
    # Or just the relevant entries?
    # The C code accesses `matrix[idx_a * 32 + idx_b]`.
    # Unmapped characters will remain 0.
    
    # To be safe, maybe fill with a default low score (mismatch) if not 0? 
    # But 0 is often a neutral or bad score in unnormalized matrices. 
    # BLOSUM/PAM have positive and negative values.
    # Let's trust the alphabet coverage.
    
    for i, char_a in enumerate(alphabet):
        idx_a = ord(char_a) & 31
        for j, char_b in enumerate(alphabet):
            idx_b = ord(char_b) & 31
            score = sub_matrix[i][j]
            # Handle collisions? (e.g. 'A' vs 'a')
            # Assuming standard uppercase alphabet.
            matrix_32[idx_a * 32 + idx_b] = score
            
    return matrix_32

def align_local_swissprot_c(seq_a_str, seq_b_str, weights="PAM250", gap_extend=-10):
    """
    Wrapper for C implementation of Local Smith-Waterman.
    """
    if _SW_LIB is None:
        raise RuntimeError("C library not available")

    # Prepare inputs
    seq_a_bytes = seq_a_str.encode('ascii')
    seq_b_bytes = seq_b_str.encode('ascii')
    len_a = len(seq_a_str)
    len_b = len(seq_b_str)
    
    # Prepare matrix
    # Note: Optimization - we could cache this if weights is a string
    matrix_32 = get_matrix_32(weights)
    matrix_ptr = matrix_32.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    
    # Prepare outputs
    out_score = ctypes.c_float()
    out_len = ctypes.c_int()
    
    # Allocate buffers for indices (max possible length is len_a + len_b)
    max_path_len = len_a + len_b
    out_indices_a = (ctypes.c_int * max_path_len)()
    out_indices_b = (ctypes.c_int * max_path_len)()
    
    # Call C function
    _SW_LIB.align_local_core(
        seq_a_bytes, len_a,
        seq_b_bytes, len_b,
        matrix_ptr, float(gap_extend),
        ctypes.byref(out_score), ctypes.byref(out_len),
        out_indices_a, out_indices_b
    )
    
    if out_score.value <= 0:
        return None
        
    path_len = out_len.value
    
    # Retrieve indices
    # C code returns them in traceback order (reversed relative to sequence)
    # We convert them to lists. 
    # Note: C returns -1 for gaps.
    raw_indices_a = out_indices_a[:path_len]
    raw_indices_b = out_indices_b[:path_len]
    
    # Construct aligned strings and index lists for result dict
    aligned_a = []
    aligned_b = []
    indices_a = []
    indices_b = []
    
    # We iterate backwards through the C output to build the strings forward?
    # No, traceback gives the alignment from end to start.
    # So raw_indices[0] is the end of the alignment.
    # raw_indices[path_len-1] is the start.
    
    # We want final output to be forward.
    # So we reverse the raw lists first.
    raw_indices_a.reverse()
    raw_indices_b.reverse()
    
    for idx_a, idx_b in zip(raw_indices_a, raw_indices_b):
        if idx_a != -1:
            aligned_a.append(seq_a_str[idx_a])
            indices_a.append(idx_a)
        else:
            aligned_a.append('-')
            
        if idx_b != -1:
            aligned_b.append(seq_b_str[idx_b])
            indices_b.append(idx_b)
        else:
            aligned_b.append('-')
            
    aligned_a_str = "".join(aligned_a)
    aligned_b_str = "".join(aligned_b)
    
    # Visual text
    match_line = ''
    for a, b in zip(aligned_a_str, aligned_b_str):
        if a == b:
            match_line += '|'
        elif a == '-' or b == '-':
            match_line += ' '
        else:
            match_line += '.'
    
    visual_text = f"{aligned_a_str}\n{match_line}\n{aligned_b_str}"
    
    return {
        "score": out_score.value,
        "visual_text": visual_text,
        "seq_a_indices": indices_a,
        "seq_b_indices": indices_b,
        "aligned_a": aligned_a_str,
        "aligned_b": aligned_b_str,
        "range_summary": {
            "seq_a_start": indices_a[0] if indices_a else 0,
            "seq_a_end": indices_a[-1] if indices_a else 0,
            "seq_b_start": indices_b[0] if indices_b else 0,
            "seq_b_end": indices_b[-1] if indices_b else 0
        }
    }


def align_local_swissprot(seq_a_str, seq_b_str, weights="PAM250", gap_open=0, gap_extend=-10, use_c=True):
    """
    Performs a Local Smith-Waterman alignment.
    Default: uses C implementation (ignoring gap_open).
    Set use_c=False to use pure Python implementation.
    """
    if use_c and _SW_LIB:
        return align_local_swissprot_c(seq_a_str, seq_b_str, weights, gap_extend)
    else:
        return align_local_swissprot_python(seq_a_str, seq_b_str, weights, gap_open, gap_extend)


def align_local_swissprot_python(seq_a_str, seq_b_str, weights="PAM250", gap_open=0, gap_extend=-10):
    """
    Performs a Local Smith-Waterman alignment using a custom implementation.
    This correctly handles zero gap open penalty.
    """
    
    # Load substitution matrix
    if isinstance(weights, str):
        sub_matrix = substitution_matrices.load(weights)
    else:
        sub_matrix = weights
    
    # Initialize sequences
    seq_a = seq_a_str
    seq_b = seq_b_str
    m, n = len(seq_a), len(seq_b)
    
    # Initialize scoring matrix (m+1 x n+1)
    H = np.zeros((m + 1, n + 1), dtype=float)
    
    # Track maximum score and its position
    max_score = 0
    max_pos = (0, 0)
    
    # Fill the scoring matrix
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            # Match/mismatch score
            match = H[i-1, j-1] + sub_matrix[seq_a[i-1]][seq_b[j-1]]
            
            # Gap in seq_b (delete from seq_a)
            delete = H[i-1, j] + gap_extend
            
            # Gap in seq_a (insert in seq_a)
            insert = H[i, j-1] + gap_extend
            
            # Smith-Waterman: take max of all options, or 0
            H[i, j] = max(0, match, delete, insert)
            
            # Track maximum score
            if H[i, j] > max_score:
                max_score = H[i, j]
                max_pos = (i, j)
    
    # If no alignment found
    if max_score <= 0:
        return None
    
    # Traceback from max_pos until we hit 0
    i, j = max_pos
    aligned_a = []
    aligned_b = []
    indices_a = []
    indices_b = []
    
    while i > 0 and j > 0 and H[i, j] > 0:
        current_score = H[i, j]
        diagonal = H[i-1, j-1]
        up = H[i-1, j]
        left = H[i, j-1]
        
        # Determine which direction we came from
        if current_score == diagonal + sub_matrix[seq_a[i-1]][seq_b[j-1]]:
            # Match/mismatch
            aligned_a.append(seq_a[i-1])
            aligned_b.append(seq_b[j-1])
            indices_a.append(i-1)
            indices_b.append(j-1)
            i -= 1
            j -= 1
        elif current_score == up + gap_extend:
            # Gap in seq_b
            aligned_a.append(seq_a[i-1])
            aligned_b.append('-')
            indices_a.append(i-1)
            i -= 1
        else:
            # Gap in seq_a
            aligned_a.append('-')
            aligned_b.append(seq_b[j-1])
            indices_b.append(j-1)
            j -= 1
    
    # Reverse alignments (we traced backwards)
    aligned_a = ''.join(reversed(aligned_a))
    aligned_b = ''.join(reversed(aligned_b))
    indices_a = list(reversed(indices_a))
    indices_b = list(reversed(indices_b))
    
    # Create visual alignment
    match_line = ''
    for a, b in zip(aligned_a, aligned_b):
        if a == b:
            match_line += '|'
        elif a == '-' or b == '-':
            match_line += ' '
        else:
            match_line += '.'
    
    visual_text = f"{aligned_a}\n{match_line}\n{aligned_b}"
    
    # Prepare result
    result = {
        "score": max_score,
        "visual_text": visual_text,
        "seq_a_indices": indices_a,
        "seq_b_indices": indices_b,
        "aligned_a": aligned_a,
        "aligned_b": aligned_b,
        "range_summary": {
            "seq_a_start": indices_a[0] if indices_a else 0,
            "seq_a_end": indices_a[-1] if indices_a else 0,
            "seq_b_start": indices_b[0] if indices_b else 0,
            "seq_b_end": indices_b[-1] if indices_b else 0
        }
    }
    
    return result


def print_alignment_results(result, seq_a=None, seq_b=None, verbose=False):
    """Print alignment results in a formatted way."""
    if not result:
        print("No significant local alignment found")
        return False
    
    print(f"Alignment Score: {result['score']:.1f}")
    print("\nVisual Alignment:")
    print(result['visual_text'])
    print()
    
    if verbose:
        print("-" * 60)
        if seq_a and seq_b:
            print(f"Sequence A: {seq_a}")
            print(f"  Length: {len(seq_a)} amino acids")
            print(f"Sequence B: {seq_b}")
            print(f"  Length: {len(seq_b)} amino acids")
            print()
        
        print(f"Seq A Indices (0-based): {result['seq_a_indices']}")
        print(f"Seq B Indices (0-based): {result['seq_b_indices']}")
        print(f"\nAlignment Summary:")
        print(f"  Seq A: residues {result['range_summary']['seq_a_start']}-{result['range_summary']['seq_a_end']}")
        print(f"  Seq B: residues {result['range_summary']['seq_b_start']}-{result['range_summary']['seq_b_end']}")
        print(f"  Aligned region length: {len(result['seq_a_indices'])} positions")
        
        # Calculate identity
        matches = sum(1 for a, b in zip(result['aligned_a'], result['aligned_b']) 
                    if a == b and a != '-')
        total = len(result['aligned_a'])
        identity = (matches / total * 100) if total > 0 else 0
        print(f"  Sequence identity: {identity:.1f}% ({matches}/{total})")
    
    return True


def test():
    """Smoke test - will the alignment work?"""
    print("Running in test mode...")
    print("=" * 60)
    print("Smith-Waterman Local Alignment Test")
    print("=" * 60)
    
    # Sequence A: 104 kDa microneme/rhoptry antigen (Theileria) - Fragment
    # Sequence B: SH3 domain-binding protein 1 (Human) - Fragment
    seq_a = "MKLLVILLFSALALAAQKPGGAPTTSLIGNESRSDQPSTVAAA"
    seq_b = "MVTAQKPGGAPTTQLLGNESRSDQPSTVGGG"

    print(f"\nSequence A (Theileria fragment): {seq_a}")
    print(f"Sequence B (Human fragment): {seq_b}")
    print()

    print("--- Testing Python Implementation ---")
    result_py = align_local_swissprot_python(seq_a, seq_b)
    print_alignment_results(result_py, seq_a, seq_b)

    if _SW_LIB:
        print("\n--- Testing C Implementation ---")
        result_c = align_local_swissprot_c(seq_a, seq_b)
        print_alignment_results(result_c, seq_a, seq_b)
        
        if result_py and result_c:
            score_diff = abs(result_py['score'] - result_c['score'])
            if score_diff < 0.001:
                print("\nSUCCESS: Scores match!")
            else:
                print(f"\nFAILURE: Scores differ! Py: {result_py['score']}, C: {result_c['score']}")
        else:
            print("\nCannot compare scores (one result is None)")
    else:
        print("\nSkipping C test (library not loaded)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Smith-Waterman local sequence alignment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  %(prog)s --test\n"
               "  %(prog)s --seq-a MKLLVILL --seq-b MVTAQKPG\n"
               "  %(prog)s --seq-a MKLLVILL --seq-b MVTAQKPG --matrix BLOSUM62 -v\n"
    )
    
    # Test mode
    parser.add_argument('--test', action='store_true',
                        help='Run test mode with example sequences')
    
    # Sequence arguments
    parser.add_argument('--seq-a', type=str, default=None,
                        help='First sequence to align')
    parser.add_argument('--seq-b', type=str, default=None,
                        help='Second sequence to align')
    
    # Alignment parameters
    parser.add_argument('--matrix', '-m', type=str, default='PAM250',
                        help='Substitution matrix name (default: PAM250)')
    parser.add_argument('--gap-open', type=float, default=0,
                        help='Gap opening penalty (default: 0)')
    parser.add_argument('--gap-extend', type=float, default=-10,
                        help='Gap extension penalty (default: -10)')
    
    # Output options
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output with additional statistics')
    parser.add_argument('--indices-only', action='store_true',
                        help='Output only the aligned indices')
    parser.add_argument('--python-only', action='store_true',
                        help='Force use of Python implementation')
    
    args = parser.parse_args()

    # Test mode
    if args.test:
        test()
        exit(0)
    
    # Require sequences if not in test mode
    if args.seq_a is None or args.seq_b is None:
        parser.print_help()
        print("\nError: Both --seq-a and --seq-b are required when not in test mode")
        exit(1)
    
    # Perform alignment
    print("=" * 60)
    print("Smith-Waterman Local Alignment")
    print("=" * 60)
    
    if args.verbose:
        print(f"\nParameters:")
        print(f"  Substitution matrix: {args.matrix}")
        print(f"  Gap open penalty: {args.gap_open}")
        print(f"  Gap extend penalty: {args.gap_extend}")
        print(f"  Implementation: {'Python' if args.python_only else 'C (default)'}")
        print()
    
    try:
        use_c = not args.python_only
        
        result = align_local_swissprot(
            args.seq_a, 
            args.seq_b, 
            weights=args.matrix,
            gap_open=args.gap_open,
            gap_extend=args.gap_extend,
            use_c=use_c
        )
        
        if args.indices_only:
            if result:
                print(f"{result['seq_a_indices']}")
                print(f"{result['seq_b_indices']}")
            else:
                exit(1)
        else:
            if not print_alignment_results(result, args.seq_a, args.seq_b, args.verbose):
                exit(1)
            
    except Exception as e:
        print(f"Error during alignment: {e}")
        # import traceback
        # traceback.print_exc()
        exit(1)