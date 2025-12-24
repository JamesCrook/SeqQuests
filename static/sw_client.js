
/**
 * Client-side Smith-Waterman Implementation (JavaScript)
 * Matches the logic in py/sw_align.py
 */

const PAM250_DATA = {
    "alphabet": "ARNDCQEGHILKMFPSTWYVBZX*",
    "values": [
        [2.0, -2.0, 0.0, 0.0, -2.0, 0.0, 0.0, 1.0, -1.0, -1.0, -2.0, -1.0, -1.0, -3.0, 1.0, 1.0, 1.0, -6.0, -3.0, 0.0, 0.0, 0.0, 0.0, -8.0],
        [-2.0, 6.0, 0.0, -1.0, -4.0, 1.0, -1.0, -3.0, 2.0, -2.0, -3.0, 3.0, 0.0, -4.0, 0.0, 0.0, -1.0, 2.0, -4.0, -2.0, -1.0, 0.0, -1.0, -8.0],
        [0.0, 0.0, 2.0, 2.0, -4.0, 1.0, 1.0, 0.0, 2.0, -2.0, -3.0, 1.0, -2.0, -3.0, 0.0, 1.0, 0.0, -4.0, -2.0, -2.0, 2.0, 1.0, 0.0, -8.0],
        [0.0, -1.0, 2.0, 4.0, -5.0, 2.0, 3.0, 1.0, 1.0, -2.0, -4.0, 0.0, -3.0, -6.0, -1.0, 0.0, 0.0, -7.0, -4.0, -2.0, 3.0, 3.0, -1.0, -8.0],
        [-2.0, -4.0, -4.0, -5.0, 12.0, -5.0, -5.0, -3.0, -3.0, -2.0, -6.0, -5.0, -5.0, -4.0, -3.0, 0.0, -2.0, -8.0, 0.0, -2.0, -4.0, -5.0, -3.0, -8.0],
        [0.0, 1.0, 1.0, 2.0, -5.0, 4.0, 2.0, -1.0, 3.0, -2.0, -2.0, 1.0, -1.0, -5.0, 0.0, -1.0, -1.0, -5.0, -4.0, -2.0, 1.0, 3.0, -1.0, -8.0],
        [0.0, -1.0, 1.0, 3.0, -5.0, 2.0, 4.0, 0.0, 1.0, -2.0, -3.0, 0.0, -2.0, -5.0, -1.0, 0.0, 0.0, -7.0, -4.0, -2.0, 3.0, 3.0, -1.0, -8.0],
        [1.0, -3.0, 0.0, 1.0, -3.0, -1.0, 0.0, 5.0, -2.0, -3.0, -4.0, -2.0, -3.0, -5.0, 0.0, 1.0, 0.0, -7.0, -5.0, -1.0, 0.0, 0.0, -1.0, -8.0],
        [-1.0, 2.0, 2.0, 1.0, -3.0, 3.0, 1.0, -2.0, 6.0, -2.0, -2.0, 0.0, -2.0, -2.0, 0.0, -1.0, -1.0, -3.0, 0.0, -2.0, 1.0, 2.0, -1.0, -8.0],
        [-1.0, -2.0, -2.0, -2.0, -2.0, -2.0, -2.0, -3.0, -2.0, 5.0, 2.0, -2.0, 2.0, 1.0, -2.0, -1.0, 0.0, -5.0, -1.0, 4.0, -2.0, -2.0, -1.0, -8.0],
        [-2.0, -3.0, -3.0, -4.0, -6.0, -2.0, -3.0, -4.0, -2.0, 2.0, 6.0, -3.0, 4.0, 2.0, -3.0, -3.0, -2.0, -2.0, -1.0, 2.0, -3.0, -3.0, -1.0, -8.0],
        [-1.0, 3.0, 1.0, 0.0, -5.0, 1.0, 0.0, -2.0, 0.0, -2.0, -3.0, 5.0, 0.0, -5.0, -1.0, 0.0, 0.0, -3.0, -4.0, -2.0, 1.0, 0.0, -1.0, -8.0],
        [-1.0, 0.0, -2.0, -3.0, -5.0, -1.0, -2.0, -3.0, -2.0, 2.0, 4.0, 0.0, 6.0, 0.0, -2.0, -2.0, -1.0, -4.0, -2.0, 2.0, -2.0, -2.0, -1.0, -8.0],
        [-3.0, -4.0, -3.0, -6.0, -4.0, -5.0, -5.0, -5.0, -2.0, 1.0, 2.0, -5.0, 0.0, 9.0, -5.0, -3.0, -3.0, 0.0, 7.0, -1.0, -4.0, -5.0, -2.0, -8.0],
        [1.0, 0.0, 0.0, -1.0, -3.0, 0.0, -1.0, 0.0, 0.0, -2.0, -3.0, -1.0, -2.0, -5.0, 6.0, 1.0, 0.0, -6.0, -5.0, -1.0, -1.0, 0.0, -1.0, -8.0],
        [1.0, 0.0, 1.0, 0.0, 0.0, -1.0, 0.0, 1.0, -1.0, -1.0, -3.0, 0.0, -2.0, -3.0, 1.0, 2.0, 1.0, -2.0, -3.0, -1.0, 0.0, 0.0, 0.0, -8.0],
        [1.0, -1.0, 0.0, 0.0, -2.0, -1.0, 0.0, 0.0, -1.0, 0.0, -2.0, 0.0, -1.0, -3.0, 0.0, 1.0, 3.0, -5.0, -3.0, 0.0, 0.0, -1.0, 0.0, -8.0],
        [-6.0, 2.0, -4.0, -7.0, -8.0, -5.0, -7.0, -7.0, -3.0, -5.0, -2.0, -3.0, -4.0, 0.0, -6.0, -2.0, -5.0, 17.0, 0.0, -6.0, -5.0, -6.0, -4.0, -8.0],
        [-3.0, -4.0, -2.0, -4.0, 0.0, -4.0, -4.0, -5.0, 0.0, -1.0, -1.0, -4.0, -2.0, 7.0, -5.0, -3.0, -3.0, 0.0, 10.0, -2.0, -3.0, -4.0, -2.0, -8.0],
        [0.0, -2.0, -2.0, -2.0, -2.0, -2.0, -2.0, -1.0, -2.0, 4.0, 2.0, -2.0, 2.0, -1.0, -1.0, -1.0, 0.0, -6.0, -2.0, 4.0, -2.0, -2.0, -1.0, -8.0],
        [0.0, -1.0, 2.0, 3.0, -4.0, 1.0, 3.0, 0.0, 1.0, -2.0, -3.0, 1.0, -2.0, -4.0, -1.0, 0.0, 0.0, -5.0, -3.0, -2.0, 3.0, 2.0, -1.0, -8.0],
        [0.0, 0.0, 1.0, 3.0, -5.0, 3.0, 3.0, 0.0, 2.0, -2.0, -3.0, 0.0, -2.0, -5.0, 0.0, 0.0, -1.0, -6.0, -4.0, -2.0, 2.0, 3.0, -1.0, -8.0],
        [0.0, -1.0, 0.0, -1.0, -3.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -2.0, -1.0, 0.0, 0.0, -4.0, -2.0, -1.0, -1.0, -1.0, -1.0, -8.0],
        [-8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, 1.0]
    ]
};

