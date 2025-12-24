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
import threading

from config import DATA_DIR, PROJECT_ROOT


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
        print(f"DEBUG: Looking for cache at: {self.cache_file.absolute()}")
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

    # An alternative init, intended to put the cache in a specific
    # place relative to the source file.
    def __init_unused__(self, data_file, cache_dir=".cache"):
        # Convert data_file to a Path object immediately
        self.data_file = Path(data_file).absolute()
        
        # Ensure cache_dir is absolute, relative to the data file's parent
        self.cache_dir = self.data_file.parent / cache_dir
        
        # Create the directory if it doesn't exist
        self.cache_dir.mkdir(exist_ok=True)
        
        super().__init__(str(self.data_file), str(self.cache_dir))
        self.handle = None  # File handle for the data file


    def load_sequences(self, data_file, file_format):

        start_time = time.time()
        self.sequences = OrderedDict()
        self.seq_list = []

        # Use binary mode to ensure tell() is accurate
        with open(data_file, 'rb') as f:
            record_starts = []
            while True:
                pos = f.tell()
                line = f.readline()
                if not line: break
                if line.startswith(b'ID'):
                    record_starts.append(pos)

            for i in range(len(record_starts)):
                f.seek(record_starts[i])
                # Read first few lines to get ID and AC
                chunk = f.read(1024).decode('latin-1')
                lines = chunk.splitlines()
                
                # Extract ID (Entry Name)
                id_line = lines[0]
                seq_id = id_line.split()[1].strip(';')
                
                # Extract Accession (Optional but recommended)
                # AC line usually follows ID line
                ac_id = None
                for line in lines:
                    if line.startswith('AC'):
                        ac_id = line.split()[1].strip(';')
                        break

                start_pos = record_starts[i]
                end_pos = record_starts[i+1] if i+1 < len(record_starts) else None
                if end_pos is None:
                    f.seek(0, 2)
                    end_pos = f.tell()

                record_info = (seq_id, start_pos, end_pos)
                
                # Store by Entry Name
                self.sequences[seq_id] = record_info
                # Store by Accession if found
                if ac_id:
                    self.sequences[ac_id] = record_info
                    
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
    user_path = DATA_DIR
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


class DataManager:
    """
    Singleton-like class to manage sequence caches.
    This replaces global variables with a centralized manager.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DataManager, cls).__new__(cls)
                    cls._instance._fasta_cache = None
                    cls._instance._swissprot_cache = None
        return cls._instance

    def reset(self):
        """Reset caches - useful for testing"""
        self._fasta_cache = None
        self._swissprot_cache = None

    def get_fasta_cache(self):
        if self._fasta_cache is None:
            filepath = get_data_path('swissprot.fasta.txt')
            self._fasta_cache = PickledSequenceCache(filepath).load_with_cache('fasta')
        return self._fasta_cache

    def get_swissprot_cache(self, file_format='swiss_index'):
        if self._swissprot_cache is None:
            filepath = get_data_path('swissprot.dat.txt')
            if file_format == 'swiss_index':
                self._swissprot_cache = SwissIndexCache(filepath).load_with_cache(file_format)
            else:
                self._swissprot_cache = PickledSequenceCache(filepath).load_with_cache(file_format)
        return self._swissprot_cache


# Convenience wrapper functions to maintain backward compatibility
# but use the DataManager instance.

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


def read_fasta_sequences():
    """
    Cached version - loads once, then yields from cache.
    Returns tuples of (seq_id, sequence_string) instead of SeqIO.Record objects.
    """
    return DataManager().get_fasta_cache().iter_records()

def read_swissprot_sequences(file_format='swiss_index'):
    """
    Cached version - loads once, then yields from cache.
    Returns tuples of (seq_id, sequence_string) instead of SeqIO.Record objects.
    """
    return DataManager().get_swissprot_cache(file_format)

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

def get_protein( identifier ):
    cache = DataManager().get_swissprot_cache(file_format='swiss_index')
    record = cache.get_record( identifier )

    # Later I may add back the old alternative that gets a record by a number
    #record = cache.get_record_by_index(number)

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

def benchmark():
    start = time.time()
    proteins = read_fasta_sequences()
    for p in proteins:
        protein_id = p.id if hasattr(p, 'id') else p.accessions[0]
        if protein_id == 'foo' :
            print("found foo")
    elapsed = time.time() - start
    print(f"Execution time: {elapsed:.4f} seconds")

def test_swiss_index_access():
    """
    Tests the SwissIndexCache by accessing records by index and ID.
    """
    DataManager().reset()
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

def main():
    parser = argparse.ArgumentParser(description="Sequence access utilities")
    parser.add_argument('--test', action='store_true', dest='test',
                        help='Enable test mode')
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark")
    parser.add_argument("--get", type=int, help="Get sequence by index")

    parser.set_defaults(test=False)    
    args = parser.parse_args()

    if args.test:
        print(f"Running in test mode...")
        test_swiss_index_access()
    elif args.benchmark:
        benchmark()
    elif args.get is not None:
        print(get_sequence_by_identifier(args.get))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
