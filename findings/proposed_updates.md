# Method

* Sensitive Smith-Waterman all-on-all comparison of Uniprot ~570,000 proteins
* Maximal scoring tree to cluster - to find links between families
* Automatic removal of relations clearly already known, based on the names and the annotations. I also removed uncharacterised proteins.

Reduces to 6,579 'finds', scoring from 4,089 down to 110. The high scores are well known, low scores well known, and scores of most interest between 140 and 300. This also produced a list of 4,207 finds with biased sequences. 

* Next sift twilight manually, with a web-based browsing interface, looking for clumping and biological insight.

In this stage I use AI assistance to find out more about the relationship, cutting and pasting promising pairs into Claude and/or Gemini for comment on the similarity. Both engines are very dismissive of 'coiled coil' similarities as 'just indicating shared evolutionary pressure, and not shared origin.'. Sometimes I have to highlight islands of matching to get AI to engage with the similarity. The AI does provide a more sensitive check of 'is this already known?' than merely looking for pfam matches in the datafiles, and it helped to refine the 'is it already known?' heuristics. For example Claude finds clues from the annotations that would alert someone familiar with the specific biochemistry of the related proteins to the connections.

AI also suggested text for updates, based on the sequence files and similarities found.

## Summary of Results

10 Data file updates proposed, based on homology
 6 Data file updates proposed, based on homology, with the strong sequence bias similarities.

In this file I also placed:
 3 additional twilight zone similarities.

# Similarities and Proposed Updates

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


P85828 is annotated as a single-pass membrane protein with a TRANSMEM region at 90-112.
E2ADG2 is annotated as a secreted protein.

It appears the Apis entry (P85828) contains an incorrect N-terminal extension. The region annotated as transmembrane (90-112) aligns with the Signal Peptide of the Camponotus entry. This suggests P85828 is also a secreted neuropeptide precursor, and the "membrane" classification is a computational artifact arising from the extended gene model. Another 
possibility is that the Apis entry is a polyprotein that is cleaved, and that the N terminal has some additional role.

??Or is Prohormone already indicating this is a known polyprotein??  

This same miss in the data file was also reported against Black cutworm moth. I've assembled the two together...

C0HKU1-P85828 s(590) Length: 217/314
 ITG-like peptide {ECO:0000303|PubMed:29466015}; Agrotis ipsilon (Black cutworm moth).
 Prohormone-3; Apis mellifera (Honeybee).
[ITG-like peptide {ECO:0000303|PubMed:25641051}; Camponotus floridanus (Florida carpenter ant).]

     1  MHRTMAVTAVLVLSAAG-AAHAWGGLFNRFSSDMLANLGYGRSPYRHYPYGQEPEEVYAEALEGNRLDDV cutworm moth
        |....|.|.|...|... ...||||||||||..||.|||||... .|............... |...|. 
    89  MYTCVALTVVALVSTMHFGVEAWGGLFNRFSPEMLSNLGYGSHG-DHISKSGLYQRPLSTSY-GYSYDS- honeybee
        |....|.|.|....|...|||||||||||||||||||||||.||......||.|......||......||
     1  MRVYAAITLVLVANTAYIGVEAWGGLFNRFSPEMLSNLGYGGHGSYMNRPGLLQEGYDGIYGEGAEPTEE carpenter ant

    70  IDEPGHCYSAPCTTNGDCCRGLLCLDTE-DGGRCLPAFAGRKLGEICNRENQCDAGLVCEEVVPGEMHVC
        ..|...||...||.|..||.|..|.... |.|.|.... |.|.||.|...|.|..||.|.||...|...|
   156  LEEVIPCYERKCTLNEHCCPGSICMNVDGDVGHCVFEL-GQKQGELCRNDNDCETGLMCAEVAGSETRSC
             |||||||..|.||||||||||..|..|.||... |.||||||.|.||||||||||..|          
       71  --PCYERKCMYNDHCCPGSICMNFNGVTGTCVSDF-GMTQGELCRRDSDCETGLMCAEMSG------

   139  RPPTAGRKQYNEDCNSSSECDVTRGLCCIMQRRHRQKPRKSCGYFKEPLVCIGPVATDQIREFVQHTAGE
        ..|....|.|||.||.|.|||..|||||..||||||.|||.|.|||.|||||||||||||...||.|.||
   225  QVPITSNKLYNEECNVSGECDISRGLCCQLQRRHRQTPRKVCSYFKDPLVCIGPVATDQIKSIVQYTSGE
        .          |||..|.||||||||||||||||||.|||||||||||||||||||||||||..||||||
    130 H----------EECAMSSECDISRGLCCQLQRRHRQAPRKVCSYFKDPLVCIGPVATDQIKSVIQYTSGE

   209  KRI
        |||
   295  KRITGQGNRIFKR
        |||||||||.|||
        KRITGQGNRLFKR


