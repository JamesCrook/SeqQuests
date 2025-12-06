## Dev Log

There is little call for a detailed development log, as Git history shows what was done when.

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
@142,363 on 01 Dec at 16:00 4.7 seconds/protein. est 15 day search.

* 01 Dec: M2 - New run with Titin optimisation; expected 2x faster.

@000,007 on 01 Dec at 16:27 estimating 5 days  7 hrs (based on PMEs). 
@002,843 on 02 Dec at 02:00 estimating 4 days 21 hrs (based on PMEs). (41 days on proteins)
@007,561 on 02 Dec at 13:00 estimating 5 days 15 hrs (based on PMEs). (32 days on proteins)
@012,954 on 03 Dec at 00:06 estimating 6 days  5 hrs (based on PMEs). (29 days on proteins)
@020,990 on 03 Dec at 13:43 estimating 6 days 16 hrs (based on PMEs). (26 days on proteins)
@036,893 on 04 Dec at 12:42 estimating 7 days  6 hrs (based on PMEs). (22 days on proteins)
@046,105 on 04 Dec at 23:50 estimating 7 days 11 hrs (based on PMEs). (21 days on proteins)
@083,585 on 06 Dec at 10:45 estimating 7 days 22 hrs (based on PMEs). (17 days on proteins)

### Additional Dev History

ed10e949fd3632d98454f6569a9d350223b4f60f fixed the 1-in-40 bug. The bug arose because UNROLL is 40, and a sequence which ended on the last item of UNROLL would steal the score from the next sequence. 

Post search analysis software now sufficiently mature (tested with the buggy data) that I am ready for the results file.

e7d73cbbd452b1babd91a4dab12d78f6d2a992f1 introduced the all-recs parameter, default false, so by default we now only compares proteins at or later in the database. This gives slightly less location information, but is fine for a score-only search.

35033228b84145572f0c0361ea73d050d13dcc93 added proper queues for proteins under analysis so that the unrolled block can handle multiple short proteins. The filter to proteins > 44 aa's long has been removed. The main beneficiaries are short neuro toxins which were previously excluded. Not yet being used in the long running search.

1st Dec 2025: Added better benchmarking speed diagnostics. Titins take many steps to complete, leaving all but 40 threads idle. By excluding proteins above 8,000aa estimated search time drops on M4 Pro from about 9 days to about 3. 2/3 of time previously was wasted on M4, estimated 1/3 of time was wasted on M2 which has half the threads. Now speed has been further enhanced by sorting the proteins, largest first, so I don't have to exclude the Titins (Mouse and Human)

4th Dec 2025: Experimenting with M4 Pro whilst the M2 runs, noticed a slow down due to sleep. Added caffeinate -i. 100 GCUPS up from 54 GCUPS on M4. With the M4 now on the 700aa proteins, 50,000 proteins in, CPU time is taking 20% of the total time, and the serial nature of GPU then CPU rather than overlapping them is costing us. We're getting 90 GCUPS, where 110 GCUPS ought to be achieved - so double buffering is becoming an essential. Doing largest protein first makes protein count a poor guide to progress, and I will switch it up to report percentage of amino acids processed and drop the protein count predictions.

5th Dec 2025: Switched to GCUP based time estimation, %aa's done, and dropped protein count estimation. M4 has overtaken M2 (with significantly less run time) and is 128,947 proteins in (73% task complete). 28% of CPU time should be reclaimable by overlapping.