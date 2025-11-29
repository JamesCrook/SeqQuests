import os
from Bio import SwissProt, SeqIO
from io import StringIO
import re
import argparse

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


class SwissIndexCache(PickledSequenceCache):
    def __init__(self, data_file, cache_dir=".cache"):
        super().__init__(data_file, cache_dir)
        self.handle = None  # File handle for the data file

    def load_sequences(self, data_file, file_format):
        start_time = time.time()
        self.sequences = OrderedDict()
        self.seq_list = []

        with open(data_file, 'r', encoding='latin-1') as f:
            # Pass 1: Find the start of every record
            record_starts = []
            f.seek(0)
            while True:
                line = f.readline()
                if not line:
                    break
                if line.startswith('ID'):
                    record_starts.append(f.tell() - len(line))

            # Pass 2: Create the index from the discovered record starts
            for i in range(len(record_starts)):
                f.seek(record_starts[i])
                id_line = f.readline()
                # The id is the second word on the ID line, and might have a trailing ';'
                seq_id = id_line.split()[1].strip(';')

                start_pos = record_starts[i]

                if i + 1 < len(record_starts):
                    end_pos = record_starts[i+1]
                else:
                    # For the last record, the end is the end of the file
                    f.seek(0, 2)
                    end_pos = f.tell()

                record_info = (seq_id, start_pos, end_pos)
                self.sequences[seq_id] = record_info
                self.seq_list.append(record_info)

        self.load_time = time.time() - start_time
        print(f"Indexed {len(self.seq_list)} sequences in {self.load_time:.2f}s")
        return self

    def get_record(self, seq_id):
        """Get record object by ID using the index"""
        if self.handle is None:
            self.handle = open(self.data_file, 'r')

        record_info = self.sequences.get(seq_id)
        if not record_info:
            return None

        _, start_pos, end_pos = record_info
        self.handle.seek(start_pos)
        raw_record = self.handle.read(end_pos - start_pos)

        # Use StringIO to parse the raw string data
        record = SwissProt.read(StringIO(raw_record))
        record.raw = raw_record
        return record

    def get_record_by_index(self, index):
        """Get record object by index using the index"""
        if self.handle is None:
            self.handle = open(self.data_file, 'r')

        if 0 <= index < len(self.seq_list):
            _, start_pos, end_pos = self.seq_list[index]
            self.handle.seek(start_pos)
            raw_record = self.handle.read(end_pos - start_pos)

            # Use StringIO to parse the raw string data
            record = SwissProt.read(StringIO(raw_record))
            record.raw = raw_record
            return record
        return None

    def __iter__(self):
        """Iterate over all records in the indexed file, yielding them one by one."""
        for i in range(len(self)):
            record = self.get_record_by_index(i)
            record.item_no = i
            yield record

    def __del__(self):
        if self.handle:
            self.handle.close()


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

def read_swissprot_sequences(file_format='swiss_index'):
    """
    Cached version - loads once, then yields from cache.
    Returns tuples of (seq_id, sequence_string) instead of SeqIO.Record objects.
    """
    global _swissprot_cache

    if _swissprot_cache is None:
        filepath = get_data_path('swissprot.dat.txt')
        if file_format == 'swiss_index':
            _swissprot_cache = SwissIndexCache(filepath).load_with_cache(file_format)
        else:
            _swissprot_cache = PickledSequenceCache(filepath).load_with_cache(file_format)

    return _swissprot_cache

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

def get_protein( number ):
    global _swissprot_cache
    if _swissprot_cache == None:
        cache = read_swissprot_sequences(file_format='swiss_index')
        _swissprot_cache = cache
    cache = _swissprot_cache
    record = cache.get_record_by_index(number)

    pattern = r"RecName:\s*Full=([^;]+)"
    # Search for the pattern in the string
    match = re.search(pattern, record.description)

    full_name = "NAME MISSING"
    if match:
        # group(1) returns the content of the first capturing group () inside the pattern
        full_name = match.group(1)

    result = SimpleNamespace()        
    result.name = f"{full_name}; {record.organism}"
    result.id = record.accessions[0]
    result.entry = record.entry_name
    result.sequence_length = record.sequence_length
    result.full = record

    return result

def test_swiss_index_access():
    """
    Tests the SwissIndexCache by accessing records by index and ID.
    """
    global _swissprot_cache
    _swissprot_cache = None
    print("Testing SwissIndexCache access...")
    cache = read_swissprot_sequences(file_format='swiss_index')

    # Test access by index
    record_by_index = cache.get_record_by_index(2)
    print(f"Record at index 2: {record_by_index.entry_name}")
    print(f"Sequence length of record by index: {len(record_by_index.sequence)}")

    # Test access by ID
    record_by_id = cache.get_record('11011_ASFWA')
    if record_by_id:
        print(f"Record with ID 11011_ASFWA: {record_by_id.entry_name}")
        print(f"Organism of record by ID: {record_by_id.organism}")
        print(f"Sequence length of record by ID: {len(record_by_id.sequence)}")
    else:
        print("Record with ID 11011_ASFWA not found.")

    # Verify some data

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

def main():
    parser = argparse.ArgumentParser(description="Sequence access utilities")
    parser.add_argument("--test", action="store_true", help="Run self-test")
    parser.add_argument("--verify", action="store_true", help="Verify sequences")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark")
    parser.add_argument("--get", type=int, help="Get sequence by index")

    args = parser.parse_args()

    if args.test:
        test_swiss_index_access()
    elif args.verify:
        verify_sequences()
    elif args.benchmark:
        benchmark()
    elif args.get is not None:
        print(get_sequence_by_identifier(args.get))
    else:
        # Default action for backward compatibility or simple check
        print("No action specified. Use --test, --verify, --benchmark, or --get <id>.")

if __name__ == "__main__":
    main()