Q2HEW6-A0A345BJN8 s(250) Length: 409/919
 Chaetoglobosin A biosynthesis cluster protein C {ECO:0000303|PubMed:33622536}; Chaetomium globosum (strain ATCC 6205 / CBS 148.51 / DSM 1962 / NBRC 6347 / NRRL 1970) (Soil fungus).
 MFS-type transporter clz9 {ECO:0000303|PubMed:28605916}; Cochliobolus lunatus (Filamentous fungus) (Curvularia lunata).

    26  RAAARQYNVPEATIRHRCTGRSARRDLPANSRKLTDLEERTIVQYILELDARAFPPRLRGVEDMANHLLR
        |.||....|..||...||.|..||||...||.||...||..|..|||.||.|.|.|.......||..||.
   507  RRAAAIFEVSRATLHRRCDGKRARRDCQPNSKKLIQQEEEVILKYILDLDTRGFLPTYAAERGMADKLLS

    96  ERDAPPVGKLWAHNFVKRQPQLRTRRTRRYDYQRA
        .|...|||..|..||||............|....|
   577  TRGGSPVGRDWPRNFVKHKAKYSILDEDVYSFDEA


Clz9 has an unannotated HTH domain sitting between its MFS transporter and its DDE endonuclease domain. The Pfam/InterPro annotation missed it. ~507-610: HTH DNA-binding domain (NOT annotated). This makes Clz9 a complete pogo-like transposase (HTH + DDE) that has been fused to an MFS transporter - presumably a domestication event where a transposase got co-opted into a biosynthetic cluster and acquired a transporter domain.


Q6UX73-Q6B4Z3 s(247) Length: 402/1079
 UPF0764 protein C16orf89; Homo sapiens (Human).
 Histone demethylase UTY; Pan troglodytes (Chimpanzee).

   325  QAGVQWRNLGSLQPLPPGFKQFSCLILPSSWDYRSVPPYLANFYIFLVETGFHHVAHAGLELLISRDPPT
        .||.||..|.||||.|||||.||.|.||.||.||..|....||.|| ||||||||..|.||||.|.....
   995  RAGMQWCDLSSLQPPPPGFKRFSHLSLPNSWNYRHLPSCPTNFCIF-VETGFHHVGQAHLELLTSGGLLA

   395  SGSQSVGL
        |.|||.|.
  1064  SASQSAGI


C16orf89's DUF4735 domain = UTY C-terminal domain
This domain should be named and linked across both protein families
The UPF0764 family is not "uncharacterized" - it's related to UTX/UTY proteins


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

VPS_HAEIN needs:

InterPro: IPR011050 (Pectin lyase fold/virulence)
SUPFAM: SSF51126 (Pectin lyase-like)
Functional annotation: probable capsule depolymerase

This finding links an orphan prophage protein to a characterized enzymatic fold with clear functional implications.




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

This is known (GeneCards). GeneCards shows:

SIMAP paralogs for CCNYL2 Gene using alignment 
CCNYL1 CTGLF11P AGAP8 AGAP4 CCNYL3 CCNY FLJ00312 AGAP10
However, it seems Simap is no longer maintained.

The N-terminal sequence similarity is NOT characterized in the literature. The papers on Cyclin-Y discuss its conserved 
cyclin box domain but don't mention relationship to AGAP proteins. This N-terminal region (~180 amino acids) that shows high similarity is upstream of the annotated cyclin domain (which starts at residue 204 in CCYL2). This suggests a shared ancestral N-terminal module that predates the gene duplications - and could merit a datafile update.


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


What this suggests:

DSC2 - should have:
InterPro: IPR022764 (Peptidase S54 rhomboid domain)
SUPFAM: SSF144091 (Rhomboid-like)

Annotation correction needed:
DSC2_SCHPO should have rhomboid domain annotations added. Currently it's only annotated as "DSC complex subunit" without the structural classification.  This is an orthology call that unifies a plant "orphan" with a functionally characterized yeast protein.

The "inactive rhomboid" in Arabidopsis and the DSC complex member in yeast are orthologs - this connects plant stress response (heat acclimation, fungal defense) to yeast SREBP signaling.

The UBAC2 family spans plants and fungi with conserved:
* Rhomboid TM architecture
* C-terminal UBA domain
* Membrane localization

This is a known family connection, but misisng an annotation in this case.


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

