/**
 * Client-side Smith-Waterman Implementation (JavaScript)
 * Matches the logic in py/sw_align.py
 */

const PAM250_DATA = {
  "alphabet": "ARNDCQEGHILKMFPSTWYVBZX*",
  "values": [
    [2.0, -2.0, 0.0, 0.0, -2.0, 0.0, 0.0, 1.0, -1.0, -1.0, -2.0, -1.0, -1.0,
      -3.0, 1.0, 1.0, 1.0, -6.0, -3.0, 0.0, 0.0, 0.0, 0.0, -8.0
    ],
    [-2.0, 6.0, 0.0, -1.0, -4.0, 1.0, -1.0, -3.0, 2.0, -2.0, -3.0, 3.0, 0.0,
      -4.0, 0.0, 0.0, -1.0, 2.0, -4.0, -2.0, -1.0, 0.0, -1.0, -8.0
    ],
    [0.0, 0.0, 2.0, 2.0, -4.0, 1.0, 1.0, 0.0, 2.0, -2.0, -3.0, 1.0, -2.0, -
      3.0, 0.0, 1.0, 0.0, -4.0, -2.0, -2.0, 2.0, 1.0, 0.0, -8.0
    ],
    [0.0, -1.0, 2.0, 4.0, -5.0, 2.0, 3.0, 1.0, 1.0, -2.0, -4.0, 0.0, -3.0, -
      6.0, -1.0, 0.0, 0.0, -7.0, -4.0, -2.0, 3.0, 3.0, -1.0, -8.0
    ],
    [-2.0, -4.0, -4.0, -5.0, 12.0, -5.0, -5.0, -3.0, -3.0, -2.0, -6.0, -5.0,
      -5.0, -4.0, -3.0, 0.0, -2.0, -8.0, 0.0, -2.0, -4.0, -5.0, -3.0, -8.0
    ],
    [0.0, 1.0, 1.0, 2.0, -5.0, 4.0, 2.0, -1.0, 3.0, -2.0, -2.0, 1.0, -1.0, -
      5.0, 0.0, -1.0, -1.0, -5.0, -4.0, -2.0, 1.0, 3.0, -1.0, -8.0
    ],
    [0.0, -1.0, 1.0, 3.0, -5.0, 2.0, 4.0, 0.0, 1.0, -2.0, -3.0, 0.0, -2.0, -
      5.0, -1.0, 0.0, 0.0, -7.0, -4.0, -2.0, 3.0, 3.0, -1.0, -8.0
    ],
    [1.0, -3.0, 0.0, 1.0, -3.0, -1.0, 0.0, 5.0, -2.0, -3.0, -4.0, -2.0, -
      3.0, -5.0, 0.0, 1.0, 0.0, -7.0, -5.0, -1.0, 0.0, 0.0, -1.0, -8.0
    ],
    [-1.0, 2.0, 2.0, 1.0, -3.0, 3.0, 1.0, -2.0, 6.0, -2.0, -2.0, 0.0, -2.0,
      -2.0, 0.0, -1.0, -1.0, -3.0, 0.0, -2.0, 1.0, 2.0, -1.0, -8.0
    ],
    [-1.0, -2.0, -2.0, -2.0, -2.0, -2.0, -2.0, -3.0, -2.0, 5.0, 2.0, -2.0,
      2.0, 1.0, -2.0, -1.0, 0.0, -5.0, -1.0, 4.0, -2.0, -2.0, -1.0, -8.0
    ],
    [-2.0, -3.0, -3.0, -4.0, -6.0, -2.0, -3.0, -4.0, -2.0, 2.0, 6.0, -3.0,
      4.0, 2.0, -3.0, -3.0, -2.0, -2.0, -1.0, 2.0, -3.0, -3.0, -1.0, -8.0
    ],
    [-1.0, 3.0, 1.0, 0.0, -5.0, 1.0, 0.0, -2.0, 0.0, -2.0, -3.0, 5.0, 0.0, -
      5.0, -1.0, 0.0, 0.0, -3.0, -4.0, -2.0, 1.0, 0.0, -1.0, -8.0
    ],
    [-1.0, 0.0, -2.0, -3.0, -5.0, -1.0, -2.0, -3.0, -2.0, 2.0, 4.0, 0.0,
      6.0, 0.0, -2.0, -2.0, -1.0, -4.0, -2.0, 2.0, -2.0, -2.0, -1.0, -8.0
    ],
    [-3.0, -4.0, -3.0, -6.0, -4.0, -5.0, -5.0, -5.0, -2.0, 1.0, 2.0, -5.0,
      0.0, 9.0, -5.0, -3.0, -3.0, 0.0, 7.0, -1.0, -4.0, -5.0, -2.0, -8.0
    ],
    [1.0, 0.0, 0.0, -1.0, -3.0, 0.0, -1.0, 0.0, 0.0, -2.0, -3.0, -1.0, -2.0,
      -5.0, 6.0, 1.0, 0.0, -6.0, -5.0, -1.0, -1.0, 0.0, -1.0, -8.0
    ],
    [1.0, 0.0, 1.0, 0.0, 0.0, -1.0, 0.0, 1.0, -1.0, -1.0, -3.0, 0.0, -2.0, -
      3.0, 1.0, 2.0, 1.0, -2.0, -3.0, -1.0, 0.0, 0.0, 0.0, -8.0
    ],
    [1.0, -1.0, 0.0, 0.0, -2.0, -1.0, 0.0, 0.0, -1.0, 0.0, -2.0, 0.0, -1.0,
      -3.0, 0.0, 1.0, 3.0, -5.0, -3.0, 0.0, 0.0, -1.0, 0.0, -8.0
    ],
    [-6.0, 2.0, -4.0, -7.0, -8.0, -5.0, -7.0, -7.0, -3.0, -5.0, -2.0, -3.0,
      -4.0, 0.0, -6.0, -2.0, -5.0, 17.0, 0.0, -6.0, -5.0, -6.0, -4.0, -8.0
    ],
    [-3.0, -4.0, -2.0, -4.0, 0.0, -4.0, -4.0, -5.0, 0.0, -1.0, -1.0, -4.0, -
      2.0, 7.0, -5.0, -3.0, -3.0, 0.0, 10.0, -2.0, -3.0, -4.0, -2.0, -8.0
    ],
    [0.0, -2.0, -2.0, -2.0, -2.0, -2.0, -2.0, -1.0, -2.0, 4.0, 2.0, -2.0,
      2.0, -1.0, -1.0, -1.0, 0.0, -6.0, -2.0, 4.0, -2.0, -2.0, -1.0, -8.0
    ],
    [0.0, -1.0, 2.0, 3.0, -4.0, 1.0, 3.0, 0.0, 1.0, -2.0, -3.0, 1.0, -2.0, -
      4.0, -1.0, 0.0, 0.0, -5.0, -3.0, -2.0, 3.0, 2.0, -1.0, -8.0
    ],
    [0.0, 0.0, 1.0, 3.0, -5.0, 3.0, 3.0, 0.0, 2.0, -2.0, -3.0, 0.0, -2.0, -
      5.0, 0.0, 0.0, -1.0, -6.0, -4.0, -2.0, 2.0, 3.0, -1.0, -8.0
    ],
    [0.0, -1.0, 0.0, -1.0, -3.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -
      1.0, -2.0, -1.0, 0.0, 0.0, -4.0, -2.0, -1.0, -1.0, -1.0, -1.0, -8.0
    ],
    [-8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0,
      -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, -8.0, 1.0
    ]
  ]
};

