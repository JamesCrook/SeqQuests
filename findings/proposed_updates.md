# Proposed Annotation Updates
### *Method*

See [METHODS.md](./METHODS.md) in this repo to reproduce the steps.

* Sensitive Smith-Waterman all-on-all comparison of Uniprot ~570,000 proteins, UniProt Swiss-Prot 2025-04, downloaded 27-Oct-2025. 
* Maximal scoring tree to cluster - to find links between families/clusters
* Automatic simple removal of relations clearly already known, based on the names and the annotations. I also removed uncharacterised proteins.

Reduces to 6,579 'finds', scoring from 4,089 down to 110. These will still have known similarities in them. The high scores are well known, lowest scores are too tenuous to be useful, and scores of most interest between 140 and 300. This also produced a list of 4,207 finds with biased sequences. 

* Next sift twilight finds manually, with a web-based browsing interface, looking for clumping in the alignment, biological insight and connections that seem prima facie less likely to be well known.

In this stage I use AI assistance to find out more about the relationship, not with an automated pipeline, but by cutting and pasting promising pairs into Claude and/or Gemini for comment on the similarity, and then discussion. Both engines are very dismissive of 'coiled coil' similarities as 'just indicating shared evolutionary pressure, and not shared origin.'. Sometimes I have to highlight islands of matching to get AI to engage with the similarity. The AI does provide a more sensitive check of 'is this already known?' than does looking for name/pfam/eggNOG etc matches in the datafiles, and the AI feedback helped to refine my automated 'is it already known?' heuristics.

The heuristics for removing 'is it already known?' were to remove the bulk of well known and uninformative finds - not a tool with surgical precision. Some known limitations: it does not scan alternate names to see if alternate names match; it does not remove matches that are actually alternative products; it does not suppress matches with low scores that have no redeeming features such as islands of matching. 

The AI was not applied to all 6,579 of the finds, just to selected ones that I wanted to look at further. I for example skipped many pairs, such as Evasins, that clearly are known homologs, but where the heuristic for marking finds as almost certainly known already didn't see the name similarity. 

AI also gave background and suggested text for updates, based on the sequence files and similarities found. In this document I have provided 'Checks:' sections to link to referenceable URLs where the proposed updates go beyond noting the similarity. It isn't yet safe to rely on the AIs suggestions, despite the fact that the AI helps considerably in finding relevant information. 

## The Proposed Updates

The proposed updates are proposed based on sequence homology, reading of the existing protein data files and comments/feedback from LLMs. That LLM feedback has mostly been to say that the similarities are known or implicit in the data files. The ones chosen for presentation here by me are all ones where the LLM did not think the similarity had already been captured in the annotations - e.g. by shared family name.

The proposed updates are based on sequence homology, not labwork.

The file [gemini_comments.md](./gemini_comments.md) contains comments made by Gemini (AI) that while generally helpful should also be treated with some caution.

## Summary of Results

* 10 Data file updates proposed, based on homology
*  8 Data file updates proposed, based on homology, with the strong sequence bias similarities.

In this file I also placed at the end:
* 3 additional twilight zone similarities that highlight strengths/weaknesses of the method.

| Found similarity |
| --- |
| Honeybee Prohormone / ITG-like peptides |
| Fungal Biosynthesis and Transporter |
| Histone demethylase and a UPF |
| Pectin Lyase-like |
| Cyclin-Y |
| Rhomboid Planty/Yeast Ortholog |
| Two GPI proteins |
| Likely Transposon annotation |
| Concrete MLO/Dicer connection |
| Vps13 Family Homologs |
| Cell Wall Binding Domain (CBD) in two Lactococcus phage proteins |
| Phosphatase related similarity |
| Flocculin and Glucoamylase |
| Starmaker and Otolith |
| Fungal Adhesion proteins |
| Extended Trichohyalin/plectin homology |
| Two Shematrin proteins |
| Chitin-binding domains |
| Metallothionein in two unicellular eukaryotes |
| Metallothionein in rabbit and rice! |
| Two fungal biosynthetic proteins |

