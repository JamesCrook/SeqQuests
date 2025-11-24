from Bio.Align import substitution_matrices
import numpy as np


def align_local_swissprot(seq_a_str, seq_b_str, weights="PAM250"):
    """
    Performs a Local Smith-Waterman alignment using a custom implementation.
    This correctly handles zero gap open penalty.
    
    weights can be a string (loaded from Biopython) or a dict-like object (custom matrix).

    Returns:
        - A dictionary with alignment score, visual text, and index mappings
    """
    
    # Load substitution matrix
    if isinstance(weights, str):
        sub_matrix = substitution_matrices.load(weights)
    else:
        sub_matrix = weights
    
    # Gap penalties
    gap_open = 0
    gap_extend = -10
    
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
        "range_summary": {
            "seq_a_start": indices_a[0] if indices_a else 0,
            "seq_a_end": indices_a[-1] if indices_a else 0,
            "seq_b_start": indices_b[0] if indices_b else 0,
            "seq_b_end": indices_b[-1] if indices_b else 0
        }
    }
    
    return result

# --- Usage Example ---
if __name__ == "__main__":
    # Sequence A: 104 kDa microneme/rhoptry antigen (Theileria) - Fragment
    # Sequence B: SH3 domain-binding protein 1 (Human) - Fragment
    # (Using dummy data similar to your twilight zone hit)
    seq_theileria = "MKLLVILLFSALALAAQKPGGAPTTSLIGNESRSDQPSTVAAA"
    seq_human     = "MVTAQKPGGAPTTQLLGNESRSDQPSTVGGG"

    data = align_local_swissprot(seq_theileria, seq_human)

    if data:
        print(f"Alignment Score: {data['score']}")
        print("\nVisual Alignment:")
        print(data['visual_text'])
        
        print("-" * 40)
        print(f"Seq A Indices (0-based): {data['seq_a_indices']}")
        print(f"Seq B Indices (0-based): {data['seq_b_indices']}")
        print(f"Summary: SeqA [{data['range_summary']['seq_a_start']}-{data['range_summary']['seq_a_end']}] "
              f"aligns with SeqB [{data['range_summary']['seq_b_start']}-{data['range_summary']['seq_b_end']}] "
              f"aligns with SeqB [{data['range_summary']['seq_b_start']}-{data['range_summary']['seq_b_end']}]")
