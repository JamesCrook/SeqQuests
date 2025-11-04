# Data Munger

The `data_munger.py` script is a command-line tool responsible for processing raw protein data from a Swiss-Prot file (`swissprot.dat.txt`). Its primary purpose is to read this data, apply a series of filters, and then write the resulting protein sequences to a new file in FASTA format.

## Key Features

- **Swiss-Prot Parsing:** Using Biopython, it reads and parses the multi-line format of Swiss-Prot data files.
- **Protein Filtering:** It applies filters to select for high-quality, well-characterized proteins. For example, requiring any filtered protein have at least one GO term, EC number, or Pfam domain associated with it. The filtering can restrict down to a subset of source organisms if so desired.
- **FASTA Output:** The script generates a clean FASTA file containing the ids/names and sequences of the proteins that pass the filtering criteria.

## Test Data
This repo includes the first few tens of proteins from swisport in /data as test data. This will be used if there is no file at the configured path in script sequences.py.

## Performance Optimization

The script uses sequences.py for file access. That script, when reading already produced FASTA format data utilizes Python's `pickle` modul, creating a pickle file if none was present. Loading data from this binary pickle file is substantially faster than re-parsing the text-based FASTA file.