If browsing the distilled results in the [online browser](https://www.catalase.com/seqquests/match_explorer.html), you will see that there are 22 sequence pairs. The first two are for the same datafile, the honeybee prohormone.

# Similarities and Proposed Updates

In the folowing s(654) and similar are the sequence similarity score, using PAM250 matrix, -10 indel score. 

### Honeybee Prohormone / ITG-like peptides
```
P85828-E2ADG2 s(654) Length: 314/205
 Prohormone-3; Apis mellifera (Honeybee).
 ITG-like peptide {ECO:0000303|PubMed:25641051}; Camponotus floridanus (Florida carpenter ant).

    89  MYTCVALTVVALVSTMHFGVEAWGGLFNRFSPEMLSNLGYGSHGDHISKSGLYQRPLSTSYGYSYDSLEE
        |....|.|.|....|...|||||||||||||||||||||||.||......||.|......||......||
     1  MRVYAAITLVLVANTAYIGVEAWGGLFNRFSPEMLSNLGYGGHGSYMNRPGLLQEGYDGIYGEGAEPTEE

   159  VIPCYERKCTLNEHCCPGSICMNVDGDVGHCVFELGQKQGELCRNDNDCETGLMCAEVAGSETRSCQVPI
          |||||||..|.||||||||||..|..|.||...|..||||||.|.||||||||||..|      .   
    71  --PCYERKCMYNDHCCPGSICMNFNGVTGTCVSDFGMTQGELCRRDSDCETGLMCAEMSG------H---

   229  TSNKLYNEECNVSGECDISRGLCCQLQRRHRQTPRKVCSYFKDPLVCIGPVATDQIKSIVQYTSGEKRIT
               |||..|.||||||||||||||||||.|||||||||||||||||||||||||..||||||||||
   130  -------EECAMSSECDISRGLCCQLQRRHRQAPRKVCSYFKDPLVCIGPVATDQIKSVIQYTSGEKRIT

   299  GQGNRIFKR
        |||||.|||
   193  GQGNRLFKR
```

Proposal:
```
P85828
DE   RecName: Full=ITG-like peptide;
DE   AltName: Full=Prohormone-3;
DE   Contains:
DE     RecName: Full=Brain peptide ITGQGNRIF;
DE   Flags: Precursor;

CC   -!- SUBCELLULAR LOCATION: Secreted {ECO:0000250|UniProtKB:E2ADG2}.
CC   -!- SEQUENCE CAUTION: The sequence 1-88 may be artifactual. An 
CC       alternative translation initiation at Met-84 is supported by 
CC       RefSeq XP_001122204 and at Met-89 by sequence similarity to E2ADG2.
CC       {ECO:0000305}.
CC   -!- SIMILARITY: Belongs to the ITG-like peptide family.
CC       {ECO:0000305}.

Remove:
FT   SIGNAL          1..19        (in artifactual region)
FT   TRANSMEM        90..112      (this is actually signal peptide)
CC   -!- SUBCELLULAR LOCATION: Membrane...  (wrong)

Add:
FT   SIGNAL          89..103
FT                   /evidence="ECO:0000250|UniProtKB:E2ADG2"
FT   PROPEP          104..294
FT                   /evidence="ECO:0000250|UniProtKB:E2ADG2"
```

Calculation of transmembrane-ness should probably be redone with the shorter sequence.

Checks:
* https://www.ncbi.nlm.nih.gov/protein/XP_001122204.2 - for the NCBI version

### Fungal Biosynthesis and Transporter
```
Q2HEW6-A0A345BJN8 s(250) Length: 409/919
 Chaetoglobosin A biosynthesis cluster protein C {ECO:0000303|PubMed:33622536}; Chaetomium globosum (strain ATCC 6205 / CBS 148.51 / DSM 1962 / NBRC 6347 / NRRL 1970) (Soil fungus).
 MFS-type transporter clz9 {ECO:0000303|PubMed:28605916}; Cochliobolus lunatus (Filamentous fungus) (Curvularia lunata).

    26  RAAARQYNVPEATIRHRCTGRSARRDLPANSRKLTDLEERTIVQYILELDARAFPPRLRGVEDMANHLLR
        |.||....|..||...||.|..||||...||.||...||..|..|||.||.|.|.|.......||..||.
   507  RRAAAIFEVSRATLHRRCDGKRARRDCQPNSKKLIQQEEEVILKYILDLDTRGFLPTYAAERGMADKLLS

    96  ERDAPPVGKLWAHNFVKRQPQLRTRRTRRYDYQRA
        .|...|||..|..||||............|....|
   577  TRGGSPVGRDWPRNFVKHKAKYSILDEDVYSFDEA
```

Proposal:
```
A0A345BJN8
FT   DOMAIN          532..601
FT                   /note="HTH CENPB-type"
FT                   /evidence="ECO:0000250|UniProtKB:Q2HEW6"
CC -!- SIMILARITY: Region 507-610 shows similarity to Q2HEW6, encompassing 
CC     the HTH CENPB-type DNA-binding domain. Together with the C-terminal 
CC     DDE domain (641-809), this suggests a complete pogo-like transposase 
CC     architecture. {ECO:0000250|UniProtKB:Q2HEW6}.
```

Checks:
https://www.ebi.ac.uk/interpro/entry/InterPro/IPR004875/protein/UniProt/?search=lunatus#table - shows A0A345BJN8 has DDE domain 641-809 which is already noted.

A scan in PROSITE gives:
```
532 - 601:  score = 7.686   [warning: hit with a low confidence level (-1)]
DCQPNSKKLIQQEEEVILKYILDLDTRGFLPTYAAERGMADKLLSTRG-GSPVGRDWPRN
FVKHKAKYSIL

Predicted features:
DOMAIN      532 601 /note="HTH CENPB-type " [condition: none]   
DNA_BIND    565 594 /note="H-T-H motif" [condition: none]
```

N.B. This arrangement is like the arrangement in POGZ_HUMAN

### Histone demethylase and a UPF
```
Q6UX73-Q6B4Z3 s(247) Length: 402/1079
 UPF0764 protein C16orf89; Homo sapiens (Human).
 Histone demethylase UTY; Pan troglodytes (Chimpanzee).

   325  QAGVQWRNLGSLQPLPPGFKQFSCLILPSSWDYRSVPPYLANFYIFLVETGFHHVAHAGLELLISRDPPT
        .||.||..|.||||.|||||.||.|.||.||.||..|....||.|| ||||||||..|.||||.|.....
   995  RAGMQWCDLSSLQPPPPGFKRFSHLSLPNSWNYRHLPSCPTNFCIF-VETGFHHVGQAHLELLTSGGLLA

   395  SGSQSVGL
        |.|||.|.
  1064  SASQSAGI
```

```
Q6UX73
CC -!- SIMILARITY: Region 325-402 shows similarity to the C-terminal 
CC     domain of histone demethylase UTY. {ECO:0000250|UniProtKB:Q6B4Z3}.
```

### Pectin Lyase-like
```
K9L8K6-P44242 s(245) Length: 883/623
 Depolymerase, capsule K63-specific {ECO:0000305}; Klebsiella phage KP36 (Bacteriophage KP36).
 Mu-like prophage FluMu defective tail fiber protein; Haemophilus influenzae (strain ATCC 51907 / DSM 11121 / KW20 / Rd).

   184  LANPDGFRHIGRCKDIATLRTIEPVESRQVIEVLSYYNGLAQGGGTFWYDPNDSVTEDNGGSC-IVTNGG
        |...||...|||||..|.||||.|.|..|.|.|..||.|...|||.|..|..|..|.|.||.| .|.|.|
    88  LKQADGYKYIGRCKSVAELRTIRPTENGQRILVDAYYEGSTAGGGEFVADLQDLITPDDGGTCFVVPNNG

   253  KRWKRIIDGAVDVLSFGAKPDDISFDSAPHIQAALDNHDAVSLYGRSYYIGSPIYMPSRTVFDGMGGKLT
        .||||..........||. ..... |......|.||.......  ..|..... |..| ......|....
   158  GRWKRLFSSSLQDTDFGV-IGGVA-DDTTNLNAFLDALRTYKV--KGYFTSRH-YKTS-AALNIAGVDIE

   323  SIAPSTAGFMAGSIFAPGNYHPDFWEEVPKVAATTTLGSANITLADPNI
        .............|...|| |..| |.........|....|..|.....
   222  GVLAGYKNKHGTRITGNGN-HNIF-EQMGGELQHITYSLKNFALSGGIV
```

```
P44242
CC   -!- SIMILARITY: Region 88-270 shows similarity to phage 
CC       depolymerases containing a pectin lyase-like fold. 
CC       {ECO:0000250|UniProtKB:K9L8K6}.
```

### Cyclin-Y
```
Q4R871-Q96P64 s(507) Length: 360/663
 Cyclin-Y-like protein 2; Macaca fascicularis (Crab-eating macaque) (Cynomolgus monkey).
 Arf-GAP with GTPase, ANK repeat and PH domain-containing protein 4 {ECO:0000312|HGNC:HGNC:23459}; Homo sapiens (Human).

     1  MGNIMTCCVCPRASPELDQHQGSVCPCGSEIYKAAAGDMIAGVPVAAAVEPGEVTFEAGEGLHVHHICER
        ||||.||.|.|..|.|.||.||||||..||||.|.|||..||.|.||||.|.|||.|.||.||.||...|
     1  MGNILTCRVHPSVSLEFDQQQGSVCPSESEIYEAGAGDRMAGAPMAAAVQPAEVTVEVGEDLHMHHVRDR

    71  EMPEDIPLESNSSDHPKASTIFLRKSQTDVQEKRKSNYTKHVSTERFTQQYSSCSTIFLDDSTASQPHLT
        ||||  .||.|.|..|.|||||.|.|||||.|.|.||.|.||||.||.||||.|||||||||||.|..||
    71  EMPE--ALEFNPSANPEASTIFQRNSQTDVVEIRRSNCTNHVSTVRFSQQYSLCSTIFLDDSTAIQHYLT

   141  MTLKSVTLAIYYHIKQRDADRSLGIFDERLHPLTREEV
        ||..||||.|..||.||||||||.|.||.||......|
   139  MTIISVTLEIPHHITQRDADRSLSIPDEQLHSFAVSTV
```

Proposal:
```
Q4R871
CC   -!- SIMILARITY: Region 1-180 shows similarity to Arf-GAP domain-
CC       containing proteins. {ECO:0000250|UniProtKB:Q96P64}.

Q96P64
CC   -!- SIMILARITY: Region 1-178 shows similarity to Cyclin-Y-like 
CC       proteins. {ECO:0000250|UniProtKB:Q4R871}.
```

### Rhomboid Planty/Yeast Ortholog
```
Q9LET3-Q9UTK7 s(244) Length: 293/372
 Rhomboid-like protein 20 {ECO:0000303|PubMed:16895613}; Arabidopsis thaliana (Mouse-ear cress).
 DSC E3 ubiquitin ligase complex subunit 2; Schizosaccharomyces pombe (strain 972 / ATCC 24843) (Fission yeast).

     1  MNGGPSGFHNAPVTKAFVITSALFTVFFGIQGRSSKLGLSYQ-DIFEKFRIWKLIMSTFAFSSTPELMFG
        |........|...||....|.....|..|............. ........|......|......|....
     1  MSSANIVPSNMGITKFLLLTISTSSVVAGVFALKPFFHINFGLHLLSHYQYWRILLWQFIYWNSTEVFQA

    70  LYLLYYFRVFERQIGSNKYSVFILFSGTVSLLLE-VI-LLSLLKDTTANLLTSGPYGLIFASFIPFYLDI
        |...|..|..||..||.....|............ .. .|..|..........||..||||.....|...
    71  LFIIYQARDVERLLGSHRFASFCVYMFILGMFVTPIFSFLYSLLFKNLDYIQPGPTFLIFAILYQYYYIV

   138  PVSTRFRVFGVNFSDKSFIYLAGVQLLLSSWKRSIFPGICGIIAGSLYRLNILGIRKAKFP-EFVASFFS
        |.....|.|...|.||.........|..|...........|...|..|.|..|.......| .||....|
   141  PSTVFVRLFNIKFTDKFQMVIPMIGLAFSHFPSTFINAFLGWTMGMFYHLSLLPGTSWRLPIRFVKPALS
```

```
Q9UTK7
CC   -!- SIMILARITY: Region 1-210 shows similarity to rhomboid-like 
CC       proteins, suggesting an S54 peptidase domain. 
CC       {ECO:0000250|UniProtKB:Q9LET3}.
```

Checks:
* https://www.ebi.ac.uk/interpro/entry/InterPro/IPR022764/protein/UniProt/?search=Rhomboid%20like%20protein%2020%20thaliana#table - Q9LET3 has S54 Rhomboid domain 49-186
* https://www.ebi.ac.uk/interpro/entry/InterPro/IPR022764/protein/UniProt/?search=DSC%20E3#table - Two DSC E3 ubiquitin ligase complexes have identified S54 Rhomboid domains, but none from UniProt shown

This find and the checks above strongly suggests Q9UTK7 has S54 Rhomboid domain too.

### Two GPI proteins
```
Q8CHJ0-Q5AMR5 s(239) Length: 435/398
 GPI-anchor transamidase component PIGU {ECO:0000250|UniProtKB:Q9H490}; Cricetulus griseus (Chinese hamster) (Cricetulus barabensis griseus).
 GPI mannosyltransferase 1; Candida albicans (strain SC5314 / ATCC MYA-2876) (Yeast).


    71  YLFHFLIDYAELVFMITDALTAIALYFAIQDFNKVVFKKQKLLLELDQYAPD-VA-ELIRTPMEMR-YIP
        .....|..|.......|..| || |... ..|.|......|||......... .. .|........ ...
    47  FVYQGLSPYLRETYRYTPIL-AI-LLIP-DNFGKYWYHFGKLLFMVSDVITGLIILKLLSKQQQLSEKKK

   138  LKVALFYLLNPYTI-LSCVAKSTCAIN-NTLIAFFILTTIKGSVFLSAIFLALATYQTLYPVTLFAPGLL
        .......||||..| .|.......... ........|.. |..|.||||.|.|......||. ...|..|
   114  MILSSIWLLNPMVITISTRGSAESVLTVMIMLSLYYLLD-KDNVILSAIWLGLSIHFKIYPI-IYLPSIL

   206  YLLQRQYIP-V-KVKSKAF-WIFSWEYAMMYIGSLVVIVCLSFFLLSSWDFIPAVYGFILSVPDLTPNIG
        |.|..|..| . .|..... ......|.......|.|...| .||...|.||...|.......|...|..
   182  YYLSSQETPFLASVPGINLVNAKNLKYIIITLTTLAVVNYL-MFLKYGWEFIDNSYLYHVTRLDHRHNFS

   273  LF---WYFFAEMFEHFSLF-FVCV-FQINVFFYTVPLAIKL-KEHPIFFMFIQIAIISIFKSYPTVGDVA
        ..   .|......|....| .... |........|...... ||..|...|||......|....|.....
   251  VYNMVLYYKSALLEDSNGFDIEKIAFVPQLLLSAVIIPLIFAKEDLISSLFIQTFVFVAFNKVITSQYFI

   337  LYMAFFPVWNHLYRFLRNVFVLTCIIVVCSLLFPVLWHLWIYAGSANSNFFYAITLTFNVGQILLISDYF
        ....|.|........|... ..| .| .|.||.......|.|. .....|. ... ||..| ....|..|
   321  WFLIFLPHFLSKTKLLTTD-KIT-GI-SCLLLWIISQATWLYF-AYKLEFL-GEN-TFDNG-LMYSSVFF

   407  Y
        .
   384  F
```

Proposal:
```
Q5AMR5
CC   -!- SIMILARITY: Belongs to the glycosyltransferase GT-C superfamily, 
CC       PIGM family. Shows sequence similarity to PIGU family members 
CC       extending N-terminal to the PIG-M domain. {ECO:0000305}.
```

Evidence:
Alignment Q8CHJ0-Q5AMR5: score 239, regions 71-407/47-384
- Q8CHJ0 PIG-U domain: 11-394 (InterPro/Pfam PF06728)
- Q5AMR5 PIG-M domain: 129-394 (InterPro/Pfam PF05007)
- Both families belong to Pfam clan CL0111 (GT-C glycosyltransferases)
- Q5AMR5 region 47-128 shows additional homology N-terminal to annotated PIG-M domain

Checks:
* Hover on domain map to get sequence range for each domain:
* https://www.ebi.ac.uk/interpro/entry/pfam/PF06728/protein/UniProt/?search=griseus#table - Q8CHJ0 has PIG-U 11-394
* https://www.ebi.ac.uk/interpro/entry/pfam/PF05007/protein/UniProt/?search=albicans#table - Q5AMR5 has PIG-M 129-394

These above are the already annotated regions. 



### Likely Transposon annotation
```
O02751-Q32L59 s(220) Length: 592/351
 Craniofacial development protein 2; Bos taurus (Bovine).
 Transmembrane and coiled-coil domain-containing protein 5B; Bos taurus (Bovine).

   455  QRWRSSVQSAKTRPGADCGSDHKLLIAKFRLKLKIIPKTTRPFRVTNEEDATN-EEAKSVLKQNEKEKPE
        ||||||.|||||||||||||||.|||||||||||...|||||||......||. ....|.|........|
   203  QRWRSSIQSAKTRPGADCGSDHELLIAKFRLKLKKVGKTTRPFRCKAQNNATQIVKPGSTLVETIQSNME

   524  ANVPSTVSSV
        ..........
   273  KTIVKKQKRI
```

Proposal:
```
O02751
CC   -!- SIMILARITY: Region 455-533 shows similarity to Q32L59. 
CC       {ECO:0000250|UniProtKB:Q32L59}.

Q32L59
CC   -!- SIMILARITY: Region 203-282 shows similarity to O02751. 
CC       {ECO:0000250|UniProtKB:O02751}.
```

Claude (AI) flagged this as a possible transposon domain, but I haven't followed this up. The similarity is clear though.

### Concrete MLO/Dicer connection
```
P81785-Q9SP32 s(209) Length: 217/1909
 MLO-like protein; Linum usitatissimum (Flax) (Linum humile).
 Endoribonuclease Dicer homolog 1; Arabidopsis thaliana (Mouse-ear cress).

   157  DIVRASGLVPNRDTSATQTTE-LSKGKLMMADTCLPTEDLVGMVVTAAHSGKRFFVDSIRYD
        |.||||||.|.||.......| ||||||||||.|...|||.|..||||||||||.||||.||
  1172  DVVRASGLLPVRDAFEKEVEEDLSKGKLMMADGCMVAEDLIGKIVTAAHSGKRFYVDSICYD
```

Proposal:
```
P81785
CC   -!- SIMILARITY: Region 157-217 shows similarity to Q9SP32 that 
CC       includes the PAZ domain. {ECO:0000250|UniProtKB:Q9SP32}.

Q9SP32
CC   -!- SIMILARITY: Region 1172-1233 shows similarity to MLO-like 
CC       proteins. {ECO:0000250|UniProtKB:P81785}.
```


### Vps13 Family Homologs
```
Q74ZX0-Q2LD37 s(219) Length: 2887/5005
 Protein CSF1; Eremothecium gossypii (strain ATCC 10895 / CBS 109.51 / FGSC 9923 / NRRL Y-1056) (Yeast) (Ashbya gossypii).
 Bridge-like lipid transfer protein family member 1 {ECO:0000305}; Homo sapiens (Human).

   434  IDIRIAKESNITVRMAAYPTENGFENILHANLVDTTISTSVNHDTLLKAKSHDITVDFSYPYGWQDKAEW
        ........|...........|||........|......||....|||.|.........|||..|.....|
   408  VHVNVGAGSYLEINIPMTVEENGYTPAIKGQLLHVDATTSMQYRTLLEAEMLAFHINASYPRIWNMPQTW

   504  NFNVCSTQAEL-FVLRDHVYLISDLVTDFSGGEEVLYEQFRPFDYRFRWDIRGYSAYLNVNDANIINNPI
        ........|.. |........ .||..|.|.........|.|....|.............|..|.|....
   478  QCELEVYKATYHFIFAQKNFF-TDLIQDWSSDSPPDIFSFVPYTWNFKIMFHQFEMIWAANQHNWIDCST

   573  DFGENCYLSVHGDDAEITFSLPITSIIQKYVTVDFNIF--TPHFSLFLNAPPWHTFSELLHYKEIGRSKN
        ...||.||...|....|.||||.|..........|...  .....|||........|.....|.....|.
   547  KQQENVYLAACGETLNIDFSLPFTDFVPATCNTKFSLRGEDVDLHLFLPDCHPSKYSLFMLVKNCHPNKM

   641  FNIKG
        ....|
   617  IHDTG
```

Proposal:
```
Q74ZX0
CC   -!- SIMILARITY: Region 434-645 shows similarity to bridge-like 
CC       lipid transfer protein BLTP1. {ECO:0000250|UniProtKB:Q2LD37}.

Q2LD37
CC   -!- SIMILARITY: Region 408-621 shows similarity to CSF1 family 
CC       proteins. {ECO:0000250|UniProtKB:Q74ZX0}.
```

But see cupin-like fold in [gemini_comments.md](./gemini_comments.md)

### Cell Wall Binding Domain (CBD) in two Lactococcus phage proteins
```
P62693-Q38135 s(211) Length: 226/270
 Endolysin {ECO:0000255|HAMAP-Rule:MF_04110}; Lactococcus phage phivML3 (Lactococcus bacteriophage phi-vML3).
 N-acetylmuramoyl-L-alanine amidase; Lactococcus phage r1t (Bacteriophage r1t).

    27  WEQMYTIGWGHYGVTAGTTWTQAQADSQLEIDINNKYAPMVDAYVK-GKANQNEFDAL-VSLAYN-CGNV
        |...|..|...|...............|.|.......|.....|.. ..|........ ..|... .||.
    63  WDKVYLVGEPGYVAYGAGSPANERSPFQIELSHYSDPAKQRSSYINYINAVREQAKVFGIPLTLDGAGNG

    94  FVADGWAPFSHAYCASMIP-KYRNAGGQVLQGLVRRRQAELNLFNKPVSSNSNQNNQTGGMI-KM-YLII
        .....|.. .........| .|....|.....|............|...||........... .| ....
   133  IKTHKWVS-DNLWGDHQDPYSYLTRIGISKDQLAKDLANGIGGASKSNQSNNDDSTHAINYTPNMEEKEM

   161  G-LDNSGKAKHWYVSDGVSVRHVRTIRMLENYQNKWAKLNLPVDTMFIAEIEAEFG
        . |......|.||...|...|...|.|.|.||||.|.|..|||||||.||...|||
   202  TYLIFAKDTKRWYITNGIEIRYIKTGRVLGNYQNQWLKFKLPVDTMFQAEVDKEFG
```

Proposal:
```
P62693
CC   -!- SIMILARITY: Region 27-215 shows similarity to phage amidases.
CC       {ECO:0000250|UniProtKB:Q38135}.

Q38135
CC   -!- SIMILARITY: Region 63-257 shows similarity to phage endolysins,
CC       extending beyond the amidase domain.
CC       {ECO:0000250|UniProtKB:P62693}.
```

For 'cell wall binding domain' see Gemini's claims in [gemini_comments.md](./gemini_comments.md). Safest is to use the HMM methods, if available.


### Phosphatase related similarity
```
Q62784-Q69ZK0 s(203) Length: 939/1650
 Inositol polyphosphate-4-phosphatase type I A; Rattus norvegicus (Rat).
 Phosphatidylinositol 3,4,5-trisphosphate-dependent Rac exchanger 1 protein; Mus musculus (Mouse).

   665  LRQLYTIGLLAQFESLLSTYG--EELAMLEDMSLGIMDLRNVTFKVTQ-ATSN-ASSDMLPVITGNRDGF
        |.|....|.|....|||....  ||..||||.......|.||||...| .... |.......|.|.|...
  1359  LEQVAATGVLLHWQSLLAPASVKEERTMLEDIWVTLSELDNVTFSFKQLDENSVANTNVFYHIEGSRQAL

   731  NVRIPLPGPLFDSLPREIQSGMLLRVQPVLFNVGI-N-EQQTLAERFGDTSLQEVINVESLVRLNSYF-E
        .|...|.|..|..||.....|..||...|||.... . |............||..||..||.....|. .
  1429  KVVFYLDGFHFSRLPSRLEGGASLRLHTVLFTKALESVEGPPPPGNQAAEELQQEINAQSLEKVQQYYRK

   798  -Q-F---KEVLP-E-DCLP-R-S---RSQTCLPELLRFLGQNVHARK-NK-NVDI-LWQ-AAEVCRRLNG
         . |   ...|| . .... . .   |....|.||.|.....||... .. .... |.. ..|.|.||..
  1499  LRAFYLERSNLPTDAGATAVKIDQLIRPINALDELYRLMKTFVHPKAGAAGSLGAGLIPVSSELCYRLGA

   852  VRFTSCKSAKDRTAMSVTLEQCLILQHEHGMAPQVFTQALECMRSEGCRRENTMKNV
        ...|.|.....|...||.|||..||...||..|....||...||..|.|.|...||.
  1569  CQITMCGTGMQRSTLSVSLEQAAILARSHGLLPKCVMQATDIMRKQGPRVEILAKNL
```

Proposal:
```
Q69ZK0
CC   -!- SIMILARITY: Region 1359-1624 shows similarity to INPP4-type 
CC       inositol polyphosphate 4-phosphatases.
CC       {ECO:0000250|UniProtKB:Q62784}.
```

## Proteins with very biased sequence

### Flocculin and Glucoamylase
```
P04065-P08640 s(826) Length: 767/1367 [Compositional: T-Biased (42%)]
 Glucoamylase S1; Saccharomyces cerevisiae (Baker's yeast).
 Flocculation protein FLO11; Saccharomyces cerevisiae (strain ATCC 204508 / S288c) (Baker's yeast).

    22  FPTALVPRGSSSSNITSSGPSSTPFSSATESFSTGTTVTPSSSKYPGSKTETSVSSTTETTIVPTTTTTS
        .|........||...|...|..|..|..|.|..|.||...|........|....|..|.||.||||||||
   905  YPGSQTETSVSSTTETTIVPTKTTTSVTTPSTTTITTTVCSTGTNSAGETTSGCSPKTVTTTVPTTTTTS

    92  VITPSTTTITTTVCSTGTNSAGETTSGCSPKTITTTVPCSTSPSETASESTTTSPTTPVTTVVSTTVVTT
        |.|.||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
   975  VTTSSTTTITTTVCSTGTNSAGETTSGCSPKTITTTVPCSTSPSETASESTTTSPTTPVTTVVSTTVVTT

   162  EYSTSTKQGGEITTTFVTKNIPTTYLTTIAPTSSVTTVTNFTPTTITTTVCSTGTNSAGETTSGCSPKTV
        |||||||.||||||||||||||||||||||||.|||||||||||||||||||||||||||||||||||||
  1045  EYSTSTKPGGEITTTFVTKNIPTTYLTTIAPTPSVTTVTNFTPTTITTTVCSTGTNSAGETTSGCSPKTV

   232  TTTVPCSTGTGEYTTEATAPVTTAVTTTVVTTESSTGTNSAGKTTTSYTTKSVPTTYV
        ||||||||||||||||||..||||||||||||||||||||||||||.|||||||||||
  1115  TTTVPCSTGTGEYTTEATTLVTTAVTTTVVTTESSTGTNSAGKTTTGYTTKSVPTTYV
```

Proposal:
```
P04065
CC   -!- SIMILARITY: Region 22-289 shows similarity to the C-terminal 
CC       domain of flocculin FLO11. {ECO:0000250|UniProtKB:P08640}.
```

### Starmaker and Otolith
```
A0A060XQP6-A2VD23 s(575) Length: 628/613 [Compositional: D-Biased (40%)]
 Otolith matrix protein OMM-64 {ECO:0000305}; Oncorhynchus mykiss (Rainbow trout) (Salmo gairdneri).
 Protein starmaker; Danio rerio (Zebrafish) (Brachydanio rerio).

     1  MLSRLLIVPLIFALAGLAISAPVNDGTEADNDERAASLLVHLKGDKDGGGLTGSPDGVSAGTTDGTDSSK
        ||||...||||.|..|..|||||......||||.||............|. ....|| ...||||.||. 
     1  MLSRTVFVPLILAFVGVSISAPVSNNNGTDNDESAADQRHIFTVQFNVGT-PAPADG-DSVTTDGKDSA-

    71  ELAGGAVDSSPDTTDTPDASSSDIFPDTNNRDTSVETTGNPDDSDAPDAAESAGSQDTTDAADASEAVAE
        |......||| |||..|......   |..... .|.|.|...............|......||.......
    68  EKNEAPGDSS-DTTEKPGTTDGK---DSAEQH-GVTTDGKDEAEQHGVTTDGQDSAEKRGEADGAPDKPD

   141  TVDTYDIPDTDGADDREKVSTEVSTEDLDSAGVDKSPESDSTESPGSDSAESPGSDSAESPGSDSTESPG
        |....|..|.|...|.....|..|.|..|..................||.|||.. .....|.||...|.
   133  TQNGTDDTDSDQETDASHHKTGDSDENKDKPSAEDHTDGNHAGKDSTDSKESPDT-TDKPEGPDSDSAPD

   211  SDSTESPRSDSTDEVLTDVQADSADVTSDDMDEATETDKDDDKSDDKSDADAATDKDDSDEDKDTELDGK
        .||......|| |.. .|..|.... |..|.|. | .|||....|.|.|.| |.|||...||||...|.|
   202  GDSASAEKTDS-DHS-PDEDANKSS-TEADKDD-T-SDKDSSQTDEKHDSD-ASDKDEKHEDKDEKSDEK

   281  AHAEDTQTEEAADSDSKQGAADSDSDTDDDRPE-KDVKNDSDDSKDTTEDDKPDKDDKKNRDSADNSNDD
        ....|........||.......|..|......| ||...||.||.......|.|..|....||||....|
   266  DSSKDSEDKSQEKSDKSDDGSNSEADEQKESVESKDHDSDSQDSDSAEKKEKHDDKDQDSSDSADSKDSD

   350  SD-EMIQVPREELEQQEINLKEGGVIGSQEETVASDMEEGSDVGDQKPGPEDSIEEGSPVGRQDFKHPQD
        .| ..........|..|...|.................|.....|.....|....|.|...........|
   336  EDKDKDHSEQKDSEDHEHKEKHTKDKEEHKDSDEGKDDEDKSKSDEHDKDESESKEASKSDESEQEEKKD

   419  SEEEELEKEAKKEKELEEAEEERTLKTIESDSQEDSVDESEAEPDSNSKKDIGTSDAPEPQEDDSEEDTD
        .............................|||..||...|....||.|..|................|..
   406  DKSDSDNSSRDSHSDSDSDSHSDSDSDSHSDSHSDSDSDSHSDSDSDSDSDSDSDSDSDSDSNSRDKDEK

   489  DSMMKEPKDSDDAESD-KDDKDKNDMDKEDMDKDDMDKDDMDK-DDMDKDDVDKDASDSVDDQSESDAEP
        .....|..|.|...|| |..........||...|.......|| |..|...|....||...|....||.|
   476  KDKSSESRDEDSSDSDSKSNSESSETAEEDTNDDKDSSVEKDKTDSSDSASVEANDSDDEHDDDSKDATP

   557  GADSHTVVDEIDGEETMTPDSEEIMKSGEMDSVVEATEVPADILDQPDQQDDMTQGASQA
        ....||.............|...|........|...|.........||..||.|.|....
   546  SSEDHTAEKTDEDSHDVSDDDDDIDAHDDEAGVEHGTDEASKPHQEPDHHDDTTHGSDDG
```

```
A0A060XQP6
CC   -!- SIMILARITY: Belongs to the starmaker family. 
CC       {ECO:0000250|UniProtKB:A2VD23}.
```

### Fungal Adhesion proteins
```
Q6FPN0-Q5AL03 s(507) Length: 870/919 [Compositional: Diverse]
 Adhesin AWP1 {ECO:0000303|PubMed:34962966}; Candida glabrata (strain ATCC 2001 / BCRC 20586 / JCM 3761 / NBRC 0622 / NRRL Y-65 / CBS 138) (Yeast) (Nakaseomyces glabratus).
 Hyphally regulated cell wall protein 1; Candida albicans (strain SC5314 / ATCC MYA-2876) (Yeast).

     6  IFAFFIKATLVLSLDILTP-TTLTGDQTFNEDVSVVSSLTLND-GSQ-YLFNNLLQIAPSSASVTANALA
        ||.......|...|...|. ....|.|.|..||.|.|..|... |.. ..|...|...............
     8  IFTILLTLNLSAALEVVTSRIDRGGIQGFHGDVKVHSGATWAILGTTLCSFFGGLEVEKGASLFIKSDNG

    73  AVSVFTFSLPPSSSLSNSGTLIISNSNTGPSTEQHIVITPNVMANTGTITLSLAHTNTDSSSTLIIDPVT
        .|......|............|..||....|.. ...|......|.|.|.|. ......|...|.....|
    78  PVLALNVALSTLVRPVINNGVISLNSKSSTSFS-NFDIGGSSFTNNGEIYLA-SSGLVKSTAYLYAREWT

   143  FYNTGTINYESIGSETNDPSLTGNILSIGSSGRTLQNLGTINLNAANSYYLLGTITENSGS-INVQKGFL
         .|.....|.. ...............|...|. . .|.......|......|..|..... |......|
   146  -NNGLIVAYQN-QKAAGNIAFGTAYQTITNNGQ-I-CLRHQDFVPATKIKGTGCVTADEDTWIKLGNTIL

   212  YVN-ALDF-IGNTINLSTTTALAFISPVSQVVRVRGVFFGNIIASVGSSG--TFSYNTQTGILTVTTNGV
        .|. ...| ...........|..............|...|......|...  .|.|...||||.......
   212  SVEPTHNFYLKDSKSSLIVHAVSSNQTFTVHGFGNGNKLGLTLPLTGNRDHFRFEYYPDTGILQLRAAAL

   278  YSY-DIGCGYNPALMS-GQQETLSFQGNLYDTFLVLVNQPIPSDLTCAAVSSSITPSSSVEPSSSVEPSS
        ..| .||.||...|.. .....|. ....||........|......|....|.....|............
   282  PQYFKIGKGYDSKLFRIVNSRGLK-NAVTYDGPVPNNEIPAVCLIPCTNGPSAPESESDLNTPTTSSIET

   346  SVEPSSSVEPSSSVEPSSSVEPSSSVEPSSSVEPSSSVEPSSSVEPSSSVEPSSSVEPSSSVEPSSSVEP
        |...|...|.|...|.||.|....|...||..|.|..|......| |||..........||....|| ..
   351  SSYSSAATESSVVSESSSAVDSLTSSSLSSKSESSDVVSSTTNIE-SSSTAIETTMNSESSTDAGSS-SI

   416  SSSVEPSSSVEPSSSVEPSSSVEPSSSVEPSSSVEPSSPAVPSSSAEPSSSVVPPITPIPSSSVVSASVF
        |.|...|.....||....|.|...||......|.| ......|.| |.||...........||.......
   419  SQSESSSTAITSSSETSSSESMSASSTTASNTSIE-TDSGIVSQS-ESSSNALSSTEQSITSSPGQSTIY

   486  DTSSTLPSSPTVPTSSVSPSSPTVPTSSVSPSSPTVPTSSESP-STLSTPSSSAAPSSFCPTCVSSGTPP
         ..||..|..|.................|..|...|||....| ||..|..........|.....|....
   487  -VNSTVTSTITSCDENKCTEDVVTIFTTVPCSTDCVPTTGDIPMSTSYTQRTVTSTITNCDEVSCSQDVV

   555  APSSSAVVPTSSAGGGNGGDNGQPGADGQPGAAGQPGAAGQPGAAGQPGAAGQPGAAGQPGAAGQPGAAG
        .........|..|........|.....|........|.........|.|.....|.....|.....|...
   556  TYTTNVPHTTVDATTTTTTSTGGDNSTGGNESGSNHGSGAGSNEGSQSGPNNGSGSGSEGGSNNGSGSGS

   625  QPGAAGQPGAAGQPGAAGQPGAGSGGGSEQPTPGAGAGSGSADGNQSGTSSGTGNGQAGSGQAGSG-QVG
        ..|.....|.....|.......|||.||. .|.|...||||..|...|...|.|.|.......||| ..|
   626  DSGSNNGSGSGSNNGSGSGSNNGSGSGSG-STEGSEGGSGSNEGSNHGSNEGSGSGSGSQTGSGSGSNNG

   694  SGQAGAGQAGSGQAGAGQAGSGQAGAGQAGLDNTASGQSEGGQASAMDGDQSGRGGQSNSGSLLQPNAQQ
        ||.......|||.......|| ..|...........|..||.......|...| .||. ||.........
   695  SGSGSQSGSGSGSQSGSESGS-NSGSNEGSNPGAGNGSNEGSGQGSGNGSEAG-SGQG-SGPNNGSGSGH

   764  GTGSGTGSDTGADQASGESPGQIGDAQPGSGTDQSSGRHSLAAEA-RTSQSHSLAADARTRSTTRQTSVI
        ..|||.||..|.....|...|.......||......|......|. .|.........|.|..|....||.
   762  NDGSGSGSNQGSNPGAGSGSGSESGSNAGSHSGSNEGAKTDSIEGFHTESKPGFNTGAHTDATVTGNSVA

   833  APGTAPGTAVVT
        .|.|.......|
   832  NPVTTSTESDTT
```

```
Q5AL03
CC   -!- SIMILARITY: Shows similarity to fungal adhesins including AWP1. 
CC       {ECO:0000250|UniProtKB:Q6FPN0}.
```

### Extended Trichohyalin/plectin homology
```
Q1RM03-P37709 s(442) Length: 499/1407 [Compositional: ER-Biased (83%)]
 Trichoplein keratin filament-binding protein; Danio rerio (Zebrafish) (Brachydanio rerio).
 Trichohyalin; Oryctolagus cuniculus (Rabbit).

    12  SRVRTLEQQLVRQ-REQEARLRRQWEQHSQYFREQDVRSSKQAQWSSRQSFHRSMSAFQRDRMREEKQRK
        ||.|..|.|..|| .|...|..|..|...|..|.|.......... .||.. ...........|.|....
   393  SRPRRQEEQSLRQDQERRQRQERERELEEQARRQQQWQAEEESER-RRQRL-SARPSLRERQLRAEERQE

    81  LEERRERLRTMLQEERDQLEAELRNIHPDRDTLARQLVEKTDALRSAREERRKNLAQELLRE-HWKQNNS
        .|.|.........|.|..|..........|...|.|| ...|.....||.||....|..... .|.....
   461  QEQRFREEEEQRRERRQELQFLEEEEQLQRRERAQQL-QEEDSFQEDRERRRRQQEQRPGQTWRWQLQEE

   150  QLRKVESELHKDHIVSQWQVQQQEKKQADERTQEEKQRFENEYERTRQEALERMRKEEENRKWEEKKRAE
        ..|.... |........ |....|..|...|.||.......| |....|..|..|..|..|...|.....
   530  AQRRRHT-LYAKPGQQE-QLREEEELQREKRRQEREREYREE-EKLQREEDEKRRRQERERQYRELEELR

   220  ELLKQMEELKLREQEAERLKQEQETLMSKRWELEKLEDERKMMEESRR-KTEFGRFLTRQYRAQLKRRAQ
        . ..|....||||.|......|.|.|.....|....|.|.....|... ..|..|.| |.....|.|..|
   597  Q-EEQLRDRKLREEEQLLQEREEERLRRQERERKLREEEQLLRQEEQELRQERERKL-REEEQLLRREEQ

   289  QVQEELEADRKILAALLEGELDEQRFHKARRERAVADAAWMKRVIEEQLQLERERE-AEFDILYREEAQR
        ....|.|........||. |..|.|.....|.|.........|..|..|..||||. .|...|.|.|.| 
   665  ELRQERERKLREEEQLLQ-EREEERLRRQERARKLREEEQLLRQEEQELRQERERKLREEEQLLRREEQ-

   358  VWEKREAEWEKERRARERLMREVLAGRQQQLQERMQENRLAREESLQRREELLQQLEQDRLTLRLEKEQQ
        ..  |. |.....|..|.|..|....|... |||.|..|..|.......|.|||..|..||. |.|.|..
   733  LL--RQ-ERDRKLREEEQLLQESEEERLRR-QEREQQLRRERDRKFREEEQLLQEREEERLR-RQERERK

   428  EGLRTARIQEIDNQVEQRRKEQWEQQQTLEQEEAQEREELRLQEEELRL-ETDRMIRQGFQERIHSRPR
        ........||.......|.................|.|.||.||.|..| |.....||..||....|.|
   798  LREEEQLLQEREEERLRRQERERKLREEEQLLQEREEERLRRQERERKLREEEQLLRQEEQELRQERAR
```

Proposal:
```
Q1RM03
CC   -!- SEQUENCE CAUTION: The annotated trichohyalin/plectin homology 
CC       domain (260-426) may extend across the full protein length 
CC       (12-490). {ECO:0000305}.
```

### Two Shematrin proteins
```
C0J7L8-P86949 s(421) Length: 406/336 [Compositional: G-Biased (47%)]
 Prisilkin-39 {ECO:0000312|EMBL:ACJ06766.1}; Pinctada fucata (Akoya pearl oyster) (Pinctada imbricata fucata).
 Shematrin-like protein 1; Pinctada maxima (Silver-lipped pearl oyster) (White-lipped pearl oyster).

    31  VAGATIGALASGGLGAGAGGFG-VGGFPVGVGAVGIPVAVGGGIPYGYGGYSGYGYGYPAGGYGGYSYGY
        |.||..||.|...||...|... |.|...|.|. |.....|...|.||.|....||||....| ||.|||
    86  VRGAAQGAAAASALGIASGVPSRVSGSSIGIGG-GRALVSGSATPIGYYGVPYGGYGYGVPSY-GYGYGY

   100  PTGGYGGYSYGYPTGGYGGY-SYGYPTGGYGGYSYGYPTGGYSGYSYGYPTGGYSGYSYGYPTGGYSGYS
        |  .| |.|||||..||||| .||||...|.| ...|.... .| ....||.| ....||...|.|.||.
   154  P--SY-GISYGYPGYGYGGYGGYGYPDVAYFG-GSTYGNLA-TG-AISSPTSG-VTIPYGGALGLYGGYG

   169  YGYPTGG-YSGYSYGYPTGGYSGYSY-GYPTG-GYSGYSYPTGGYSGYSYSSTPGYGYYGSGSGMGGMRS
         ||..|. |.||.||.|..|| ||.| .|... ||.||.|  |||.||.|......|....|....|..|
   217  -GYGLGSTYGGYGYGVPSYGY-GYGYPSYGISYGYPGYGY--GGYGGYGYPDVAHFGGSTYGNLATGAIS

   236  GYSYYSSPAPSYYSSGSMTPGYGYYSSGSGI-GGGM-GSGYSYYSSPA
        . . .|.....|........|||.|..|.|| |||. |||...||..|
   283  S-P-TSGVTIPYGGALGLYGGYGSYGYGPGIYGGGIYGSGGGIYSGGA
```

Proposal:
```
C0J7L8
CC   -!- SIMILARITY: Belongs to the shematrin family. 
CC       {ECO:0000250|UniProtKB:P86949}.
```

### Chitin-binding domains
```
P34504-Q54YG2 s(394) Length: 1463/1710 [Compositional: C-Biased (40%)]
 Chitin binding domain (ChtBD2) containing chtb-1 {ECO:0000312|WormBase:K04H4.2c}; Caenorhabditis elegans.
 Extracellular matrix protein A; Dictyostelium discoideum (Social amoeba).

   155  IVPKRMSSLSPSTSSPSNTENPCSKCPLGSACRNGNCIPLTTSNLCSDGSPPNNTCTRDPYSCPKGHFCT
        ............|.....|..|... ....||....|.|||..............||.|  ||.....|.
   354  VDDNNKCTIDACTKEGGVTHTPVNT-DDNNACTLDSCSPLTGVTHTPINCDDKKACTVD--SCSNSTGCV

   225  AQKVCC--PST-ALQSSIGCSTVCTIDESCPKGMTCQNNCCEERKLLRHPKVYRYATVEATNTIFEVDND
        .....|  ... ...........|...........|....|.......|..|........|.........
   421  NTPISCDDNNPCTVDTCDDSTGCCNTPINVDDNNPCTVDACTKSTGVTHTPVNVDDNNKCTIDACTKEGG

   292  IFDSAAIESLPTQKPQRLDEIMA-PGITPTPTRTTEPPKLRCLSSNTDEVNSLGGASSSSATCGGTNANC
        . ....... .......||.... .|.|.||..... .|.....|............|.......|...|
   491  V-THTPVNT-DDNNACTLDNCSPLTGVTHTPINCDD-KKACTVDSCSNSTGCVNTPISCDDNNPCTVDSC

   361  TSDED-CPTTFKCYQ-GCCKLAVCPRSLTAVKFTCKTQYHCRANEHCFFGGCCPK-TIELAVIKSQVLTM
        ..... |.|...... ..|....|..| |.|  | .|......|..|....|... ..............
   558  DDITGCCNTPINVDDNNPCTVDACTKS-TGV--T-HTPVNVDDNNKCTIDACTKEGGVTHTPVNTDDNNA

   428  SKDNEHTKETEKLIIGDCEVDTRVKKCDIDIICPEMSECVD-GICCKQ-PP-KAR-CGNGLMALSIPVHC
        .........|. ........|.. ..|..| .|.....||. ...... .| ... |.........||..
   624  CTLDSCSPSTG-VSHTPINCDDS-NPCTVD-SCSNSTGCVNTPVNVDDNNPCTVDACTKSTGVTHTPVNV

   494  SLSDDCPIASRCEYGKCCPFLSESADSTSDSVGETTPVIIKEEIISTATKVWKKVDKTSGVSINKNKCLS
        .....|.|.. |  .|...........................|..|......|...|.....|...|..
   691  DDNNKCTIDA-C--TKEGGVTHTPVNTDDNNACTIDSCSPSTGISHTPINCDDKKACTVDSCSNSTGCVN

   564  TQ-RCDLHTLCPPDFTC-SLSGKCCKLNIHCPDGTV-PETSCQSASNHDHCPSSSHKCTLLNKEHFACCY
        |. .||....|..| .| .|.| ||...|...|... ....|.......|.|..... .  ||.....|.
   758  TPISCDDNNPCTVD-SCDDLTG-CCNTPINVDDNNPCTIDACTKSTGVTHTPVNVDD-N--NKCTIDTCT

                                                              **************** 
   631  SPGLVVEGSVTAEVSSECPIGSVEVDPRFGTSCRYSLQCPSPYFCN-QRGQQASGLVCTFSSCSNSNPCS
        ..|.|....|.......|...|  ..|..|.| .....|.....|. .......|.|.|...|..||||.
   823  KEGGVTHTPVNTDDNNACTLDS--CSPSTGVS-HTPINCDDNNKCTVDSCSNSTGCVNTPINCDDSNPCT

        **********
   700  VGTCNNGYCCSSGSNSGSAIIDSDTNSTTNPSQPETTKTK-NNTKKSNSSKKHRKPKKKDVDPLSDPLLQ
        |..|||...|..................|.......|... ....|...................|....
   890  VDSCNNSTGCVNTPVNVDDNNPCTVDACTKSTGVTHTPVNVDDNNKCTIDACTKEGGVTHTPVNTDDNNA

   769  NDFPIGPPGYGFPEHLSNLDEVLIRAQGDGVSCAGGFQSSLICSVGSECPAGLHCDTAINLCCPLLLPLT
        ..........|......|.|..............|.......|.....|... .|..... ||.......
   960  CTIDACTKEGGVTHTPVNTDDNNACTLDSCSPSTGVSHTPINCDDSNPCTVD-SCSNSTG-CCNTPINVD

   839  DPKNPKKRK-TKRRKQKQDENEMEASANFPDSDPARFSSYSCGCM-GGGSSNC-V-GCQNAPQIITIPQN
        |........ ||................................. ......| . .|.....|...|.|
  1028  DNNPCTVDSCTKPTGVTHTPVNVDDNNKCTIDACTKEGGVTHTPVNTDDNNACTLDSCSPSTGISHAPIN

   905  SCPGGGYSVGGC--SSGYCATGYSCIQNQCCPSYNSAPRISVYTCPSGGNAVGACMSGRCA-SGYTCSNN
        ...........|  |.|.|.|......|..|..........|...|........|....|. .|......
  1098  CDDSNPCTIDSCNNSTGCCNTPINVDDNNPCTVDSCTKSGGVTHTPVNVDDNNKCTTDACTKEGGVTHTP

   972  VCCPQTTTTNPFVCPDGTQAAGGCVNGQCGTGYTCSNGLCCAGTSTTVKCLDGSDAVGACIPSCTGDGCG
        ..|..........|...|....... . |.....|....|...........|..|.....|..|.... |
  1168  ISCDDNNACTIDSCSNSTGCVNTPI-S-CDDRNPCTVDTCTKEKGCQHSPIDTDDSNKCTIDACSSTT-G

  1042  GVQVSYYCGSGYTCTTGNICCPINSCPNGGEVLGPTINGLCPTGYTVQGNLCCSATCTDGSTGLPSVNGV
        ....|..|.....||... |.....|.... . .......|..........||.......... ......
  1235  VTHTSINCDDNNACTFDS-CSNSTGCVSTP-I-SCDDKNPCTLDSCDKKTGCCNTPINVDDND-KCTTDS

  1112  CIDGYSLTN-GVCCPASVTCTDEISIGPCTGTGFNGGCPAGYACDSNQ-VNCCPVVRYTDESCQVGPAID
        |......|. ...|.....||................|.....|.... .|...............|...
  1301  CTKEGGVTHTPISCDDNNACTTDSCSKSTGCVNKPISCDDSNPCTVDSCSNSTGCCNTPINVDDNNPCTT

  1180  GLCPPGYVVVYIPNSPLITNGVNPGTCIDLQCTTGLCLTANQIGDC--DTATDAGTCPTGYTCFTNAGIC
        ..|.....|...|......|......|......|...........|  |.......|............|
  1371  DSCTKSGGVTHTPVNVDDNNKCTTDSCTKEGGITHTPISCDDNNPCTLDSCSPTTGCVNKPMNVDDNDAC

  1248  CSTTTFSRLRIGNSRQMAQKPNYGRPLHSYMPPR-FGGPSSSCSDGSLSS-GPCMNGL-C-GIGLEC-Q-
        ...|......|..........| ...|....|.. .......|.||.... ..|.... | .....| . 
  1441  TTDTCNKDGTITHTPINTDDNN-KCTLDACSPKTGVTHTPINCDDGNKCTINSCSPSVGCISTPVSCPKP

  1312  NGKCCSPSSNKPAG-L-LQSKCPSGDTAVSGCFPNGSC-GTGYECVSSLNLC
        ..||.........| . ....|.|.......| ..|.| .....|....|.|
  1510  KDKCSISQCDSAKGCIEVPMNCTSDKCNEASC-CDGVCTSKPISCPKPKNKC
```

```
Q54YG2
CC   -!- SIMILARITY: Region 354-1560 contains multiple chitin-binding 
CC       type 2 motifs similar to P34504. {ECO:0000250|UniProtKB:P34504}.
```

Gemini additionally cited PROSITE motif CHIT_BIND_II

Checks:
* https://prosite.expasy.org/PS50940 - CHIT_BIND_II
* https://prosite.expasy.org/PDOC50940 - Documentation for above

C-x(13,20)-C-x(5,6)-C-x(9,19)-C-x(10,14)-C-x(4,14)-C

I'm heistant about this particular PROSITE pattern as it seems to me most Cysteine rich proteins of any extent are going to contain motifs this non specific. Meanwhile the similarity between these two proteins seems worth noting, noticably stronger than can just be explained by Cysteine bias, see for example the region marked with *****.


## Below the fold

The last three similarities are intriguing but without further evidence do not warrant a datafile update. I found multiple intriguing Cysteine rich matches besides the two examples here below. Convergent evolution rather than common origin could explain them. The algorithm tends to score them highly because of the normal rarity of Cysteine. A follow up investigation specifically of Cysteine rich proteins could be worthwhile.

There is also a 'below the fold' fungal biosynthetic similarity that Gemini was excited about. This find suggests the algorithm is picking up something in the twilight zone that correlates with function, even when we can't confidently call it homology. The fungal similarity is below the threshold where on its own a note in the datafile is warranted. 


### Metallothionein in two unicellular eukaryotes
```
Q10357-O97388 s(194) Length: 297/107 [Compositional: C-Biased (59%)]
 Superoxide dismutase 1 copper chaperone; Schizosaccharomyces pombe (strain 972 / ATCC 24843) (Fission yeast).
 Metallothionein-1; Tetrahymena pyriformis.

   220  NEGSSCCSKKDSS---PSEKPSCCSQEKKSCCSSKKPSCCSQEKKGCCSTEKTSCCSQEK-KSCCTSEKP
        .....||....|.   .||...||...||.||......|.....| ||...|..||...| |.|||....
    12  ENAKPCCTDPNSGCCCVSETNNCCKSDKKECCTGTGEGCKCTGCK-CCEPAKSGCCCGDKAKACCTDPNS

   286  SCCSNGKSTVC
        .||...|...|
    81  GCCCSSKTNKC
```

Possibly worth a note 
```
Q10357
-!- SIMILARITY Contains a cysteine-rich metal-binding motif similar to metallothioneins. 
```

The cysteines in pairs, vicinal cysteines, indicate this is not just down to composition bias.

### Metallothionein in rabbit and rice!
```
  P80292-Q67UU9 s(195) Length: 61/426 [Compositional: C-Rich (74%)]
 Metallothionein-2E; Oryctolagus cuniculus (Rabbit).
 Guanine nucleotide-binding protein subunit gamma 4 {ECO:0000305}; Oryza sativa subsp. japonica (Rice).

     3  PNCSCATRDSCACA-SSCKCKECKCTSCKKSCCSCCPAGCTKCA-QGCICKG-ALDKCSC
        ..|.|.....|.|. .||.||.|.|.||....|.|...||..|. ..|.|.| .|..|.|
   214  SQCNCSSPNCCTCTLPSCSCKGCACPSCGCNGCGCPSCGCNGCGCPSCGCNGCGLPSCGC
```

Like the previous find, just possibly worth a note 

```
Q67UU9
-!- NOTE 214-273 Similar composition bias to P80292 Metallothionein
```

The similarity is weak and is largely down to composition.

### Two fungal biosynthetic proteins
```
A0A7L9EYL3-S8B3I8 s(206) Length: 162/176
 Epoxidase xenD {ECO:0000303|PubMed:34900544}; Xenoacremonium sinensis (Endophyte fungus).
 Oxaleimides biosynthesis cluster protein N {ECO:0000303|PubMed:28365998}; Penicillium oxalicum (strain 114-2 / CGMCC 5302) (Penicillium decumbens).

                               H       H                                                 
     7  SIRLLRLLPALSSTSVLMFALDEHLIFGTWMHP-TLRER-ANTTLP-PWWTKGGLRWRWVIIIGYPL-TY
        ....||..|....|..|...|.......|...| |.... ...... ..|........|...|...| |.
    14  ALKVLRVTPLITTTILLVNRLAQYFALSTFLPPHTSPKKIDHVGAAFQHWLQTVVPRVWTGVISIVLFTR
                                         H       H      H

    73  LLGILNLLVARDELQATGSTLWYTTGLLFSIAHMAYVGTALNWIANIENGMPKGNVTYS-MGNWLKMNWT
        ...||||.|..|.|........|..||..|.||.......|..............|... ...|.|.|..
    84  VALILNLFVRPDDLAGSNARFLYGVGLFLSFAHLSVAPKMLKFEKRMMSPETVPHVAMELLAGWMKVNNI

   142  RALITDLPAWVCFITAALKVL
        |..|.|.|.||....|.|..|
   154  RFWIVDVPFWVVGVWATLEGL
```

Gemini considers these orthologs, based on near end-to-end correspondence, related function and 'conserved' Histidine spacing (shown with H's).

Likely needs input from a domain expert to decide whether a data file update is actually warranted. 