// Map char to index in alphabet
const ALPHABET_MAP = {};
for(let i = 0; i < PAM250_DATA.alphabet.length; i++) {
  ALPHABET_MAP[PAM250_DATA.alphabet[i]] = i;
}

function getScore(a, b) {
  const idxA = ALPHABET_MAP[a] !== undefined ? ALPHABET_MAP[a] : ALPHABET_MAP[
    'X'];
  const idxB = ALPHABET_MAP[b] !== undefined ? ALPHABET_MAP[b] : ALPHABET_MAP[
    'X'];
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
  for(let i = 1; i <= m; i++) {
    for(let j = 1; j <= n; j++) {
      const charA = seqA[i - 1];
      const charB = seqB[j - 1];

      // Match/Mismatch
      const match = H[(i - 1) * cols + (j - 1)] + getScore(charA, charB);

      // Gap in seq_b (delete from seq_a)
      const del = H[(i - 1) * cols + j] + gapExtend;

      // Gap in seq_a (insert in seq_a)
      const ins = H[i * cols + (j - 1)] + gapExtend;

      // Max(0, match, delete, insert)
      let score = match;
      if(del > score) score = del;
      if(ins > score) score = ins;
      if(score < 0) score = 0;

      H[i * cols + j] = score;

      if(score > maxScore) {
        maxScore = score;
        maxPos = [i, j];
      }
    }
  }

  if(maxScore <= 0) {
    return null;
  }

  // Traceback
  let i = maxPos[0];
  let j = maxPos[1];

  let alignedA = [];
  let alignedB = [];
  let indicesA = [];
  let indicesB = [];

  while(i > 0 && j > 0 && H[i * cols + j] > 0) {
    const currentScore = H[i * cols + j];
    const diagonal = H[(i - 1) * cols + (j - 1)];
    const up = H[(i - 1) * cols + j];

    // Check which direction
    // Float comparison: matching Python equality logic
    const matchScore = getScore(seqA[i - 1], seqB[j - 1]);

    // Epsilon for float comparison?
    // JS floats are 64-bit, but we used Float32Array for H.
    // Let's use a small epsilon or just check strictness if the values are integers/simple floats.
    // The Python code uses simple equality.

    if(Math.abs(currentScore - (diagonal + matchScore)) < 1e-6) {
      // Match/Mismatch
      alignedA.push(seqA[i - 1]);
      alignedB.push(seqB[j - 1]);
      indicesA.push(i - 1);
      indicesB.push(j - 1);
      i--;
      j--;
    } else if(Math.abs(currentScore - (up + gapExtend)) < 1e-6) {
      // Gap in seq_b
      alignedA.push(seqA[i - 1]);
      alignedB.push('-');
      indicesA.push(i - 1);
      i--;
    } else {
      // Gap in seq_a
      alignedA.push('-');
      alignedB.push(seqB[j - 1]);
      indicesB.push(j - 1);
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
  for(let k = 0; k < strAlignedA.length; k++) {
    const a = strAlignedA[k];
    const b = strAlignedB[k];
    if(a === b) {
      matches += '|';
    } else if(a === '-' || b === '-') {
      matches += ' ';
    } else {
      matches += '.';
    }
  }

  return {
    score: maxScore,
    align1: strAlignedA,
    align2: strAlignedB,
    matches: matches,
    seq1_start: indicesA.length > 0 ? indicesA[0] : 0,
    seq2_start: indicesB.length > 0 ? indicesB[0] : 0
  };
}

function formatAlignment(alignment) {
  // Build alignment view
  const lineLen = 70;
  const lines = [];

  // Get starting positions from server data (convert from 0-indexed to 1-indexed)
  let pos1 = alignment.seq1_start + 1;
  let pos2 = alignment.seq2_start + 1;

  for(let i = 0; i < alignment.align1.length; i += lineLen) {
    const chunk1 = alignment.align1.substr(i, lineLen);
    const chunkMatch = alignment.matches.substr(i, lineLen);
    const chunk2 = alignment.align2.substr(i, lineLen);

    // Format current positions
    const pos1Str = String(pos1).padStart(6, ' ');
    const pos2Str = String(pos2).padStart(6, ' ');

    lines.push(`${pos1Str}  ${chunk1}`);
    lines.push(`        ${chunkMatch}`);
    lines.push(`${pos2Str}  ${chunk2}\n`);

    for(let c of chunk1)
      if(c !== '-') pos1++;
    for(let c of chunk2)
      if(c !== '-') pos2++;
  }
  return lines;
}

// WASM Module Loader
let wasmModule = null;
let wasmMemory = null;
let wasmExports = null;

// Load the Emscripten-generated module
async function initWasm() {
  try {

    // Dynamically load the WASM module script
    await new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'sw_align_module.js';
      script.onload = resolve;
      script.onerror = () => reject(new Error('WASM module not found'));
      document.head.appendChild(script);
    });

    wasmModule = await createWasmModule();
    //console.log("WASM Module keys:", Object.keys(wasmModule)); // Debug

    wasmExports = wasmModule;
    console.log("WASM Initialized successfully");
    return true;
  } catch (e) {
    console.warn("WASM Init failed:", e);
    return false;
  }
}