A 2018 paper by Eisenhaber et al. discovered this relationship using a specialized tool called dissectHMMER. They found that a sequence module with 10 TMs in PIG-W is homologous to PIG-U, a transamidase subunit, and to mannosyltransferases PIG-B, PIG-M, PIG-V and PIG-Z. They concluded that this new membrane-embedded domain named "BindGPILA" functions as the unit for recognizing, binding and stabilizing the GPI lipid anchor.

However, note that this relationship is still not reflected in Pfam - PIGU (PF06728) and PIGM (PF05007) remain separate families. So there's still an annotation gap in the databases, even though the paper exists.


O02751-Q32L59 s(220) Length: 592/351
 Craniofacial development protein 2; Bos taurus (Bovine).
 Transmembrane and coiled-coil domain-containing protein 5B; Bos taurus (Bovine).

   455  QRWRSSVQSAKTRPGADCGSDHKLLIAKFRLKLKIIPKTTRPFRVTNEEDATN-EEAKSVLKQNEKEKPE
        ||||||.|||||||||||||||.|||||||||||...|||||||......||. ....|.|........|
   203  QRWRSSIQSAKTRPGADCGSDHELLIAKFRLKLKKVGKTTRPFRCKAQNNATQIVKPGSTLVETIQSNME

   524  ANVPSTVSSV
        ..........
   273  KTIVKKQKRI

Transposon domain. Misisng annotation. Check sheep. Likely just a recent transposon event.


P81785-Q9SP32 s(209) Length: 217/1909
 MLO-like protein; Linum usitatissimum (Flax) (Linum humile).
 Endoribonuclease Dicer homolog 1; Arabidopsis thaliana (Mouse-ear cress).

   157  DIVRASGLVPNRDTSATQTTE-LSKGKLMMADTCLPTEDLVGMVVTAAHSGKRFFVDSIRYD
        |.||||||.|.||.......| ||||||||||.|...|||.|..||||||||||.||||.||
  1172  DVVRASGLLPVRDAFEKEVEEDLSKGKLMMADGCMVAEDLIGKIVTAAHSGKRFYVDSICYD


This connects two major plant pathways (Immunity/Cell Death and RNA Silencing).
"The Plant Dicer PAZ domain contains a 'fossilized' MLO C-terminus."

The MLO C-terminus binds Calmodulin (calcium sensor). Does Dicer-Like 1 (DCL1) also bind Calmodulin at this spot? If so,  a mechanism for Calcium-regulated MicroRNA processing.

Gemini: While the functional crosstalk between MLO and Dicer is an emerging field, the specific structural "fossil" you’ve identified—a shared sequence between the MLO C-terminus and the Dicer PAZ-connector—appears to be a novel observation of a "Rosetta Stone" protein relationship.


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

Similarity known, but could be more clearly documented in the datafiles.

Q2LD37 is a high profile sequence, relevant to celiac disease: 
CC   -!- MISCELLANEOUS: KIAA1109 is mapped in the genomic region associated with
CC       susceptibility to celiac disease (CELIAC6).


Conserved "Barrel" Signature
The region aligned (approx. residues 570–640 in CSF1 and 550–620 in BLTP1) corresponds to a highly specific structural feature found in lipid transfer proteins: a beta-barrel or "cupin-like" fold used to shield hydrophobic lipids.

The Anchor: The alignment FSLPITS vs FSLPFTD is striking. The FSLP motif is hydrophobic and structurally rigid. In lipid transfer proteins, these hydrophobic residues often line the interior of the lipid-binding cavity.

Have effectively replicated with Smith-Waterman algorithm a discovery that required "heavy machinery" (HHpred and AlphaFold) for the scientific community to fully accept.

For years, these proteins sat in databases as "uncharacterized" because standard BLASTP searches failed to connect them reliably.
* **The Problem:** The sequence identity between Yeast CSF1 and Human BLTP1 is ~20–25%. This is the "Twilight Zone" of homology, where standard BLAST results are indistinguishable from random noise (high E-values).
* **The Result:** If you ran BLASTP in 2010, it likely returned "No significant similarity found" or buried the hit so deep in the list that no one noticed it.

### How did researchers find it?
The connection was only solidified very recently (around 2021–2022) using two methods that are far more sensitive than BLAST:

* **Method A: HHpred (Profile HMMs)**
    Instead of comparing *sequence to sequence* (like BLAST), researchers used **HHpred**. This tool compares "profiles" (statistical models of protein families).
    * They built a profile for the yeast protein (CSF1).
    * They built a profile for the human protein (BLTP1/KIAA1109).
    * They matched the *profiles*, which is much more sensitive than matching the letters directly.
    * *Reference:* Neuman et al. (2022) explicitly state they used HHpred to identify Csf1 and KIAA1109 as homologs of the Vps13 family.

