#!/usr/bin/env python3
"""
Filter twilight zone protein comparisons by identifying unsurprising matches.

This program:
1. Parses a twilight comparison file
2. Uses fuzzy string matching (after stopword removal and stemming) to find shared terms
3. Optionally retrieves full UniProt records for deeper analysis
   (checking shared IDs in InterPro, PRINTS, Pfam, PANTHER, etc.)
4. Produces a filtered file and a reasons file for auditing
"""

import re
from collections import defaultdict
from typing import List, Optional, Set, Callable, Dict
import argparse

import sequences
from config import PROJECT_ROOT
from sw_align import assess_compositional_bias, align_local_swissprot


# =============================================================================
# Configuration
# =============================================================================

STOPWORDS = {
    'protein', 'domain', 'containing', 'subunit', 'member', 'regulator', 'fragment',
    'precursor', 'chain', 'component', 'factor', 'element', 'unit', 'specific',
    'probable', 'putative', 'possible', 'predicted', 'potential',
    'abnormal', 'disabled', 'uncharacterized', 'hypothetical', 'unknown',
    'small', 'large', 'short', 'long', 'terminal', 'internal',
    'type', 'like', 'related', 'homolog', 'ortholog', 'paralog',
    'family', 'superfamily', 'class',
}

MIN_STEM_LENGTH = 8

# Databases to check for exact ID matches (DB Name, Display Prefix, Strip Suffix Boolean)
ID_CHECK_DATABASES = [
    ('InterPro', 'InterPro', False),
    ('PANTHER', 'Panther', True),
    ('PRINTS', 'PRINTS', False),
    ('Pfam', 'Pfam', False),
    ('PROSITE', 'PROSITE', False),
    ('SMART', 'SMART', False),
    ('eggNOG', 'eggNOG', False),
    ('OrthoDB', 'OrthoDB', False)
]

# Databases to extract descriptive text from (3rd column of DR line)
TEXT_EXTRACT_DATABASES = {
    'InterPro', 'Pfam', 'SMART', 'PROSITE', 'SUPFAM', 'PRINTS' # Added PRINTS
}


# =============================================================================
# Text Processing Functions
# =============================================================================

def simple_stem(word: str) -> str:
    """Simple suffix-stripping stemmer."""
    word = word.lower()
    for suffix in ['ase', 'ases', 'ing', 'ed', 'es', 's', 'tion', 'sion', 'ness', 'ment']:
        if len(word) > len(suffix) + MIN_STEM_LENGTH and word.endswith(suffix):
            return word[:-len(suffix)]
    return word


def extract_meaningful_tokens(name: str, stopwords: Set[str], min_length: int = MIN_STEM_LENGTH) -> List[str]:
    """Extract meaningful tokens from a protein name."""
    name = re.sub(r';\s*[^;]+$', '', name)
    name = re.sub(r'\{[^}]*\}', '', name)
    name = re.sub(r'\([^)]*\)', '', name)
    
    tokens = re.findall(r'[a-zA-Z0-9]+', name.lower())
    
    meaningful_tokens = []
    for token in tokens:
        if token.isdigit() or len(token) < 3 or token in stopwords:
            continue
        stemmed = simple_stem(token)
        if len(stemmed) >= min_length:
            meaningful_tokens.append(stemmed)
    
    return meaningful_tokens


# =============================================================================
# Record Parsing
# =============================================================================

class TwilightEntry:
    """Represents a single twilight zone comparison."""
    
    def __init__(self, header_line: str, protein1_line: str, protein2_line: str):
        self.raw_header = header_line
        self.raw_protein1 = protein1_line
        self.raw_protein2 = protein2_line
        
        # e.g: P0C6Y0-P0C6X9 s(36047) Length: 7180/7176
        header_match = re.match(
            r'\s*([A-Z0-9]+)-([A-Z0-9]+)\s+s\((\d+)\)\s+Length:\s+(\d+)/(\d+)',
            header_line
        )
        if not header_match:
            raise ValueError(f"Could not parse header: {header_line}")
        
        self.score = int(header_match.group(3))
        self.id1, self.id2 = header_match.group(1), header_match.group(2)
        self.len1, self.len2 = int(header_match.group(4)), int(header_match.group(5))
        
        protein1_match = re.match(r'\s+(.+)', protein1_line)
        protein2_match = re.match(r'\s+(.+)', protein2_line)
        
        if not protein1_match or not protein2_match:
            raise ValueError("Could not parse protein lines")
        
        self.name1 = protein1_match.group(1).strip()
        self.name2 = protein2_match.group(1).strip()


