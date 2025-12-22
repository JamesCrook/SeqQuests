# Smith Waterman Speed

The metal SW implementation handles strips of cells 40 wide and the height of the query sequence.

This results in very low I/O requirements for each thread, as only the strip boundary is I/O, whilst the work done is the area inside. I couldn't increase above 40 as this is the sweet spot for metal internal registers.

I can launch a large number of threads, 65,536 on a Mac M4 Pro, and they all work exactly in lock step. The only branching is in 'max'/'select' calls, which are efficient intrinsics.

* Array index order matters hugely. The fastest increasing index MUST be the thread index.
* I only find scores, not locations. Less than 1 in 100 comparisons is above threshold. A second CPU pass to find the alignment and locations is just fine. 
* I use uint16 arithmetic, with an offset of 32 to allow for negative numbers down to -32. Very high scores won't be reported accurately, but this is fine. Scores that high are compelling evidence of relatedness. The actual score can be found in a later pass. Using uint16 rather than int32 means less I/O.
* I do not offer the gap openning penalty of SW, only the gap extension penalty, making this a simpler less expensive variant.