* **Method B: AlphaFold (Structural Alignment)**
    The "smoking gun" was the release of AlphaFold. When the 3D structures were predicted, it became obvious they were identical.
    * Both proteins form a giant "taco shell" or "slide" shape (a long hydrophobic groove made of beta-sheets) used to transport lipids.
    * The sequence alignment you found corresponds to the **Repeating Beta Groove (RBG)** structural motif.


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


The similarity warrants a datafile update, both lack the annotation for the shared C-terminal Cell Wall Binding Domain (CBD).



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

Proposal:

CC   -!- SIMILARITY: The C-terminal part of the protein (residues ~800-1650)
CC       contains a domain homologous to the Type I inositol 3,4-bisphosphate
CC       4-phosphatase family (INPP4), but it lacks the critical cysteine
CC       residue required for phosphatase activity.
C. Add a Caution/Note on Activity
To prevent users from thinking it is an active phosphatase:



## Proteins with very biased sequence


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


Although this relationship is referenced in the bibliography of the linked P08640 entry (specifically Yamashita I., et al., J. Bacteriol. 169:2142-2149(1987), "Gene fusion is a possible mechanism underlying the evolution of STA1"), it is not currently described in the CC -!- SIMILARITY or CC -!- DOMAIN sections of P04065.

Could a note be added to P04065 clarifying that the C-terminal domain is homologous to the flocculin FLO11? This would greatly clarify the structural and evolutionary context of this enzyme for future users.

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

Currently, this entry is treated as a standalone otolith matrix protein. However, here is strong evidence that it is the ortholog of the well-characterized Zebrafish protein Starmaker (A2VD23).

Could a "Similarity" note be added, such as: "Belongs to the Starmaker family"?



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

Currently, these proteins are annotated as belonging to disparate families (Trimer_LpxA-like vs. Hyphal_reg_CWP). However, structural and architectural evidence suggests they are homologs within the broader fungal adhesin superfamily.

Could a "Similarity" note be added to Q6FPN0 indicating that it belongs to the fungal beta-helix adhesin superfamily, similar to the HYR1/IFF or Flo families?


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

Current Annotation: Currently, TCHP_DANRE contains a "Trichohyalin/plectin homology domain" annotated only at positions 260–426. The homology extends across the entire length of the TCHP protein (approx. AA 12–490) aligning to the central rod region of Trichohyalin (approx. AA 390–860 in Rabbit).

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

Annotation Update: PRSKL_PINFU belongs to the Shematrin/Glycine-rich SMP family


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

Current annotation identifies this protein as containing 66 "Cys-rich" repeats (FT REPEAT). However, sequence analysis indicates that these are not generic repeats, but are in fact Chitin-binding Peritrophin-A domains (CBM14 / ChtBD2).

PROSITE Motif Match The repeat units in ECMA_DICDI align with the PROSITE motif PS50940 (CHIT_BIND_II): C-x(13,20)-C-x(5,6)-C-x(9,19)-C-x(10,14)-C-x(4,14)-C

The "Cys-rich repeats" currently annotated in ECMA_DICDI (e.g., residues 43-70) fulfill this specific disulfide spacing requirement, including the diagnostic vicinal disulfide (CC) or closely spaced Cysteines at the C-terminus of the domain.

Biological Context: Dictyostelium stalk tubes are composed of cellulose and chitin. The presence of multiple tandem CBM14 domains in EcmA is consistent with its role as a structural "mortar" protein that binds these polysaccharide fibers, functionally analogous to the role of chtb-1 in the nematode cuticle.




## Cysteine rich ion-binding

Convergent evolution rather than common origin could explain these Cysteine rich matches. Algorithm tends to score them highly because of the normal rarity of C. 

Q10357-O97388 s(194) Length: 297/107 [Compositional: C-Biased (59%)]
 Superoxide dismutase 1 copper chaperone; Schizosaccharomyces pombe (strain 972 / ATCC 24843) (Fission yeast).
 Metallothionein-1; Tetrahymena pyriformis.

   220  NEGSSCCSKKDSS---PSEKPSCCSQEKKSCCSSKKPSCCSQEKKGCCSTEKTSCCSQEK-KSCCTSEKP
        .....||....|.   .||...||...||.||......|.....| ||...|..||...| |.|||....
    12  ENAKPCCTDPNSGCCCVSETNNCCKSDKKECCTGTGEGCKCTGCK-CCEPAKSGCCCGDKAKACCTDPNS

   286  SCCSNGKSTVC
        .||...|...|
    81  GCCCSSKTNKC

