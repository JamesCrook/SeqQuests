# sequences.py should insulate other modules from knowing what file the sequences come from and their underlying format. When initialised, it should check availability of the data files at its configured path and if not fall back to using the data in /data

# it should read from /data/swissprot.dat.txt, if needing full annotated data.
# it should read from /data/swissprot.fasta.txt, if needing just sequence and identification

import os

def get_data_path(filename):
    # This is a placeholder for a more robust configuration.
    # For now, it defaults to the 'data' directory.
    # A real implementation would check a configured path first.
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, 'data', filename)

def read_fasta_sequences():
    """
    Reads sequences from the swissprot.fasta.txt file.
    """
    filepath = get_data_path('swissprot.fasta.txt')
    sequences = []
    try:
        with open(filepath, 'r') as f:
            header = None
            sequence_lines = []
            for line in f:
                line = line.strip()
                if line.startswith('>'):
                    if header:
                        sequences.append((header, ''.join(sequence_lines)))
                    header = line
                    sequence_lines = []
                else:
                    sequence_lines.append(line)
            if header:
                sequences.append((header, ''.join(sequence_lines)))
    except FileNotFoundError:
        print(f"Error: {filepath} not found.")
    return sequences

def read_dat_records():
    """
    Reads and parses records from the swissprot.dat.txt file.
    """
    filepath = get_data_path('swissprot.dat.txt')
    records = []
    try:
        with open(filepath, 'r') as f:
            record_lines = []
            for line in f:
                if line.startswith('//'):
                    if record_lines:
                        records.append(parse_dat_record(record_lines))
                        record_lines = []
                else:
                    record_lines.append(line)
    except FileNotFoundError:
        print(f"Error: {filepath} not found.")
    return records

def parse_dat_record(lines):
    """
    Parses a single record from the .dat file.
    """
    record = {}
    for line in lines:
        key = line[:2]
        value = line[5:].strip()
        if key in record:
            if isinstance(record[key], list):
                record[key].append(value)
            else:
                record[key] = [record[key], value]
        else:
            record[key] = value
    return record

if __name__ == '__main__':
    fasta_data = read_fasta_sequences()
    print(f"Read {len(fasta_data)} sequences from FASTA file.")

    dat_data = read_dat_records()
    print(f"Read {len(dat_data)} records from .dat file.")
