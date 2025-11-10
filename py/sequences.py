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



class SequenceCache:
    def __init__(self):
        self.sequences = OrderedDict()  # Maps seq_id -> record object
        self.seq_list = []  # For fast index-based access: [record, record, ...]
        self.load_time = 0

    def load_sequences(self, data_file, file_format):
        """Load entire sequence file into memory"""
        start = time.time()
        self.sequences = OrderedDict()
        self.seq_list = []

        # Use the correct parser based on file format
        with open(data_file, 'r') as handle:
            if file_format == 'fasta':
                parser = SeqIO.parse(handle, "fasta")
            elif file_format == 'swiss':
                parser = SwissProt.parse(handle)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")

            for record in parser:
                # For FASTA, record.id is fine. For SwissProt, the primary accession is better.
                seq_id = record.accessions[0] if hasattr(record, 'accessions') and record.accessions else record.id
                self.sequences[seq_id] = record
                self.seq_list.append(record)
        
        self.load_time = time.time() - start
        print(f"Loaded {len(self.sequences)} sequences in {self.load_time:.2f}s")
        return self

    def get_sequence(self, seq_id):
        """Get sequence by ID (returns bytes)"""
        record = self.sequences.get(seq_id)
        if not record:
            return None
        # Handle both SeqRecord (from FASTA) and SwissProt Record
        seq_data = record.sequence if hasattr(record, 'sequence') else record.seq
        return bytes(seq_data)

    def get_description(self, seq_id):
        """Get description by ID"""
        record = self.sequences.get(seq_id)
        return record.description if record else None

    def get_record(self, seq_id):
        """Get record object by ID"""
        return self.sequences.get(seq_id)

    def get_sequence_by_index(self, index):
        """Get sequence by index (0-based, returns bytes)"""
        if 0 <= index < len(self.seq_list):
            record = self.seq_list[index]
            seq_data = record.sequence if hasattr(record, 'sequence') else record.seq
            return bytes(seq_data)
        return None

    def get_id_by_index(self, index):
        """Get sequence ID by index"""
        if 0 <= index < len(self.seq_list):
            record = self.seq_list[index]
            return record.accessions[0] if hasattr(record, 'accessions') and record.accessions else record.id
        return None

    def get_record_by_index(self, index):
        """Get record object by index"""
        if 0 <= index < len(self.seq_list):
            return self.seq_list[index]
        return None

    def get_subsequence(self, seq_id, start, end):
        """Get slice of sequence by ID"""
        seq = self.get_sequence(seq_id)
        return seq[start:end] if seq else None

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
        return [
            rec.accessions[0] if hasattr(rec, 'accessions') and rec.accessions else rec.id
            for rec in self.seq_list
        ]

    def iter_sequences(self):
        """Iterate over (seq_id, sequence) tuples - DEPRECATED, use iter_records()"""
        for record in self.seq_list:
            seq_id = record.accessions[0] if hasattr(record, 'accessions') and record.accessions else record.id
            seq_data = record.sequence if hasattr(record, 'sequence') else record.seq
            yield (seq_id, bytes(seq_data))

    def iter_records(self):
        """Iterate over record objects"""
        yield from self.seq_list

    def __iter__(self):
        """Make the cache itself iterable, yielding records"""
        return self.iter_records()


class PickledSequenceCache(SequenceCache):
    def __init__(self, data_file, cache_dir=".cache"):
        super().__init__()  # Call parent __init__
        self.data_file = Path(data_file)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def load_with_cache(self, file_format):
        format_suffix = f"_{file_format}" if file_format else ""
        self.cache_file = self.cache_dir / f"{self.data_file.stem}{format_suffix}.pkl"
        """Load from pickle if available, otherwise parse the data file"""
        # Check if cache exists and is newer than the data file
        if (self.cache_file.exists() and 
            self.cache_file.stat().st_mtime > self.data_file.stat().st_mtime):
            # quick return, if already has the sequences.
            if hasattr( self, 'sequences' ) and self.sequences:
                return self
            start = time.time()
            with open(self.cache_file, 'rb') as f:
                data = pickle.load(f)
                self.sequences = data['sequences']
                self.seq_list = data['seq_list']
            self.load_time = time.time() - start
            print(f"Loaded {len(self.sequences)} sequences from cache in {self.load_time:.2f}s")
        else:
            self.load_sequences(self.data_file, file_format)
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
    user_path = os.path.expanduser( '~/BigData/bio_sequence_data' )
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

_fasta_cache = None
_swissprot_cache = None

def read_fasta_sequences():
    """
    Cached version - loads once, then yields from cache.
    Returns tuples of (seq_id, sequence_string) instead of SeqIO.Record objects.
    """
    global _fasta_cache
    
    if _fasta_cache is None:
        filepath = get_data_path('swissprot.fasta.txt')
        _fasta_cache = PickledSequenceCache(filepath).load_with_cache('fasta')
    
    return _fasta_cache.iter_records()

def read_swissprot_sequences():
    """
    Cached version - loads once, then yields from cache.
    Returns tuples of (seq_id, sequence_string) instead of SeqIO.Record objects.
    """
    global _swissprot_cache

    if _swissprot_cache is None:
        filepath = get_data_path('swissprot.dat.txt')
        _swissprot_cache = PickledSequenceCache(filepath).load_with_cache('swiss')

    return _swissprot_cache.iter_records()

def get_sequence_by_identifier(identifier, db_name='swissprot'):
    """
    Retrieves a single sequence from the specified database by its accession number or index.
    This does a sequential search.
    """
    if db_name == 'swissprot':
        sequence_iterator = read_swissprot_sequences()
    else:
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

def benchmark():
    start = time.time()
    proteins = read_fasta_sequences()
    for p in proteins:
        protein_id = p.id if hasattr(p, 'id') else p.accessions[0]
        if protein_id == 'foo' :
            print("found foo")
    elapsed = time.time() - start
    print(f"Execution time: {elapsed:.4f} seconds")

def main():
    # Just read one sequence from the database and show it.
    print( get_sequence_by_identifier( 1 ))

def verify_sequences():
    """
    Compares sequences from FASTA and Swiss-Prot caches to find mismatches.
    """
    fasta_sequences = list(read_fasta_sequences())
    swissprot_sequences = list(read_swissprot_sequences())

    mismatches = 0
    missing_in_swissprot = 0

    start = time.time()
    for i, fasta_record in enumerate(fasta_sequences):
        if i < len(swissprot_sequences):
            swissprot_record = swissprot_sequences[i]
            if fasta_record.seq != swissprot_record.sequence:
                mismatches += 1
        else:
            missing_in_swissprot += 1
        if i%1000 == 0:
            print( f"Sequence:{i}")

    print(f"Sequence Verification Report:")
    print(f"Mismatches: {mismatches}")
    print(f"Missing in Swiss-Prot: {missing_in_swissprot}")
    elapsed = time.time() - start
    print(f"Execution time: {elapsed:.4f} seconds")

if __name__ == "__main__":
    main()
    benchmark()
    verify_sequences()
