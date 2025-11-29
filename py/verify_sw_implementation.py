
import sys
import os
import numpy as np

# Add py and metal directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'py'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'metal'))

from sw_align import align_local_swissprot
import pam_converter
from sw_search_metal import sw_step


"""
Smith-Waterman Implementation Validator - Cross-validates multiple SW implementations.

This tool runs the same protein alignment using four different implementations
to verify numerical correctness, particularly around the PAM250 matrix conversion
to 32×32 integer format used by the Metal kernel.

Implementations compared:
1. Pure Python with Biopython's standard PAM250 matrix
2. Pure Python with BLOSUM62 (demonstrates flexibility)
3. Pure Python with custom rounded PAM250 (matches Metal kernel format)
4. Metal proxy (Python code that mimics Metal kernel logic)

Usage:
    python validation/verify_sw_implementations.py

When to run:
- After modifying PAM matrix conversion logic (pam_converter.py)
- After changing Metal kernel alignment code (sw.metal)
- When investigating score discrepancies
- Before committing changes to core alignment algorithms

Scientific ground truth:
Uses real protein sequences with known alignment scores. Score discrepancies
are preserved as comments for investigation (e.g., "only scores 41, not 118").

This is numerical verification across implementations, not pass/fail testing.
Discrepancies indicate bugs in conversion logic or algorithm implementation.

Key validation: Ensures the integer rounding and 32×32 matrix transformation
doesn't introduce significant scoring errors compared to standard implementations.
"""


comment = '42840-32796 s(299) Q9JLV1-P37278 Length: 577/926 [...skipped 1 uncharacterized and 4 similar names] 42840: BAG family molecular chaperone regulator 3; Mus musculus (Mouse). 32796: Calcium-transporting ATPase; Synechococcus elongatus (strain ATCC 33912 / PCC 7942 / FACHB-805) (Anacystis nidulans R2).'

seq1 = 'MSAATQSPMMQMASGNGASDRDPLPPGWEIKIDPQTGWPFFVDHNSRTTTWNDPRVPPEGPKDTASSANGPSRDGSRLLPIREGHPIYPQLRPGYIPIPVLHEGSENRQPHLFHAYSQPGVQRFRTEAAAATPQRSQSPLRGGMTEAAQTDKQCGQMPATATTAAAQPPTAHGPERSQSPAASDCSSSSSSASLPSSGRSSLGSHQLPRGYIPIPVIHEQNITRPAAQPSFHQAQKTHYPAQQGEYQPQQPVYHKIQGDDWEPRPLRAASPFRSPVRGASSREGSPARSGTPVHCPSPIRVHTVVDRPQPMTHREPPPVTQPENKPESKPGPAGPDLPPGHIPIQVIRREADSKPVSQKSPPPAEKVEVKVSSAPIPCPSPSPAPSAVPSPPKNVAAEQKAAPSPAPAEPAAPKSGEAETPPKHPGVLKVEAILEKVQGLEQAVDSFEGKKTDKKYLMIEEYLTKELLALDSVDPEGRADVRQARRDGVRKVQTILEKLEQKAIDVPGQVQVYELQPSNLEAEQPLQEIMGAVVADKDKKGPENKDPQTESQQLEAKAATPPNPSNPADSAGNLVAP'

seq2 = 'MKGAIVSASLTDVRQPIAHWHSLTVEECHQQLDAHRNGLTAEVAADRLALYGPNELVEQAGRSPLQILWDQFANIMLLMLLAVAVVSGALDLRDGQFPKDAIAILVIVVLNAVLGYLQESRAEKALAALKGMAAPLVRVRRDNRDQEIPVAGLVPGDLILLEAGDQVPADARLVESANLQVKESALTGEAEAVQKLADQQLPTDVVIGDRTNCLFQGTEVLQGRGQALVYATGMNTELGRIATLLQSVESEKTPLQQRLDKLGNVLVSGALILVAIVVGLGVLNGQSWEDLLSVGLSMAVAIVPEGLPAVITVALAIGTQRMVQRESLIRRLPAVETLGSVTTICSDKTGTLTQNKMVVQQIHTLDHDFTVTGEGYVPAGHFLIGGEIIVPNDYRDLMLLLAAGAVCNDAALVASGEHWSIVGDPTEGSLLTVAAKAGIDPEGLQRVLPRQDEIPFTSERKRMSVVVADLGETTLTIREGQPYVLFVKGSAELILERCQHCFGNAQLESLTAATRQQILAAGEAMASAGMRVLGFAYRPSAIADVDEDAETDLTWLGLMGQIDAPRPEVREAVQRCRQAGIRTLMITGDHPLTAQAIARDLGITEVGHPVLTGQQLSAMNGAELDAAVRSVEVYARVAPEHKLRIVESLQRQGEFVAMTGDGVNDAPALKQANIGVAMGITGTDVSKEASDMVLLDDNFATIVAAVEEGRIVYGNIRKFIKYILGSNIGELLTIASAPLLGLGAVPLTPLQILWMNLVTDGIPALALAVEPGDPTIMQRRPHNPQESIFARGLGTYMLRVGVVFSAFTIVLMVIAYQYTQVPLPGLDPKRWQTMVFTTLCLAQMGHAIAVRSDLLTIQTPMRTNPWLWLSVIVTALLQLALVYVSPLQKFFGTHSLSQLDLAICLGFSLLLFVYLEAEKWVRQRRY'

