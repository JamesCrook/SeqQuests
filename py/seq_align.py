from Bio.Align import PairwiseAligner
from Bio.Align import substitution_matrices

def align_local_swissprot(seq_a_str, seq_b_str, weights = "PAM250"):
    """
    Performs a Local Smith-Waterman alignment (sensitive).
    Returns:
        - formatted_text: The visual alignment string
        - align_data: A dictionary with indices and raw aligned strings
    """
    
    # 1. Configure the Aligner (Smith-Waterman / Local)
    aligner = PairwiseAligner()
    aligner.mode = 'local'  # 'global' would be Needleman-Wunsch
    
    # 2. Set Sensitivity Parameters (Twilight Zone Settings)
    # BLOSUM62 is standard. For deep twilight, BLOSUM45 or BLOSUM80 might be tuned,
    # but BLOSUM62 is the best generalist.
    aligner.substitution_matrix = substitution_matrices.load(weights)
    
    # Gap Penalties (Open, Extend) - heavily affects 'sensitivity'
    # Standard: Open -10, Extend -0.5
    aligner.open_gap_score = 0
    aligner.extend_gap_score = -10
    
    # 3. Perform Alignment
    alignments = aligner.align(seq_a_str, seq_b_str)
    
    # If no alignment found (score <= 0), return None
    if not alignments:
        return None

    # Get the single best alignment (top scoring)
    top_aln = alignments[0]
    
    # 4. Extract Indices
    # top_aln.aligned is a tuple of two lists: (ranges_in_seq_a, ranges_in_seq_b)
    # ranges are tuples (start, end)
    ranges_a = top_aln.aligned[0]
    ranges_b = top_aln.aligned[1]
    
    # Flatten ranges to get a list of ALL indices involved in the alignment
    # Useful for your 3D viewer mapping
    indices_a = []
    for start, end in ranges_a:
        indices_a.extend(range(start, end))
        
    indices_b = []
    for start, end in ranges_b:
        indices_b.extend(range(start, end))

    # 5. Prepare Output Data
    # Note: top_aln.format() produces the visual "text" alignment
    
    result = {
        "score": top_aln.score,
        "visual_text": str(top_aln),  # Visual representation with | and gaps
        "seq_a_indices": indices_a,   # List of 0-based indices in Seq A that matched
        "seq_b_indices": indices_b,   # List of 0-based indices in Seq B that matched
        "range_summary": {
            # Overall start/end of the alignment block (for the Info Card)
            "seq_a_start": indices_a[0], 
            "seq_a_end": indices_a[-1],
            "seq_b_start": indices_b[0], 
            "seq_b_end": indices_b[-1]
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
              f"aligns with SeqB [{data['range_summary']['seq_b_start']}-{data['range_summary']['seq_b_end']}]")