function runWasmAlign(seqA, seqB) {
  const encoder = new TextEncoder();
  const bytesA = encoder.encode(seqA);
  const bytesB = encoder.encode(seqB);

  // Use Emscripten's _malloc
  const ptrA = wasmModule._malloc(bytesA.length + 1);
  const ptrB = wasmModule._malloc(bytesB.length + 1);

  // Use Emscripten's HEAPU8 view directly
  wasmModule.HEAPU8.set(bytesA, ptrA);
  wasmModule.HEAPU8[ptrA + bytesA.length] = 0;
  wasmModule.HEAPU8.set(bytesB, ptrB);
  wasmModule.HEAPU8[ptrB + bytesB.length] = 0;

  // Matrix
  const matrixPtr = wasmModule._malloc(1024 * 4);
  const flatMatrix = new Float32Array(1024);

  for(let i = 0; i < PAM250_DATA.alphabet.length; i++) {
    const charA = PAM250_DATA.alphabet[i];
    const idxA = charA.charCodeAt(0) & 31;

    for(let j = 0; j < PAM250_DATA.alphabet.length; j++) {
      const charB = PAM250_DATA.alphabet[j];
      const idxB = charB.charCodeAt(0) & 31;
      const score = PAM250_DATA.values[i][j];
      flatMatrix[idxA * 32 + idxB] = score;
    }
  }

  // Copy matrix to WASM memory
  wasmModule.HEAPF32.set(flatMatrix, matrixPtr / 4);

  // Output pointers
  const scorePtr = wasmModule._malloc(4);
  const lenPtr = wasmModule._malloc(4);

  const maxLen = bytesA.length + bytesB.length;
  const indicesAPtr = wasmModule._malloc(maxLen * 4);
  const indicesBPtr = wasmModule._malloc(maxLen * 4);

  // Call function
  wasmModule._align_local_core(
    ptrA, bytesA.length,
    ptrB, bytesB.length,
    matrixPtr, -10.0,
    scorePtr, lenPtr,
    indicesAPtr, indicesBPtr
  );

  // Read results using Emscripten's HEAP views
  const score = wasmModule.HEAPF32[scorePtr / 4];
  const len = wasmModule.HEAP32[lenPtr / 4];

  // Copy indices out before freeing
  const indicesA = new Int32Array(len);
  const indicesB = new Int32Array(len);
  for(let k = 0; k < len; k++) {
    indicesA[k] = wasmModule.HEAP32[indicesAPtr / 4 + k];
    indicesB[k] = wasmModule.HEAP32[indicesBPtr / 4 + k];
  }

  // Free memory
  wasmModule._free(ptrA);
  wasmModule._free(ptrB);
  wasmModule._free(matrixPtr);
  wasmModule._free(scorePtr);
  wasmModule._free(lenPtr);
  wasmModule._free(indicesAPtr);
  wasmModule._free(indicesBPtr);

  // Build alignment strings (reverse order from traceback)
  let alignedA = "";
  let alignedB = "";
  const realIndicesA = [];
  const realIndicesB = [];

  for(let k = len - 1; k >= 0; k--) {
    const ia = indicesA[k];
    const ib = indicesB[k];

    if(ia !== -1) {
      alignedA += seqA[ia];
      realIndicesA.push(ia);
    } else {
      alignedA += "-";
    }

    if(ib !== -1) {
      alignedB += seqB[ib];
      realIndicesB.push(ib);
    } else {
      alignedB += "-";
    }
  }

  // Generate match string
  let matches = '';
  for(let k = 0; k < alignedA.length; k++) {
    const a = alignedA[k];
    const b = alignedB[k];
    if(a === b) matches += '|';
    else if(a === '-' || b === '-') matches += ' ';
    else matches += '.';
  }

  return {
    score: score,
    align1: alignedA,
    align2: alignedB,
    matches: matches,
    seq1_start: realIndicesA.length > 0 ? realIndicesA[0] : 0,
    seq2_start: realIndicesB.length > 0 ? realIndicesB[0] : 0
  };
}

function calculateIdentity(data) {
  let matches = 0;
  let len = 0;
  for(let i = 0; i < data.align1.length; i++) {
    if(data.align1[i] !== '-' && data.align2[i] !== '-') {
      len++;
      if(data.align1[i] === data.align2[i]) matches++;
    }
  }
  return len > 0 ? ((matches / len) * 100).toFixed(1) : "0.0";
}
