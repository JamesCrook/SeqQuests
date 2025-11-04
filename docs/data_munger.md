# Data Munger

The `data_munger.py` script is a command-line tool responsible for processing raw protein data from a Swiss-Prot file (`swissprot.dat.txt`). Its primary purpose is to read this data, apply a series of filters, and then write the resulting protein sequences to a new file in FASTA format.

## Key Features

- **Swiss-Prot Parsing:** It reads and parses the complex, multi-line format of Swiss-Prot data files.
- **Protein Filtering:** It applies filters to select for high-quality, well-characterized proteins. A key requirement is that any filtered protein must have at least one GO term, EC number, or Pfam domain associated with it.
- **FASTA Output:** The script generates a clean FASTA file containing the sequences of the proteins that pass the filtering criteria.

## Performance Optimization

To significantly speed up subsequent access to the filtered FASTA data, the `data_munger.py` script utilizes Python's `pickle` module. After generating the FASTA file, it also creates a pickled version of the data. Loading data from this binary pickle file is substantially faster than re-parsing the text-based FASTA file, which benefits other tools in the project that consume this data.
