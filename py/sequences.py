import os
from Bio import SwissProt, SeqIO

import pickle
from pathlib import Path
import time
from collections import OrderedDict
from types import SimpleNamespace

"""
Utilities for efficient access to sequence data.
It's main role is for fasta data, where it can make and use a pickle cache (much faster than 
normal access via SeqIO).
It provides iterators for fasta and full swissprot data
"""

# sequences.py should insulate other modules from knowing what file the sequences come from and their underlying format. When initialised, it should check availability of the data files at its configured path and if not fall back to using the data in /data

# it should read from /data/swissprot.dat.txt, if needing full annotated data.
# it should read from /data/swissprot.fasta.txt, if needing just sequence and identification



class FastaCache:
    def __init__(self):
        self.sequences = OrderedDict()  # Maps seq_id -> (sequence, description)
        self.seq_list = []  # For fast index-based access: [(seq_id, sequence, description), ...]
        self.load_time = 0
    
    def load_fasta(self, fasta_file):
        """Load entire FASTA file into memory"""
        start = time.time()
        self.sequences = OrderedDict()
        self.seq_list = []
        
        for record in SeqIO.parse(fasta_file, "fasta"):
            seq_id = record.id
            seq_bytes = bytes(record.seq)
            description = record.description
            
            self.sequences[seq_id] = (seq_bytes, description)
            self.seq_list.append((seq_id, seq_bytes, description))
        
        self.load_time = time.time() - start
        print(f"Loaded {len(self.sequences)} sequences in {self.load_time:.2f}s")
        return self
    
    def get_sequence(self, seq_id):
        """Get sequence by ID (returns just the sequence string)"""
        data = self.sequences.get(seq_id)
        return data[0] if data else None
    
    def get_description(self, seq_id):
        """Get description by ID"""
        data = self.sequences.get(seq_id)
        return data[1] if data else None
    
    def get_record(self, seq_id):
        """Get record object by ID"""
        data = self.sequences.get(seq_id)
        if data:
            return SimpleNamespace(id=seq_id, seq=data[0], description=data[1])
        return None
    
    def get_sequence_by_index(self, index):
        """Get sequence by index (0-based)"""
        if 0 <= index < len(self.seq_list):
            return self.seq_list[index][1]
        return None
    
    def get_id_by_index(self, index):
        """Get sequence ID by index"""
        if 0 <= index < len(self.seq_list):
            return self.seq_list[index][0]
        return None
    
    def get_record_by_index(self, index):
        """Get record object by index"""
        if 0 <= index < len(self.seq_list):
            seq_id, seq_str, description = self.seq_list[index]
            return SimpleNamespace(id=seq_id, seq=seq_str, description=description)
        return None
    
    def get_subsequence(self, seq_id, start, end):
        """Get slice of sequence by ID"""
        data = self.sequences.get(seq_id)
        return data[0][start:end] if data else None
    
    def get_subsequence_by_index(self, index, start, end):
        """Get slice of sequence by index"""
        seq = self.get_sequence_by_index(index)
        return seq[start:end] if seq else None
    
    def __len__(self):
        """Return number of sequences"""
        return len(self.seq_list)
    
    def __getitem__(self, key):
        """Support both cache[index] and cache[seq_id]"""
        if isinstance(key, int):
            return self.get_record_by_index(key)
        else:
            return self.get_record(key)
    
    def get_all_ids(self):
        """Return list of all sequence IDs in order"""
        return [seq_id for seq_id, _, _ in self.seq_list]
    
    def iter_sequences(self):
        """Iterate over (seq_id, sequence) tuples - DEPRECATED, use iter_records()"""
        for seq_id, sequence, _ in self.seq_list:
            yield (seq_id, sequence)
    
    def iter_records(self):
        """Iterate over record objects with .id, .seq, and .description attributes"""
        for seq_id, seq_str, description in self.seq_list:
            yield SimpleNamespace(id=seq_id, seq=seq_str, description=description)
    
    def __iter__(self):
        """Make the cache itself iterable, yielding records"""
        return self.iter_records()


