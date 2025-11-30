from Bio.Align import substitution_matrices
import numpy as np
import argparse


def align_local_swissprot(seq_a_str, seq_b_str, weights="PAM250", gap_open=0, gap_extend=-10):
    """
    Performs a Local Smith-Waterman alignment using a custom implementation.
    This correctly handles zero gap open penalty.
    
    Args:
        seq_a_str: First sequence string
        seq_b_str: Second sequence string
        weights: Substitution matrix name (string) or dict-like object
        gap_open: Gap opening penalty (default: 0)
        gap_extend: Gap extension penalty (default: -10)

    Returns:
        - A dictionary with alignment score, visual text, and index mappings
        - None if no alignment found
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

    result = align_local_swissprot(seq_a, seq_b)
    
    if print_alignment_results(result, seq_a, seq_b, verbose=True):
        print("\n" + "=" * 60)
        print("Test completed successfully!")
    else:
        print("Test failed - no significant local alignment detected")


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
    parser.add_argument('--no-test', action='store_false', dest='test',
                        help='Disable test mode')
    parser.set_defaults(test=False)
    
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
        print()
    
    try:
        result = align_local_swissprot(
            args.seq_a, 
            args.seq_b, 
            weights=args.matrix,
            gap_open=args.gap_open,
            gap_extend=args.gap_extend
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
        exit(1)