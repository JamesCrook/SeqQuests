# SeqQuest Protein Homology Findings: Methods

## Overview

This release documents novel protein sequence homologies discovered through sensitive Smith-Waterman comparison of the UniProt database, with particular focus on "twilight zone" similarities (15-30% identity) that escape standard annotation pipelines.

## Computational Pipeline

### 1. Database

UniProt Swiss-Prot 2025-04, downloaded 27-Oct-2025. Approximately 570,000 protein sequences.

### 2. All-on-all Smith-Waterman Comparison

Metal-accelerated Smith-Waterman alignment using `sw_search.py` (C++/Metal backend via PyObjC), optimized for Apple Silicon.

| Parameter | Value |
|-----------|-------|
| Scoring matrix | PAM250 |
| Gap open penalty | 0 |
| Gap extend penalty | -10 |
| Score threshold | 110 |
| Runtime | ~30 hours on Mac M4 Pro |

**Output:** `sw_results/sw_results.csv` (~3.8 GB)

### 3. Clustering via Maximal Scoring Tree

Pairwise scores assembled into a maximal scoring tree using `tree_builder.py`. This identifies connections *between* protein families rather than redundantly capturing relationships *within* families.

**Outputs:**
- `sw_results/sw_raw_finds.txt` — Tree-reduced finds (three-line format)
- `sw_results/sw_tree.txt` — Same data in tree format (~0.8 GB)

### 4. Automated Filtering

`filter_twilight.py` removes relationships already captured by existing annotations:

- Shared InterPro/Pfam domain assignments
- Name/description similarity
- Same gene family indicators

For this search:

```
Kept 6579 entries after filtering
Filtered out 508663 entries (phase0)
Filtered out 16721 entries (phase1)
Filtered out 25043 entries (phase2)
Filtered out 4207 entries (bias)     # in sw_finds_biased.txt instead
```

Phase0 drops pairs with the same name (per first 11 chars), toxins, uncharacterised and putative. The rationale is that these finds are likely to be of low interest.
Phase1 drops pairs with shared meaningful words in the description (i.e. stop words excluded)
Phase2 drops pairs matching on any of InterPro, PANTHER, PRINTS, Pfam etc, also -!- SIMILARITY. It's an attempt to find where the annotation indicates its actually known. 

Full details of these filters are in the source code.
Filter statistics were logged to `sw_results/filter_reasons.txt`.

Additionally the filtering does alignments and counts amino acids matches, building a composition of the matches used. This composition is then used to mark some sequence pairs as biased. This is hoped to be more sensitive than just checking composition, as it shows the residues the alignment actually relied on. 

**Outputs:**
- `sw_results/sw_finds.txt` — **6,579 candidate finds** (scores 110-4,089)
- `sw_results/biased_alignment.txt` — **4,207 compositionally biased finds** (flagged separately)

### 5. Manual Curation

The reduced set was manually reviewed for biological significance, focusing on:

- Score range 140-300 (twilight zone — most likely to contain overlooked homology)
- Clumping patterns in the tree suggesting functional groupings  
- Conserved rare residues (C, W, F, M) within compositionally biased backgrounds

Many similarities where the pairs of protein names suggested the similarity was not likely to be new or specially interesting were skipped over. 

**LLM-assisted evaluation:** Claude and Gemini were then used to check whether relationships were already documented and to assess biological plausibility. Both models showed systematic skepticism toward compositionally biased alignments (coiled-coils, low-complexity regions), often dismissing them as "convergent evolution" or "shared evolutionary pressure." Manual override was applied where extended alignment length and rare-residue conservation patterns supported genuine homology.

## Reproducing This Analysis

### Requirements

- macOS with Apple Silicon (M1, M2, or M4)
- Python ≥3.9
- Clang (included with Xcode Command Line Tools)

### Installation

```bash
git clone https://github.com/JamesCrook/seqquest
cd seqquest
pip install -e .
```

This installs dependencies including PyObjC for Metal acceleration.

### Running the Pipeline

```bash
# 1. Download UniProt Swiss-Prot
#    (manual download from uniprot.org or use provided script)

# 2. All-on-all Smith-Waterman (~30 hours)
python py/sw_search.py

# 3. Build maximal scoring tree
python py/tree_builder.py

# 4. Apply filters
python py/filter_twilight.py
```

See `GETTING_STARTED.md` for full details.

## Browsing the Findings

### Online

This is for the files already in the findings folder

* **GitHub:** [SeqQuest Findings](github.com/jamescrook/seqquest/findings)
* **Dynamic:** [Online Browser](www.catalase.com/seqquest/match_explorer.html)

### Local

If reproducing the results, you can read the results files you make in a text editor. To instead use the dynamic browser on these results, overwrite the files in /findings/ with them. Then browse to 'http://127.0.0.1:8006/match_explorer.html' starting the web server first with:

```
python py/web_server.py
```

## Release Contents

```
seqquest/
├── GETTING_STARTED.md              # Reproduction instructions
├── pyproject.toml                  # Dependencies
│
├── findings/
│   ├── METHODS.md                  # This file
│   ├── filter_reasons.txt          # Counts for rules used to filter
│   ├── proposed_updates.md         # Specific annotation corrections
│   ├── sw_finds_biased.txt         # 4,207 compositionally biased finds
│   ├── sw_finds_distilled.txt      # 22 curated finds
│   └── sw_finds_standard.txt       # 6,579 filtered finds (browsable)
│
├── static/
│   ├── sequest.html                # About the site
│   ├── match_explorer.html         # Finds/Alignments viewer
│   ├── fast-align.html             # Standalone WASM aligner
│   └── fetch-seq.html              # Standalone UniProt fetcher
│
└── py/
    ├── sw_search.py                # Main search tool
    ├── tree_builder.py             # MST construction  
    └── filter_twilight.py          # Annotation-based filtering
```

**Not included:** Raw `sw_results.csv` (3.8 GB) and `sw_tree.txt` (0.8 GB). These are regenerable via the pipeline above.

## Proposed Annotation Updates

| Accession | Current | Proposed | Evidence |
|-----------|---------|----------|----------|
| P85828 | Membrane protein | Secreted neuropeptide precursor | Alignment with E2ADG2; "transmembrane" region aligns to signal peptide |
| DSC2_SCHPO | DSC complex subunit (no structure) | Add rhomboid domain (IPR022764) | Alignment with Q9LET3 |
| VPS_HAEIN | Orphan prophage protein | Add pectin lyase fold (IPR011050) | Alignment with K9L8K6 |
| C16orf89 | UPF0764 / uncharacterized | Related to UTY C-terminal domain | Alignment with Q6B4Z3 |
| ECMA_DICDI | "Cys-rich repeats" | Chitin-binding Peritrophin-A domains (CBM14) | Alignment + PROSITE PS50940 match |

See `findings/proposed_updates.md` for full details and justifications.

## Citation

> James Crook. SeqQuest Protein Homology Findings, v0.1. Zenodo. [DOI]

## Contact

email: james.k.crook@gmail.com