class PickledFastaCache(FastaCache):
    def __init__(self, fasta_file, cache_dir=".cache"):
        super().__init__()  # Call parent __init__
        self.fasta_file = Path(fasta_file)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / f"{self.fasta_file.stem}.pkl"
    
    def load_with_cache(self):
        """Load from pickle if available, otherwise parse FASTA"""
        # Check if cache exists and is newer than FASTA
        if (self.cache_file.exists() and 
            self.cache_file.stat().st_mtime > self.fasta_file.stat().st_mtime):
            start = time.time()
            with open(self.cache_file, 'rb') as f:
                data = pickle.load(f)
                self.sequences = data['sequences']
                self.seq_list = data['seq_list']
            self.load_time = time.time() - start
            print(f"Loaded {len(self.sequences)} sequences from cache in {self.load_time:.2f}s")
        else:
            self.load_fasta(self.fasta_file)
            # Save cache
            with open(self.cache_file, 'wb') as f:
                pickle.dump({
                    'sequences': self.sequences,
                    'seq_list': self.seq_list
                }, f, protocol=pickle.HIGHEST_PROTOCOL)
            print(f"Cache saved to {self.cache_file}")
        return self


def get_data_path(original_filename):
    """
    Checks for data files in a user-specified path first, falling back
    to the default './data' directory if not found.
    """
    user_path = '/Users/jamescrook/BigData/bio_sequence_data'
    filename_map = {
        'swissprot.fasta.txt': 'uniprot_sprot.fasta',
        'swissprot.dat.txt': 'uniprot_sprot.dat',
    }

    user_filename = filename_map.get(original_filename)

    if user_filename:
        user_filepath = os.path.join(user_path, user_filename)
        if os.path.exists(user_filepath):
            return user_filepath

    # Fallback to the original path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, 'data', original_filename)

def read_fasta_sequences_direct():
    """
    Reads sequences from the swissprot.fasta.txt file, yielding them one by one.
    """
    filepath = get_data_path('swissprot.fasta.txt')
    try:
        with open(filepath, 'r') as f:
            for record in SeqIO.parse(f, 'fasta'):
                yield record
    except FileNotFoundError:
        print(f"Error: {filepath} not found.")

# Global cache variable
_fasta_cache = None 

def read_fasta_sequences():
    """
    Cached version - loads once, then yields from cache.
    Returns tuples of (seq_id, sequence_string) instead of SeqIO.Record objects.
    """
    global _fasta_cache
    
    if _fasta_cache is None:
        filepath = get_data_path('swissprot.fasta.txt')
        _fasta_cache = PickledFastaCache(filepath).load_with_cache()
    
    return _fasta_cache.iter_records()

def get_sequence_by_identifier(identifier, sequence_iterator=None):
    """
    Retrieves a single sequence from the FASTA file by its accession number or index.
    This does a sequential search.
    """
    if sequence_iterator is None:
        sequence_iterator = read_fasta_sequences()
    if isinstance(identifier, str):
        for record in sequence_iterator:
            if identifier in record.id:
                return record
    elif isinstance(identifier, int):
        for i, record in enumerate(sequence_iterator):
            if i == identifier:
                return record
    return None

def read_swissprot_records():
    """
    Reads and parses records from the swissprot.dat.txt file, yielding them one by one.
    """
    filepath = get_data_path('swissprot.dat.txt')
    try:
        with open(filepath, 'r') as f:
            for record in SwissProt.parse(f):
                yield record
    except FileNotFoundError:
        print(f"Error: {filepath} not found.")

def benchmark():
    start = time.time()
    proteins = read_fasta_sequences()
    for p in proteins:
        if p.id == 'foo' :
            print("found foo")
    elapsed = time.time() - start
    print(f"Execution time: {elapsed:.4f} seconds")

def main():
    # Just read one sequence from the database and show it.
    print( get_sequence_by_identifier( 1 ))

if __name__ == "__main__":
    main()
    benchmark()