def parse_twilight_file(filepath: str) -> List[TwilightEntry]:
    """Parse a twilight comparison file into structured entries."""
    entries = []
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line or line.startswith('found ') or line.startswith('===') or line.startswith('TOTAL SKIPPED'):
            i += 1
            continue
        
        if re.match(r'^[A-Z0-9]+-[A-Z0-9]+\s+s\(', line):
            if i + 2 < len(lines):
                try:
                    entries.append(TwilightEntry(line, lines[i+1], lines[i+2]))
                except ValueError as e:
                    print(f"Warning: {e}")
                i += 3
            else:
                i += 1
        else:
            i += 1
    
    return entries


# =============================================================================
# Record Feature Extraction (Consolidated)
# =============================================================================

def extract_xref_ids(record, db_name: str, strip_suffix: bool = False) -> Set[str]:
    """
    Extract IDs from cross-references for a given database.
    Example PRINTS: DR PRINTS; PR02045; F138DOMAIN. -> Returns 'PR02045'
    """
    ids = set()
    if hasattr(record, 'cross_references'):
        for xref in record.cross_references:
            if xref[0] == db_name and len(xref) >= 2:
                id_val = xref[1].split(':')[0] if strip_suffix else xref[1]
                ids.add(id_val)
    return ids


def extract_similarity_terms(record) -> Set[str]:
    """Extract meaningful terms from -!- SIMILARITY: lines."""
    terms = set()
    similarity_stopwords = STOPWORDS | {
        'proteins', 'subfamily', 'group', 'contains', 'domains', 'repeat', 'repeats',
        'region', 'regions', 'motif', 'motifs', 'sequence', 'sequences'
    }
    
    if not hasattr(record, 'comments'):
        return terms
        
    for comment in record.comments:
        if not comment.startswith('SIMILARITY:'):
            continue
            
        text = comment[11:].strip()
        text = re.sub(r'\{ECO:[^}]*\}', '', text)
        text = re.sub(r'^(Belongs|Member) to the\s+', '', text, flags=re.IGNORECASE)
        
        family_match = re.search(r'([\w\s/-]+?)\s+(?:super)?family', text, re.IGNORECASE)
        if family_match:
            family_name = family_match.group(1).strip().lower()
            if len(family_name) >= 3:
                terms.add(family_name)
        
        # Capture mixed-case identifiers (e.g., FliB, Met9, RecA) - keep original case
        mixed_case_terms = re.findall(r'\b[A-Za-z0-9]+[A-Z0-9][A-Za-z0-9]*\b', text)
        for term in mixed_case_terms:
            terms.add(term)
        
        for pattern, min_len in [(r'\b[\w]+(?:/[\w]+)+\b', 4), (r'\b\w+(?:-\w+)+\b', 6), (r'\b[A-Za-z]{3,}\b', 6)]:
            for term in re.findall(pattern, text):
                term = term.lower()
                if len(term) >= min_len and term not in similarity_stopwords:
                    terms.add(term)
    
    return terms


def extract_family_terms(record) -> Set[str]:
    """Extract family names from various record fields."""
    terms = set()
    
    if hasattr(record, 'description'):
        family_match = re.search(r'Family:\s*([\w-]+(?:\s+\d+)?)', record.description, re.IGNORECASE)
        if family_match:
            terms.add(family_match.group(1).lower())
    
    if hasattr(record, 'comments'):
        for comment in record.comments:
            belongs_match = re.search(r'Belongs to the\s+([\w-]+(?:\s+[\w-]+)?(?:\s+\d+)?)\s+family', 
                                     comment, re.IGNORECASE)
            if belongs_match:
                terms.add(belongs_match.group(1).lower())
    
    return terms


