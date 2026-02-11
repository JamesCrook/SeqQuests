# Match Explorer UI
match_explorer.html provides a web based interface for browsing sequence hits files featuring pairs of proteins, such as sw_finds.txt

Here is an example of one such reported similar pair.

```
B1HPV0-Q72H22 s(299) Length: 307/608
 Heme A synthase {ECO:0000255|HAMAP-Rule:MF_01664}; Lysinibacillus sphaericus (strain C3-41).
 Protoheme IX farnesyltransferase; Thermus thermophilus (strain ATCC BAA-163 / DSM 7039 / HB27).
```

The user interface provides display of the source swiss-prot files, and the alignment of the two proteins.

----

There are three lists to choose from:
* The curated list, ~20 sequence similarities that were reported on in the proposed updates to SwissProt.
* A list of standard matches, that do not have significant sequence bias. These are similarity pairs where it is not algorithmically obvious from the data files that the simialrity is known. For example pfams don't match, and the neame does not have an exact match. Often it is clear that the simialrity is not surprising.
* A list of biassed matches. The higher scores of biassed matches are less compelling than for standard matches. The matching algorithm assumes normal amino acid frequencies. If the set of amino acids being used is more restrictive, matches become more likely.

## Copy

The copy buttons copy text to the clip board. 

## MultiScroller

Rather than two separate scrollers, the multi scroller mode makes it so that dragging one list up or down also causes scrolling in the other. This can be helpful when navigating the list as it saves switching back and forth between the two scroll bars.
