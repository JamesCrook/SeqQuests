## Dev Log

There is little calll for a detailed development log, as Git history shows what was done when.

However, I am tracking performance, and so am tracking early runs of the all-on-all search code.


### All-on-all Runs

M2 is a Mac M2 Pro with 16GB of RAM.
4.14 GB uniprot_sprot.dat, downloaded on 27 Oct
286.8 MB uniprot_sprot.fasta, downloaded on 27 Oct


#### PAM 250, Indel 10.
* 3rd Nov: M2 - Aborted on 24th Nov after around 300,000 sequences, as 1 in 40 sequence scores were assigned to the wrong sequences.
* 24th Nov: M2 - New run with 1 in 40 bug fix
* 28th Nov:  " - Run continues now with all-recs parameter (2x faster)

@114,330 on 30 Nov at 00:39
@131,189 on 01 Dec at 01:30

### Additional Dev History

ed10e949fd3632d98454f6569a9d350223b4f60f fixed the 1-in-40 bug. The bug arose because UNROLL is 40, and a sequence which ended on the last item of UNROLL would steal the score from the next sequence. 

Post search analysis software now sufficiently mature (tested with the buggy data) that I am ready for the results file.

e7d73cbbd452b1babd91a4dab12d78f6d2a992f1 introduced the all-recs parameter, default false, so by default we now only compares proteins at or later in the database. This gives slightly less location information, but is fine for a score-only search.

35033228b84145572f0c0361ea73d050d13dcc93 added proper queues for proteins under analysis so that the unrolled block can handle multiple short proteins. The filter to proteins > 44 aa's long has been removed. The main beneficiaries are short neuro toxins which were previously excluded. Not yet being used in the long running search.

1st Dec 2025: Added better benchmarking speed diagnostics. Titins take many steps to complete, leaving all but 40 threads idle. By excluding proteins above 8,000aa estimated search time drops on M4 Pro from about 9 days to about 3. 2/3 of time previously was wasted on M4, estimated 1/3 of time was wasted on M2 which has half the threads.