# only scores 41, not 118
# Yet billed as 969,602,118,252,70 in the database.
comment2 = '969-602 s(118) P0DX24-P13750 Length: 366/359 [...skipped 4 uncharacterized] 969: 3-beta-hydroxysteroid dehydrogenase {ECO:0000303|PubMed:35108497}; Mycolicibacterium neoaurum (Mycobacterium neoaurum). 602: Patr class I histocompatibility antigen, B-1 alpha chain; Pan troglodytes (Chimpanzee).'


def run_sw_align_test():
    print("--- Running sw_align.py test (Standard Biopython PAM250) ---")
    data = align_local_swissprot(seq1, seq2)
    if data:
        print(f"Alignment Score: {data['score']}")
    else:
        print("No alignment found")

def run_sw_align_test_blosum62():
    print("--- Running sw_align.py test (Biopython BLOSUM62) ---")
    try:
        data = align_local_swissprot(seq1, seq2, weights="BLOSUM62")
        if data:
            print(f"Alignment Score: {data['score']}")
        else:
            print("No alignment found")
    except Exception as e:
        print(f"Failed to run BLOSUM62: {e}")

def run_sw_align_test_custom_rounded():
    print("--- Running sw_align.py test (Custom Rounded PAM250) ---")
    pam_32x32, aa_letters = pam_converter.convert_pam_to_32x32()

    # Adapt 32x32 array to dictionary expected by sw_align
    # The matrix should be indexable by [char_a][char_b]

    class CustomMatrix:
        def __init__(self, matrix, alphabet):
            self.matrix = matrix
            self.alphabet = alphabet

        def __getitem__(self, char_a):
            if char_a not in self.alphabet:
                return CustomRow(None, self.alphabet) # Handle missing char
            idx_a = ord(char_a) % 32
            return CustomRow(self.matrix[idx_a], self.alphabet)

    class CustomRow:
        def __init__(self, row_data, alphabet):
            self.row_data = row_data
            self.alphabet = alphabet

        def __getitem__(self, char_b):
            if self.row_data is None or char_b not in self.alphabet:
                return -4 # Default mismatch? Or 0?
            idx_b = ord(char_b) % 32
            return self.row_data[idx_b]

    # Need to construct alphabet list for validity check
    alphabet = set(aa_letters)
    # Add sequences chars to alphabet just in case
    for c in seq1 + seq2:
        alphabet.add(c)

    custom_matrix = CustomMatrix(pam_32x32, alphabet)

    data = align_local_swissprot(seq1, seq2, weights=custom_matrix)
    if data:
        print(f"Alignment Score: {data['score']}")

def make_fasta_lut_from_string(sequence, pam_32x32):
    """
    Adapted from pam_converter.make_fasta_lut but takes a string directly.
    """
    seq_length = len(sequence)

    # Create array with each entry as amino acid mod 32
    seq_mod32 = np.array([ord(aa) % 32 for aa in sequence], dtype=int)

    # Create PamLut array 32 x seq_length)
    pam_lut = np.zeros((32, seq_length), dtype=int)

    # Fill PamLut
    for col in range(32):
        for i, aa_idx in enumerate(seq_mod32):
            pam_lut[col, i] = pam_32x32[col, aa_idx]

    return pam_lut

def run_metal_proxy_test():
    print("\n--- Running Metal Proxy (sw_step) test ---")

    # 1. Prepare PAM Matrix (Rounded)
    pam_32x32, _ = pam_converter.convert_pam_to_32x32()

    # 2. Prepare Query LUT (seq1)
    pam_lut = make_fasta_lut_from_string(seq1, pam_32x32)
    pam_flat = np.array(pam_lut, dtype=np.int16).flatten()

    # 3. Initialize Buffers
    num_threads = 1
    num_rows = len(seq1)

    input_arr = np.zeros((num_threads, num_rows), dtype=np.int16)
    output_arr = np.zeros((num_threads, num_rows), dtype=np.int16)
    final_max = np.zeros(num_threads * 2, dtype=np.int16)
    aa_data = np.zeros(num_threads, dtype=np.int16)

    # 4. Run Search (Iterate over seq2)
    # Note: Metal code adds '@' at start of sequences
    seq2_processed = '@' + seq2

    for i, char in enumerate(seq2_processed):
        # Set current amino acid for the thread
        aa_data[0] = ord(char) % 32

        # Determine input/output buffer for this step
        if i % 2 == 0:
            curr_in = input_arr
            curr_out = output_arr
        else:
            curr_in = output_arr
            curr_out = input_arr

        # Run step
        sw_step(curr_in, curr_out, pam_flat, aa_data, final_max, num_threads, num_rows)

    print(f"Metal Proxy Score: {final_max[1]}") # final_max[thread*2+1] is the max score

if __name__ == "__main__":
    run_sw_align_test()
    run_sw_align_test_blosum62()
    run_sw_align_test_custom_rounded()
    run_metal_proxy_test()
