import torch
import numpy as np
from collections import Counter

import torch
import torch.nn.functional as F
import numpy as np

class FastNWS:
    def __init__(self, device=None, batch_size=100):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        self.batch_size = batch_size
        
        # BLOSUM62 as tensor
        self.blosum62 = self.load_blosum62().to(device)
        self.gap_open = -10
        self.gap_extend = -1
        
    def compute_all_pairs(self, sequences):
        """Compute full NxN score matrix"""
        n = len(sequences)
        
        # Preallocate score matrix
        scores = np.zeros((n, n), dtype=np.float32)
        
        # Convert sequences to tensors
        seq_tensors = [self.sequence_to_tensor(s) for s in sequences]
        
        # Batch computation
        for i in range(0, n, self.batch_size):
            for j in range(i, n, self.batch_size):
                batch_i = seq_tensors[i:i+self.batch_size]
                batch_j = seq_tensors[j:j+self.batch_size]
                
                # Compute batch scores
                batch_scores = self.batch_nws(batch_i, batch_j)
                
                # Fill score matrix (symmetric)
                for bi, ii in enumerate(range(i, min(i+self.batch_size, n))):
                    for bj, jj in enumerate(range(j, min(j+self.batch_size, n))):
                        scores[ii, jj] = batch_scores[bi, bj]
                        scores[jj, ii] = batch_scores[bi, bj]
        
        return scores
    
    def nws_wavefront_batch(seq1_batch, seq2_batch, match=1, mismatch=-1, gap=-1):
        batch_size = seq1_batch.shape[0]
        m, n = seq1_batch.shape[1], seq2_batch.shape[1]
        
        # Initialize DP matrix
        dp = torch.zeros(batch_size, m+1, n+1, device='cuda')
        
        # Initialize boundaries
        dp[:, :, 0] = torch.arange(m+1) * gap
        dp[:, 0, :] = torch.arange(n+1) * gap
        
        # Wavefront computation
        for diag in range(1, m + n + 1):
            # Compute valid range for this diagonal
            i_start = max(1, diag - n + 1)
            i_end = min(m + 1, diag)
            
            # Parallel computation for all valid cells in diagonal
            for i in range(i_start, i_end):
                j = diag - i
                if j > 0 and j <= n:
                    match_score = (seq1_batch[:, i-1] == seq2_batch[:, j-1]) * match + \
                                 (seq1_batch[:, i-1] != seq2_batch[:, j-1]) * mismatch
                    
                    dp[:, i, j] = torch.max(torch.stack([
                        dp[:, i-1, j-1] + match_score,  # match/mismatch
                        dp[:, i-1, j] + gap,            # deletion
                        dp[:, i, j-1] + gap             # insertion
                    ], dim=0), dim=0)[0]
        
        return dp[:, -1, -1]  # Return final scores

    def batch_nws(self, seqs1, seqs2):
        """Wavefront NWS for batches"""
        # Implementation of wavefront algorithm
        # Returns score matrix for all pairs in batch
        pass


class FastNwsDummy:
    def __init__(self, device=None, batch_size=100):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        self.batch_size = batch_size
        
        # Amino acid order
        self.aa_order = 'ACDEFGHIKLMNPQRSTVWY'
        self.aa_to_idx = {aa: i for i, aa in enumerate(self.aa_order)}
        
    def sequence_to_composition(self, seq):
        """Convert sequence to normalized composition vector"""
        counts = Counter(seq)
        total = len(seq)
        comp = np.zeros(20, dtype=np.float32)
        
        for aa, count in counts.items():
            if aa in self.aa_to_idx:
                comp[self.aa_to_idx[aa]] = count / total
        
        return comp
    
    def batch_composition_similarity(self, seqs1, seqs2):
        """
        Compute composition-based similarity as NWS stub.
        Uses Bhattacharyya coefficient scaled to approximate NWS scores.
        """
        n1, n2 = len(seqs1), len(seqs2)
        
        # Convert sequences to composition matrices
        comp1 = np.array([self.sequence_to_composition(s) for s in seqs1])
        comp2 = np.array([self.sequence_to_composition(s) for s in seqs2])
        
        # Convert to torch tensors
        comp1_t = torch.tensor(comp1, device=self.device)
        comp2_t = torch.tensor(comp2, device=self.device)
        
        # Compute all pairs similarity using Bhattacharyya coefficient
        # BC = sum(sqrt(p_i * q_i))
        scores = torch.zeros((n1, n2), device=self.device)
        
        for i in range(n1):
            # Broadcast computation for all j
            sqrt_prod = torch.sqrt(comp1_t[i:i+1] * comp2_t)  # (n2, 20)
            bc_scores = torch.sum(sqrt_prod, dim=1)  # (n2,)
            
            # Scale to approximate NWS range
            # BC is [0,1], NWS is roughly [-len*gap, len*match]
            # Use geometric mean of lengths for scaling
            len1 = len(seqs1[i])
            lens2 = torch.tensor([len(s) for s in seqs2], device=self.device)
            geom_mean = torch.sqrt(len1 * lens2.float())
            
            # Scale: perfect match ≈ len*2, no match ≈ -len*5
            # BC=1 -> len*2, BC=0 -> -len*5
            scores[i] = geom_mean * (7 * bc_scores - 5)
        
        return scores.cpu().numpy()
    
    def batch_nws(self, seqs1, seqs2):
        """Stub using composition similarity"""
        return self.batch_composition_similarity(seqs1, seqs2)