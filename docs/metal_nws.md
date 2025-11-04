# Metal NWS Searcher

`metal_nws.mm` is a command-line tool that performs a Needleman-Wunsch-Smith (NWS) local sequence alignment search. It is written in Objective-C and utilizes Apple's Metal framework to GPU accelerate search.

## Core Functionality

The tool takes a query protein sequence and searches for local alignments against a database of protein sequences in FASTA format. It operates directly on pre-compiled binary data, avoiding the overhead of parsing text files at runtime. The binary data is prepared using script `prepare_data.py`

## PAM Look-Up Table (LUT)

For each search, the tool pre-computes a look-up table (LUT) for the query sequence based on the PAM substitution matrix. This `pam_lut` is a `int16` array with a size 32 times that of the query sequence. This lut removes one step of indirect access from the alignment calculation.

The actual amino acid alphabet in the PAM substitution matrix is 26. 32 is the next largest power of 2. The characater '@' is used for end of sequence, and has a penalty of 30,000 for matching anything. This is part of resetting the scores at the end of sequences without doing branching.

## Parallel Execution

The search of one query sequence is against a database of sequences. The workload is divided as follows:

-   **COLS:** This compile-time constant, usually 4096, defines how many database sequences are processed in parallel by the GPU. Each sequence is assigned to a separate thread.
-   **UNROLL:** This constant, usually 32, determines how many elements of a database sequence are processed by a single GPU thread in one go. Each of the COLS threads is working on a grid of size query sequence size x UNROLL. All threads work on the same sized blocks of data.

## Kernel Output

The Metal kernel executes the NWS algorithm and, for each database sequence, it returns an array of scores, each thread returning batches of size UNROLL. These scores are the **maximum local alignment score ending at each residue** in the database sequence. Additionally the threads do a running max for sequences in the UNROLLed block, to get the overall max score for each sequence. 
