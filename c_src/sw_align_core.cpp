#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>

// Define max macro if not available
#ifndef max
#define max(a,b) (((a) > (b)) ? (a) : (b))
#endif

/*
 * Smith-Waterman Local Alignment (C Core)
 *
 * Inputs:
 *   seq_a: First sequence (string)
 *   len_a: Length of first sequence
 *   seq_b: Second sequence (string)
 *   len_b: Length of second sequence
 *   matrix: Flattened 32x32 substitution matrix (1024 floats)
 *           Access via [(char_a & 31) * 32 + (char_b & 31)]
 *   gap_extend: Gap extension penalty (typically negative)
 *
 * Outputs:
 *   out_score: Pointer to store the maximum score
 *   out_len: Pointer to store the length of the alignment path
 *   out_indices_a: Buffer to store indices of sequence A (allocated by caller)
 *   out_indices_b: Buffer to store indices of sequence B (allocated by caller)
 *
 * Note: out_indices_a and out_indices_b are filled in reverse order (traceback).
 *       The caller might need to reverse them, but the Python implementation
 *       seems to construct the list by appending and then reversing.
 *       Here we will store them as we trace back.
 */
extern "C" {

void align_local_core(
    const char* seq_a,
    int len_a,
    const char* seq_b,
    int len_b,
    const float* matrix,
    float gap_extend,
    float* out_score,
    int* out_len,
    int* out_indices_a,
    int* out_indices_b
) {
    int m = len_a;
    int n = len_b;
    
    // Allocate scoring matrix H of size (m+1) x (n+1)
    // Using calloc to initialize to 0
    float* H = (float*)calloc((size_t)(m + 1) * (n + 1), sizeof(float));
    if (!H) {
        *out_score = -1.0f; // Error indicator
        return;
    }

    float max_score_val = 0.0f;
    int max_i = 0;
    int max_j = 0;

    // Fill the matrix
    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            // Calculate indices for sequences (0-based)
            char char_a = seq_a[i - 1];
            char char_b = seq_b[j - 1];
            
            // Look up score in the 32x32 matrix
            int idx_a = char_a & 31;
            int idx_b = char_b & 31;
            float score_match = matrix[idx_a * 32 + idx_b];

            // Calculate potential scores
            // H[i-1][j-1] -> Match/Mismatch
            float match = H[(i - 1) * (n + 1) + (j - 1)] + score_match;
            
            // H[i-1][j] -> Gap in seq_b (delete from seq_a)
            float delete_val = H[(i - 1) * (n + 1) + j] + gap_extend;
            
            // H[i][j-1] -> Gap in seq_a (insert in seq_a)
            float insert_val = H[i * (n + 1) + (j - 1)] + gap_extend;
            
            // Take max(0, match, delete, insert)
            float score = 0.0f;
            if (match > score) score = match;
            if (delete_val > score) score = delete_val;
            if (insert_val > score) score = insert_val;
            
            H[i * (n + 1) + j] = score;

            if (score > max_score_val) {
                max_score_val = score;
                max_i = i;
                max_j = j;
            }
        }
    }

    *out_score = max_score_val;

    // If no alignment found
    if (max_score_val <= 0.0f) {
        *out_len = 0;
        free(H);
        return;
    }

    // Traceback
    int i = max_i;
    int j = max_j;
    int k = 0; // path index

    while (i > 0 && j > 0 && H[i * (n + 1) + j] > 0) {
        float current_score = H[i * (n + 1) + j];
        float diagonal = H[(i - 1) * (n + 1) + (j - 1)];
        float up = H[(i - 1) * (n + 1) + j];
        // float left = H[i * (n + 1) + (j - 1)]; // Unused but implied

        char char_a = seq_a[i - 1];
        char char_b = seq_b[j - 1];
        int idx_a = char_a & 31;
        int idx_b = char_b & 31;
        float score_match = matrix[idx_a * 32 + idx_b];

        // Replicate precedence from Python:
        // 1. Match/Mismatch
        // 2. Up (Gap in seq_b)
        // 3. Left (Gap in seq_a) -- Fallthrough

        // Floating point comparison epsilon could be needed, 
        // but exact match logic is used in Python so we try exact here.
        // Or essentially strict equality as produced by the same operations.
        
        // Note: Python does: if current_score == diagonal + sub_matrix...
        
        if (current_score == diagonal + score_match) {
            // Match/Mismatch
            out_indices_a[k] = i - 1;
            out_indices_b[k] = j - 1;
            i--;
            j--;
        } else if (current_score == up + gap_extend) {
            // Gap in seq_b (delete) -> seq_a consumes a char, seq_b has gap
            // In Python output: aligned_b has '-', aligned_a has char.
            // indices_a records i-1. indices_b records nothing (or -1?).
            // Wait, Python `indices_a` appends `i-1`. `indices_b` appends nothing?
            /*
                Python logic:
                elif current_score == up + gap_extend:
                    # Gap in seq_b
                    aligned_a.append(seq_a[i-1])
                    aligned_b.append('-')
                    indices_a.append(i-1)
                    i -= 1
            */
            // So indices lists are not necessarily same length or synchronized by index?
            // "indices_a" and "indices_b" in the Python result seem to be just lists of indices involved.
            // Let's look at the return value format:
            // "seq_a_indices": indices_a, "seq_b_indices": indices_b
            // These are lists of the indices in the original sequences that are part of the alignment.
            // If there is a gap, that position is skipped in the index list for that sequence.
            
            // To pass this back to Python via simple arrays, we can use -1 to indicate a gap?
            // No, the Python code produces two separate lists which might have different lengths.
            // But here in C I have parallel arrays `out_indices_a` and `out_indices_b`.
            // I should use -1 to indicate a gap in the parallel structure (alignment columns).
            
            out_indices_a[k] = i - 1;
            out_indices_b[k] = -1; // Gap in B
            i--;
        } else {
            // Gap in seq_a
            /*
                Python logic:
                else:
                    # Gap in seq_a
                    aligned_a.append('-')
                    aligned_b.append(seq_b[j-1])
                    indices_b.append(j-1)
                    j -= 1
            */
            out_indices_a[k] = -1; // Gap in A
            out_indices_b[k] = j - 1;
            j--;
        }
        k++;
    }

    *out_len = k;
    free(H);
}

}