Possibly worth a note -!- SIMILARITY Contains a cysteine-rich metal-binding motif similar to metallothioneins. 
Though it's well known that Cadmium and Copper binding are related.

  P80292-Q67UU9 s(195) Length: 61/426 [Compositional: C-Rich (74%)]
 Metallothionein-2E; Oryctolagus cuniculus (Rabbit).
 Guanine nucleotide-binding protein subunit gamma 4 {ECO:0000305}; Oryza sativa subsp. japonica (Rice).

     3  PNCSCATRDSCACA-SSCKCKECKCTSCKKSCCSCCPAGCTKCA-QGCICKG-ALDKCSC
        ..|.|.....|.|. .||.||.|.|.||....|.|...||..|. ..|.|.| .|..|.|
   214  SQCNCSSPNCCTCTLPSCSCKGCACPSCGCNGCGCPSCGCNGCGCPSCGCNGCGLPSCGC

Also possibly worth a note -!- SIMILARITY .
(The 'enhanced tolerance to copper and cadmium' likely from the metallothionein-like fragment.) 


## Below the fold

These similarities are intriguing but without further evidence do not warrant a datafile update.


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

In twilight. Argument for is not clear, but could be orthologs based on near end-to-end correspondence and 'conserved' Histidine spacing.


Gemnini Says:

This match is far from the "twilight zone"—it is actually a high-value hit that connects two specific **secondary metabolite biosynthetic gene clusters (BGCs)**. While the sequence identity might look "weak" to a general algorithm, in the context of fungal natural products, this is a "smoking gun" for a shared enzymatic mechanism.

The biological story here is the **synthesis of complex, bioactive cyclic compounds (maleimides/alkaloids)** through a specialized oxidation pathway.

### 1. The Functional Connection: Epoxidation and Maleimides

* **A0A7L9EYL3 (xenD):** This is a key enzyme in the biosynthesis of **Xenovulene A**, a potent GABA receptor modulator. The "xenD" protein is a specialized epoxidase that modifies the backbone of the molecule.
* **S8B3I8 (Protein N):** This is part of the cluster that produces **Oxaleimides**. These are maleimide-containing secondary metabolites known for anti-tumor activity.

**The Story:** Both enzymes are likely **non-canonical epoxidases or cyclases** that work on hydrophobic, polyketide-derived substrates. The "weakness" in the alignment is likely due to the fact that they have evolved to recognize slightly different chemical structures (Xenovulene vs. Oxaleimide), but they maintain the same catalytic "engine."

---

### 2. The "H" Residue Clues (Histidine Coordination)

Notice the **H (Histidine)** residues highlighted in your alignment (residues 36, 40, and 56/61). In fungal BGC enzymes, these often indicate:

* **Non-Heme Iron Coordination:** Many of these biosynthetic oxidases (like the P450s or α-ketoglutarate-dependent dioxygenases) use histidines to hold a metal ion in place to activate oxygen.
* **Active Site Architecture:** The fact that the histidines align suggests that the **chemical reaction mechanism** is identical, even if the surrounding "pocket" (the L and V residues) has drifted to accommodate different-sized molecules.

---

### 3. Shared Membrane Architecture

Both proteins show a profile of a **small, multi-pass membrane protein** (roughly 160–180 amino acids).

* In fungal secondary metabolism, enzymes that handle very "greasy" (hydrophobic) molecules like polyketides are often membrane-bound.
* This alignment proves that **xenD** and **Oxaleimide Protein N** are structural homologs belonging to the same uncharacterized family of **membrane-associated biosynthetic oxidoreductases**.

---

### Why this is important

This homology allows you to "cross-annotate" these clusters:

1. **Reaction Prediction:** If the function of *xenD* is experimentally confirmed as an epoxidase, we can now confidently predict that *Protein N* performs a similar epoxidation or oxidative cyclization in the oxaleimide pathway.
2. **Cluster Discovery:** This motif could be used to find similar biosynthetic clusters in other fungi that are currently "silent" or unannotated.

### Summary Table

| Feature | xenD (Xenoacremonium) | Protein N (Penicillium) |
| --- | --- | --- |
| **Metabolite** | Xenovulene A | Oxaleimides |
| **Enzyme Type** | Epoxidase / Oxidoreductase | Oxidoreductase (likely Epoxidase) |
| **Substrate** | Diterpene-polyketide hybrid | Polyketide-derived maleimide |
| **Localization** | Membrane (ER/Golg) | Membrane (ER/Golg) |

**Conclusion:** This isn't a weak match; it's a **functional bridge** between two different classes of fungal drugs.


