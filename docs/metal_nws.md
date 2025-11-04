# Metal NWS Searcher

`metal_nws.mm` is a high-performance, command-line tool that performs a Needleman-Wunsch-Smith (NWS) local sequence alignment search. It is written in Objective-C and utilizes Apple's Metal framework to dramatically accelerate the search process by running the computation on the GPU.

## Core Functionality

The tool takes a query protein sequence and searches for local alignments against a large database of protein sequences in FASTA format. It is designed for performance and operates directly on pre-compiled binary data, avoiding the overhead of parsing text files at runtime.

## GPU Acceleration Strategy

The power of `metal_nws.mm` comes from its custom Metal compute kernel, which implements a highly parallelized version of the NWS algorithm.

### PAM Look-Up Table (LUT)

For each search, the tool pre-computes a look-up table (LUT) for the query sequence based on the PAM substitution matrix. This `pam_lut` is a `int16` array with a size 32 times that of the query sequence. This pre-computation allows the GPU kernel to quickly fetch substitution scores without needing to perform expensive matrix lookups during the alignment calculation.

### Parallel Execution

The search is parallelized across the entire database of sequences. The workload is divided as follows:

-   **COLS:** This compile-time constant defines how many database sequences are processed in parallel by the GPU. Each sequence is assigned to a separate compute pipeline.
-   **UNROLL:** This constant determines how many elements of a sequence are processed by a single GPU thread in one go. It represents a block of data that each thread handles, allowing for efficient memory access and computation.

### Kernel Output

The Metal kernel executes the NWS algorithm and, for each database sequence, it returns an array of scores. Specifically, it calculates the **maximum local alignment score ending at each residue** in the database sequence. This provides a detailed view of all potential local alignment hits within each sequence, rather than just a single overall score.
