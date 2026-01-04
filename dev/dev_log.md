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

* 01 Dec: M2 - New run with Titin optimisation; expected 2x faster. It is.

@000,007 on 01 Dec at 16:27 estimating 5 days  7 hrs (based on PMEs). 
@002,843 on 02 Dec at 02:00 estimating 4 days 21 hrs (based on PMEs). (41 days on proteins)
@007,561 on 02 Dec at 13:00 estimating 5 days 15 hrs (based on PMEs). (32 days on proteins)
@012,954 on 03 Dec at 00:06 estimating 6 days  5 hrs (based on PMEs). (29 days on proteins)
@020,990 on 03 Dec at 13:43 estimating 6 days 16 hrs (based on PMEs). (26 days on proteins)
@036,893 on 04 Dec at 12:42 estimating 7 days  6 hrs (based on PMEs). (22 days on proteins)
@046,105 on 04 Dec at 23:50 estimating 7 days 11 hrs (based on PMEs). (21 days on proteins)
@083,585 on 06 Dec at 10:45 estimating 7 days 22 hrs (based on PMEs). (17 days on proteins)
@097,280 on 06 Dec at 20:45 estimating 8 days  0 hrs (based on PMEs). (16 days on proteins)
@168,340 on 08 Dec at 20:00 estimating 8 days  1 hrs (based on PMEs). (12 days on proteins)
Search aborted on 8th Dec due to 32,000 bug. Better to produce correct dataset with the new faster code.

@000,000 on 08 Dec at 20:00  00% done, estimating 4 days  8 hrs
@007,380 on 09 Dec at 13:00  15% done, estimating 4 days  3 hrs
@066,000 on 11 Dec at 01:50  54% done, estimating 4 days  0 hrs
@141,815 on 11 Dec at 22:40  76% done, estimating 3 days 23 hrs
@234,467 on 12 Dec at 12:16  90% done, estimating 3 days 23 hrs
@387,777 on 12 Dec at 21:10  99% done, estimating 2 days 23 hrs
@573,660 on 13 Dec at 23:35 100% done, estimating 4 days  0 hrs

Actual was 4 days 3hrs on M2.
### Additional Dev History

ed10e949fd3632d98454f6569a9d350223b4f60f fixed the 1-in-40 bug. The bug arose because UNROLL is 40, and a sequence which ended on the last item of UNROLL would steal the score from the next sequence. 

Post search analysis software now sufficiently mature (tested with the buggy data) that I am ready for the results file.

e7d73cbbd452b1babd91a4dab12d78f6d2a992f1 introduced the all-recs parameter, default false, so by default we now only compares proteins at or later in the database. This gives slightly less location information, but is fine for a score-only search.

35033228b84145572f0c0361ea73d050d13dcc93 added proper queues for proteins under analysis so that the unrolled block can handle multiple short proteins. The filter to proteins > 44 aa's long has been removed. The main beneficiaries are short neuro toxins which were previously excluded. Not yet being used in the long running search.

1st Dec 2025: Added better benchmarking speed diagnostics. Titins take many steps to complete, leaving all but 40 threads idle. By excluding proteins above 8,000aa estimated search time drops on M4 Pro from about 9 days to about 3. 2/3 of time previously was wasted on M4, estimated 1/3 of time was wasted on M2 which has half the threads. Now speed has been further enhanced by sorting the proteins, largest first, so I don't have to exclude the Titins (Mouse and Human)

4th Dec 2025: Experimenting with M4 Pro whilst the M2 runs, noticed a slow down due to sleep. Added caffeinate -i. 100 GCUPS up from 54 GCUPS on M4. With the M4 now on the 700aa proteins, 50,000 proteins in, CPU time is taking 20% of the total time, and the serial nature of GPU then CPU rather than overlapping them is costing us. We're getting 90 GCUPS, where 110 GCUPS ought to be achieved - so double buffering is becoming an essential. Doing largest protein first makes protein count a poor guide to progress, and I will switch it up to report percentage of amino acids processed and drop the protein count predictions.

5th Dec 2025: Switched to GCUP based time estimation, %aa's done, and dropped protein count estimation. M4 has overtaken M2 (with significantly less run time) and is 128,947 proteins in (73% task complete). 28% of CPU time should be reclaimable by overlapping.

6th Dec 2025: Got the 'coiled' implementation working where CPU/GPU usage overlap. 122 GCUPS with this design. Helped by less data going in in this design. The M4 (running part time) has now massively overtaken the M2 running the older software full time. It's credibly estimating 6hrs to completion, and 4x the speed. 4x is reasonable. The M4 is about twice as fast, and the software by overlapping is on the home stretch going at nearly double the speed that it would without the overlapping.

8th Dec 2025: Analysing the full results from M4, found the 32,000 bug - namely very large scores above 32,000 can/will overflow into the next protein, even though they can never go above 32,767 in the matrix, due to int_16 overflow. The fix I've now made is to pull the full 32,767 down, rather than the earlier assumption that no proteins could score that high. Titin vs Titin will have a higher than 32,000 score, and in fact saturates at 32,767. Fortunately the reconstruction is done in int32's, so we get the speed of search from int16 use and sustain accuracy by doing the reconstruction later. This incidentally suggests I can more than double the speed by working in int8s and doing the same trick.

9th Dec 2025: Starting some optimisation steps.
Testing start at 70,000 and 10 sequences is currently running at:
122 GCUPs 49% CPU - Baseline
128 GCUPs 52% CPU - aa and PAM now int8
121 GCUPs 46% CPU - Writing direct to the correct entry.
121 GCUPs 50% CPU - With the clever 8 bit values.
 75 GCUPs 30% CPU - When I also increase UNROLL to 80.
183 GCUPs 62% CPU - With flipped PAM indexing and capture of residues.

So no real gain from int16 -> int8 on the intermediate values.

11 Dec 2025: The M4 run with max 223 saturation has completed, so I now have my first clean dataset. Using 65503 saturation seems to have very similar perf to using 223 saturation, making it relatively not worthwhile having a two stage 223 filter-and-then-rescore pipeline. So I am rerunning with 65503. Currently 190 GCUPS and estimating 1d 7h all-on-all search. Discussion with Gemini about where we lose perf, and it looks like packing multiple queries into one kernel will be a good solution. I think I should put the thresholding logic in the kernel, as that will mean less data is written.   

12 Dec 2025:  

As before, at 70,000 and 10 sequences:
202 GCUPs 53% CPU - With recent size reductions and flipped data.
211 GCUPs 64% CPU - With preparation of aa data in thread order.
246 GCUPs 67% CPU - Up the number of threads.

These optimisations included dead ends, such as using ushort4, doing some buffer creation before the waitfor, reducing threadgroup size. Also explorations using Inspector that showed 1/3rd of task is hitting launch speed limits and 2/3rds Int16.Arithmetic/Conditionals limits. 

13 Dec 2025:

M4 search has now completed too (22:26 Dec 11 to 10:50 AM Dec 13 paused day time Dec 12). 4,126,706,362 bytes

4 Jan 2026:

Nearing first release. These are must-fix issues:
* Copy Alignment button broken
* Should scroll to top on a new pair
* Repsoition help panel so fewer crossed arrows