def extract_domain_terms(record) -> Set[str]:
    """
    Extract domain/repeat names from record annotations.
    Now includes PRINTS text (e.g., 'F138DOMAIN').
    """
    terms = set()
    
    if hasattr(record, 'cross_references'):
        for xref in record.cross_references:
            # Check configured databases
            if xref[0] in TEXT_EXTRACT_DATABASES and len(xref) >= 3:
                # xref[2] is usually the domain name/description
                domain_name = re.sub(r'[._]\d+$', '', xref[2].lower())
                if len(domain_name) >= 4: # Lowered limit slightly to catch short codes
                    terms.add(domain_name)
    
    if hasattr(record, 'features'):
        for feature in record.features:
            if hasattr(feature, 'type') and feature.type in ('DOMAIN', 'REPEAT', 'REGION'):
                if hasattr(feature, 'description'):
                    terms.update(re.findall(r'\b[a-z]{5,}\b', feature.description.lower()))
    
    return terms


MIN_NAME_TOKEN_LENGTH = 4      # Minimum length for individual name tokens
MIN_NAME_TOTAL_CHARS = 10     # Minimum total characters across all matching tokens


def extract_all_name_terms(record, stopwords: Set[str]) -> Set[str]:
    """Extract meaningful terms from all protein names (RecName + AltNames)."""
    terms = set()
    
    if not hasattr(record, 'description'):
        return terms
    
    desc = record.description
    
    # Extract all Full= values (covers RecName and AltName) and Short= values
    for match in re.finditer(r'(?:Full|Short)=([^;{]+)', desc):
        name = match.group(1).strip()
        tokens = extract_meaningful_tokens(name, stopwords, min_length=MIN_NAME_TOKEN_LENGTH)
        terms.update(tokens)
    
    return terms


# =============================================================================
# Filtering Logic
# =============================================================================

def check_common_ids(record1, record2, db_name: str, strip_suffix: bool = False) -> Optional[str]:
    """Check for common cross-reference IDs between two records."""
    ids1 = extract_xref_ids(record1, db_name, strip_suffix)
    ids2 = extract_xref_ids(record2, db_name, strip_suffix)
    common = ids1 & ids2
    return sorted(common)[0] if common else None


def check_sequential_panther_ids(record1, record2) -> Optional[str]:
    """Check if two records have sequential PANTHER family IDs."""
    ids1 = extract_xref_ids(record1, 'PANTHER', strip_suffix=True)
    ids2 = extract_xref_ids(record2, 'PANTHER', strip_suffix=True)
    
    for id1 in ids1:
        match1 = re.match(r'PTHR(\d+)', id1)
        if not match1:
            continue
        num1 = int(match1.group(1))
        
        for id2 in ids2:
            match2 = re.match(r'PTHR(\d+)', id2)
            if not match2:
                continue
            num2 = int(match2.group(1))
            
            if abs(num1 - num2) == 1:
                return f"{id1}/{id2}" if num1 < num2 else f"{id2}/{id1}"
    
    return None


def check_common_terms(record1, record2, extractor_func: Callable, min_length: int = 3) -> Optional[str]:
    """Find common terms between two records using a specific extractor."""
    terms1 = extractor_func(record1)
    terms2 = extractor_func(record2)
    common = terms1 & terms2
    
    if common:
        longest = max(common, key=len)
        if len(longest) >= min_length:
            return longest
    return None


def phase0_filter(entry: TwilightEntry) -> Optional[str]:
    """Phase 0: Superficial analysis."""
    name1_lower, name2_lower = entry.name1.lower(), entry.name2.lower()
    
    if 'toxin' in name1_lower and 'toxin' in name2_lower:
        return 'toxins'
    if 'uncharacterized' in name1_lower or 'uncharacterized' in name2_lower or \
       'putative' in name1_lower or 'putative' in name2_lower:
        return 'uncharacterized'
    if name1_lower[:11] == name2_lower[:11]:
        return 'similar names'
    return None


