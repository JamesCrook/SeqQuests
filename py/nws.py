import torch
import numpy as np
from collections import Counter

class FastNWS:
    def __init__(self, device='cuda', batch_size=100):
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