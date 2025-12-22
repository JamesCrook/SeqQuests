# AI Interpretation

The hits explorer that explores pairs of matching proteins can paste text to the clipboard that can then be pasted as a prompt to a mainstream AI/LLM to ask about found similarities.

## Strengths
* The AI can pay attention to many details of the data files, using pfam, eggNOG, InterPro, Alternative products and FT records. It can also go beyond and see that from the title of cited papers a family resemblance is known already, including taking account of older terminology and naming.
* The AI has background knowledge about many common patterns in proteins, such as signalling sequences and metal binding motifs.

The AI is a tremendous boost as an augmented web searcher, finding evidence that a protein similarity is in fact already known that may be non-obvious from the sequence data files. It is also great about giving background information about proteins one might be unfamiliar with.

## Weaknesses
* The AI tends to be very dismissive of sequence similarities that are not already known. Unless careful prompted it will tend to disregard a weak similarity that does not include an active site. This can matter a great deal. Inactivated enzymes can take on new roles in binding but not transforming substrates - and the similarities can be very informative. The AI also tends to treat metal binding and weak coiled coil similarities as 'merely' convergent evolution, pointing out the heptad repeat or the biassed composition. 
* The AI may too readily get excited about a similarity that it knows was an important step forward in understanding. It too easily conflates the rediscovery with the original discovery of a hidden similarity or controversial but now accepted family regrouping which it knows about.
* When looking for eggNOG on line, AI will keep finding the drink.

The AI tendencies need to be counterbalanced by an understanding of [the Twilight Zone](./twilight-zone.md). Better prompting may help overcome the AI engine's tendencies.