def phase1_filter(entry: TwilightEntry, stopwords: Set[str]) -> Optional[List[str]]:
    """Phase 1: String-based fuzzy matching."""
    tokens1 = extract_meaningful_tokens(entry.name1, stopwords)
    tokens2 = extract_meaningful_tokens(entry.name2, stopwords)
    common_stems = sorted(set(tokens1) & set(tokens2))
    return common_stems if common_stems else None


def phase2_filter(entry: TwilightEntry) -> Optional[str]:
    """Phase 2: Full record analysis."""
    try:
        r1 = sequences.get_protein(entry.id1)
        r2 = sequences.get_protein(entry.id2)
        
        if not r1 or not r2:
            return None

        # Check cross-reference IDs for all configured databases (PRINTS, Pfam, etc.)
        for db, prefix, strip in ID_CHECK_DATABASES:
            match = check_common_ids(r1.full, r2.full, db, strip)
            if match:
                return f"{prefix}: {match}"

        # Check sequential PANTHER IDs
        seq_match = check_sequential_panther_ids(r1.full, r2.full)
        if seq_match:
            return f"Panther: {seq_match}"

        # Check pooled name terms (RecName + AltNames)
        name_terms1 = extract_all_name_terms(r1.full, STOPWORDS)
        name_terms2 = extract_all_name_terms(r2.full, STOPWORDS)
        common_name_terms = name_terms1 & name_terms2
        if common_name_terms:
            total_chars = sum(len(t) for t in common_name_terms)
            if total_chars >= MIN_NAME_TOTAL_CHARS:
                return f"Name: {', '.join(sorted(common_name_terms))}"

        # Check term-based extractors
        for extractor, prefix in [(extract_similarity_terms, "-!- SIMILARITY: "),
                                   (extract_family_terms, "Family: "),
                                   (extract_domain_terms, "Domain: ")]:
            match = check_common_terms(r1.full, r2.full, extractor)
            if match:
                return f"{prefix}{match}"

    except Exception as e:
        print(f"Warning: Phase 2 failed for {entry.id1}-{entry.id2}: {e}")

    return None


def phase_compositional_bias(entry: TwilightEntry, threshold: float = 0.5) -> Optional[str]:
    """Phase for compositional bias detection."""
    try:
        r1 = sequences.get_protein(entry.id1)
        r2 = sequences.get_protein(entry.id2)
        
        result = align_local_swissprot(r1.full.sequence, r2.full.sequence,
                                       weights='PAM250', gap_extend=-10)
        if not result:
            return None
        
        bias_result = assess_compositional_bias(result['aligned_a'], result['aligned_b'])
        
        if bias_result['goodness'] < threshold:
            return f"Compositional: {bias_result['reason']}"
        
    except Exception as e:
        print(f"Warning: Compositional bias check failed for {entry.id1}-{entry.id2}: {e}")
    
    return None


# =============================================================================
# Output Writing
# =============================================================================

def write_filtered_output(output_file: str, kept_entries: List[TwilightEntry],
                          filtered_counts: Dict[str, int]):
    """Write the kept entries to the output file."""
    print(f"\nWriting {len(kept_entries)} kept entries to {output_file}...")
    with open(output_file, 'w') as f:
        f.write(f"Kept {len(kept_entries)} entries after filtering\n")
        for phase, count in filtered_counts.items():
            f.write(f"Filtered out {count} entries ({phase})\n")
        f.write("\n")
        for entry in kept_entries:
            f.write(entry.raw_header + '\n')
            f.write(entry.raw_protein1)
            f.write(entry.raw_protein2)


def write_bias_output(bias_output_file: str, bias_entries: List[tuple]):
    """Write bias output with reasons if requested."""
    if bias_output_file and bias_entries:
        print(f"Writing {len(bias_entries)} biased entries to {bias_output_file}...")
        with open(bias_output_file, 'w') as f:
            f.write(f"Composition-biased alignments: {len(bias_entries)} entries\n\n")
            for entry, reason in bias_entries:
                f.write(f"{entry.raw_header} [{reason}]\n")
                f.write(entry.raw_protein1)
                f.write(entry.raw_protein2)


