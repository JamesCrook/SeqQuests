# sequences.py should insulate other modules from knowing what file the sequences come from and their underlying format. When initialised, it should check availability of the data files at its configured path and if not fall back to using the data in /data

# it should read from /data/swissprot.dat.txt, if needing full annotated data.
# it should read from /data/swissprot.fasta.txt, if needing just sequence and identification

import os
from Bio import SwissProt, SeqIO

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

def read_fasta_sequences():
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

def get_sequence_by_identifier(identifier, sequence_iterator=None):
    """
    Retrieves a single sequence from the FASTA file by its accession number or index.
    """
    if sequence_iterator is None:
        sequence_iterator = read_fasta_sequences()
    if isinstance(identifier, str):
        for record in sequence_iterator:
            if identifier in record.id:
                return (record.description, str(record.seq))
    elif isinstance(identifier, int):
        for i, record in enumerate(sequence_iterator):
            if i == identifier:
                return (record.description, str(record.seq))
    return None

def read_dat_records():
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

