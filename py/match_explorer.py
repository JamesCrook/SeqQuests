"""
FastAPI server for Protein Sequence Match Explorer
Serves findings file and generates sequence alignments dynamically using BioPython
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from pathlib import Path
from typing import Dict, Optional
import re

# BioPython imports
from Bio import SeqIO, Align
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

app = FastAPI(title="Protein Sequence Match Explorer API")

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
FINDINGS_FILE = Path("../nws_results/finds.txt")  # Path to your main results file
SEQUENCE_DB = Path("sequences")  # Directory containing sequence files (e.g., sequences/249655.fasta)

# Cache for loaded sequences
sequence_cache: Dict[str, SeqRecord] = {}


def load_sequence(seq_id: str) -> Optional[SeqRecord]:
    """Load a sequence from file, with caching"""
    return None
    
    if seq_id in sequence_cache:
        return sequence_cache[seq_id]
    
    # Try common file extensions
    for ext in ['.fasta', '.fa', '.faa', '.txt']:
        seq_file = SEQUENCE_DB / f"{seq_id}{ext}"
        if seq_file.exists():
            try:
                record = SeqIO.read(seq_file, "fasta")
                sequence_cache[seq_id] = record
                return record
            except Exception as e:
                print(f"Error loading {seq_file}: {e}")
                continue
    
    return None


def generate_alignment(seq1: SeqRecord, seq2: SeqRecord) -> Dict[str, str]:
    """Generate pairwise alignment using BioPython"""
    # Create aligner with default settings
    aligner = Align.PairwiseAligner()
    aligner.mode = 'global'
    aligner.match_score = 2
    aligner.mismatch_score = -1
    aligner.open_gap_score = -2
    aligner.extend_gap_score = -0.5
    
    # Perform alignment
    alignments = aligner.align(seq1.seq, seq2.seq)
    
    # Get best alignment
    best_alignment = alignments[0]
    
    # Convert alignment to strings
    align_str = str(best_alignment).split('\n')
    
    # Extract aligned sequences
    if len(align_str) >= 3:
        align1 = align_str[0]
        align2 = align_str[2]
    else:
        # Fallback if alignment format is unexpected
        align1 = str(seq1.seq)
        align2 = str(seq2.seq)
    
    # Generate match string
    matches = []
    for a, b in zip(align1, align2):
        if a == b and a != '-':
            matches.append('|')
        elif a == '-' or b == '-':
            matches.append(' ')
        else:
            matches.append(':')
    
    return {
        "sequence1": str(seq1.seq),
        "sequence2": str(seq2.seq),
        "alignment1": align1,
        "alignment2": align2,
        "matches": ''.join(matches)
    }


class SequenceResponse(BaseModel):
    sequence1: str
    sequence2: str
    alignment1: str
    alignment2: str
    matches: str


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Protein Sequence Match Explorer API",
        "endpoints": {
            "findings": "/api/findings",
            "sequences": "/api/sequences/{id1}/{id2}"
        }
    }


@app.get("/api/findings", response_class=PlainTextResponse)
async def get_findings():
    """Return the findings file content"""
    if not FINDINGS_FILE.exists():
        raise HTTPException(status_code=404, detail="Findings file not found")
    
    try:
        return FINDINGS_FILE.read_text()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading findings: {str(e)}")


@app.get("/api/sequences/{id1}/{id2}", response_model=SequenceResponse)
async def get_sequence_alignment(id1: str, id2: str):
    """
    Generate alignment between two sequences
    
    Args:
        id1: First sequence ID
        id2: Second sequence ID
    
    Returns:
        JSON with sequence data and alignment
    """
    # Load sequences
    seq1 = load_sequence(id1)
    if not seq1:
        raise HTTPException(status_code=404, detail=f"Sequence {id1} not found")
    
    seq2 = load_sequence(id2)
    if not seq2:
        raise HTTPException(status_code=404, detail=f"Sequence {id2} not found")
    
    # Generate alignment
    try:
        alignment_data = generate_alignment(seq1, seq2)
        return SequenceResponse(**alignment_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating alignment: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("Protein Sequence Match Explorer API")
    print("=" * 60)
    print(f"Findings file: {FINDINGS_FILE.absolute()}")
    print(f"Sequence directory: {SEQUENCE_DB.absolute()}")
    print("-" * 60)
    print("Starting server on http://localhost:8086")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8086)