def write_reasons_output(reasons_file: str, reason_counts: Dict[str, int],
                          filtered_counts: Dict[str, int], kept_count: int):
    """Write the filtering reasons to a file."""
    print(f"Writing reasons to {reasons_file}...")
    total_filtered = sum(filtered_counts.values())
    
    with open(reasons_file, 'w') as f:
        f.write("FILTERING REASONS (sorted by length - shortest first)\n")
        f.write("=" * 80 + "\n\n")

        for reason, count in sorted(reason_counts.items(), key=lambda x: (len(x[0]), x[0])):
            f.write(f"{reason:40s} : {count:6d}\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write(f"Total filtered: {total_filtered}\n")
        for phase, count in filtered_counts.items():
            f.write(f"  {phase}: {count}\n")
        f.write(f"Total kept: {kept_count}\n")


# =============================================================================
# Main Processing
# =============================================================================

def filter_twilight(input_file: str, output_file: str, reasons_file: str, 
                    bias_output_file: str = None, use_phase2: bool = False):
    """Main filtering function."""
    print(f"Parsing {input_file}...")
    entries = parse_twilight_file(input_file)
    print(f"Found {len(entries)} comparisons")
    if entries == 0:
        print("Nothing to do.")
        return
    
    filtered_counts = {'phase0': 0, 'phase1': 0, 'phase2': 0, 'bias': 0}
    kept_entries = []
    bias_entries = []
    reason_counts = defaultdict(int)
    
    print("Filtering...")
    for i, entry in enumerate(entries):
        if (i + 1) % 1000 == 0:
            print(f"  Processed {i + 1}/{len(entries)} entries...")

        # Phase 0
        reason = phase0_filter(entry)
        if reason:
            filtered_counts['phase0'] += 1
            reason_counts[reason] += 1
            continue
        
        # Phase 1
        stems = phase1_filter(entry, STOPWORDS)
        if stems:
            reason = ', '.join(stems)
            filtered_counts['phase1'] += 1
            reason_counts[reason] += 1
            continue
        
        # Phase 2
        if use_phase2:
            reason = phase2_filter(entry)
            if reason:
                filtered_counts['phase2'] += 1
                reason_counts[reason] += 1
                continue
        
        # Compositional bias
        bias_reason = phase_compositional_bias(entry, threshold=0.7)
        if bias_reason:
            filtered_counts['bias'] += 1
            reason_counts[bias_reason] += 1
            bias_entries.append((entry, bias_reason))
            continue
        
        kept_entries.append(entry)
    
    # Write outputs
    write_filtered_output(output_file, kept_entries, filtered_counts)
    write_bias_output(bias_output_file, bias_entries)
    write_reasons_output(reasons_file, reason_counts, filtered_counts, len(kept_entries))

    # Summary
    print(f"\nSummary:")
    print(f"  Input:    {len(entries):5d} comparisons")
    for phase, count in filtered_counts.items():
        print(f"  {phase:8s}: {count:5d} comparisons ({100*count/len(entries):.1f}%)")
    print(f"  Kept:     {len(kept_entries):5d} comparisons ({100*len(kept_entries)/len(entries):.1f}%)")
    print(f"  Unique reasons: {len(reason_counts)}")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Filter twilight zone protein comparisons')
    
    default_input = PROJECT_ROOT / "sw_results/sw_raw_finds.txt"
    default_output = PROJECT_ROOT / "sw_results/sw_finds.txt"
    default_reasons = PROJECT_ROOT / "sw_results/filter_reasons.txt"
    default_bias = PROJECT_ROOT / "sw_results/biased_alignments.txt"
    
    parser.add_argument('-i', '--input', default=str(default_input),
                        help='Input twilight comparison file')
    parser.add_argument('-o', '--output', default=str(default_output),
                        help='Output file for kept comparisons')
    parser.add_argument('-r', '--reasons', default=str(default_reasons),
                        help='Output file for filtering reasons')
    parser.add_argument('-b', '--bias-output', default=str(default_bias),
                        help='Output file for biased comparisons')
    parser.add_argument('--phase2', action='store_true', default=True,
                        help='Enable Phase 2 filtering (full record retrieval)')
    
    args = parser.parse_args()
    
    filter_twilight(args.input, args.output, args.reasons, args.bias_output, args.phase2)


if __name__ == '__main__':
    main()