// Map char to index in alphabet
const ALPHABET_MAP = {};
for (let i = 0; i < PAM250_DATA.alphabet.length; i++) {
    ALPHABET_MAP[PAM250_DATA.alphabet[i]] = i;
}

function getScore(a, b) {
    const idxA = ALPHABET_MAP[a] !== undefined ? ALPHABET_MAP[a] : ALPHABET_MAP['X'];
    const idxB = ALPHABET_MAP[b] !== undefined ? ALPHABET_MAP[b] : ALPHABET_MAP['X'];
    return PAM250_DATA.values[idxA][idxB];
}

function alignLocalJS(seqA, seqB, gapExtend = -10) {
    const m = seqA.length;
    const n = seqB.length;

    // Initialize scoring matrix H (m+1 x n+1)
    // Using 1D array for performance: H[i][j] -> H[i * (n+1) + j]
    const cols = n + 1;
    const H = new Float32Array((m + 1) * cols);

    let maxScore = 0;
    let maxPos = [0, 0];

    // Fill matrix
    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            const charA = seqA[i-1];
            const charB = seqB[j-1];

            // Match/Mismatch
            const match = H[(i-1) * cols + (j-1)] + getScore(charA, charB);

            // Gap in seq_b (delete from seq_a)
            const del = H[(i-1) * cols + j] + gapExtend;

            // Gap in seq_a (insert in seq_a)
            const ins = H[i * cols + (j-1)] + gapExtend;

            // Max(0, match, delete, insert)
            let score = match;
            if (del > score) score = del;
            if (ins > score) score = ins;
            if (score < 0) score = 0;

            H[i * cols + j] = score;

            if (score > maxScore) {
                maxScore = score;
                maxPos = [i, j];
            }
        }
    }

    if (maxScore <= 0) {
        return null;
    }

    // Traceback
    let i = maxPos[0];
    let j = maxPos[1];

    let alignedA = [];
    let alignedB = [];
    let indicesA = [];
    let indicesB = [];

    while (i > 0 && j > 0 && H[i * cols + j] > 0) {
        const currentScore = H[i * cols + j];
        const diagonal = H[(i-1) * cols + (j-1)];
        const up = H[(i-1) * cols + j];

        // Check which direction
        // Float comparison: matching Python equality logic
        const matchScore = getScore(seqA[i-1], seqB[j-1]);

        // Epsilon for float comparison?
        // JS floats are 64-bit, but we used Float32Array for H.
        // Let's use a small epsilon or just check strictness if the values are integers/simple floats.
        // The Python code uses simple equality.

        if (Math.abs(currentScore - (diagonal + matchScore)) < 1e-6) {
             // Match/Mismatch
             alignedA.push(seqA[i-1]);
             alignedB.push(seqB[j-1]);
             indicesA.push(i-1);
             indicesB.push(j-1);
             i--;
             j--;
        } else if (Math.abs(currentScore - (up + gapExtend)) < 1e-6) {
             // Gap in seq_b
             alignedA.push(seqA[i-1]);
             alignedB.push('-');
             indicesA.push(i-1);
             i--;
        } else {
             // Gap in seq_a
             alignedA.push('-');
             alignedB.push(seqB[j-1]);
             indicesB.push(j-1);
             j--;
        }
    }

    // Reverse
    alignedA.reverse();
    alignedB.reverse();
    indicesA.reverse();
    indicesB.reverse();

    const strAlignedA = alignedA.join('');
    const strAlignedB = alignedB.join('');

    // Format visual text
    let matches = '';
    for (let k = 0; k < strAlignedA.length; k++) {
        const a = strAlignedA[k];
        const b = strAlignedB[k];
        if (a === b) {
            matches += '|';
        } else if (a === '-' || b === '-') {
            matches += ' ';
        } else {
            matches += '.';
        }
    }

    return {
        score: maxScore,
        alignment1: strAlignedA,
        alignment2: strAlignedB,
        matches: matches,
        seq1_start: indicesA.length > 0 ? indicesA[0] : 0,
        seq2_start: indicesB.length > 0 ? indicesB[0] : 0
    };
}
