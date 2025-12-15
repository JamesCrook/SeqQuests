#!/usr/bin/env python3
"""
Filter twilight zone protein comparisons by identifying unsurprising matches.

This program:
1. Parses a twilight comparison file
2. Uses fuzzy string matching (after stopword removal and stemming) to find shared terms
3. Optionally retrieves full UniProt records for deeper analysis
4. Produces a filtered file and a reasons file for auditing
"""

import re
from collections import defaultdict
from typing import List, Tuple, Optional, Set, Callable, Dict, Any
import argparse

import sequences
from config import PROJECT_ROOT
from sw_align import assess_compositional_bias, align_local_swissprot


# =============================================================================
# Configuration
# =============================================================================

STOPWORDS = {
    # Generic terms
    'protein', 'domain', 'containing', 'subunit', 'member', 'regulator', 'fragment',
    'precursor', 'chain', 'component', 'factor', 'element', 'unit', 'specific',
    # Modifiers
    'probable', 'putative', 'possible', 'predicted', 'potential',
    'uncharacterized', 'hypothetical', 'unknown',
    # Size/position descriptors
    'small', 'large', 'short', 'long', 'terminal', 'internal',
    # Common but uninformative
    'type', 'like', 'related', 'homolog', 'ortholog', 'paralog',
    'family', 'superfamily', 'class',
}

# Minimum length for a stem to be considered a valid reason
MIN_STEM_LENGTH = 8


# =============================================================================
# Text Processing Functions
# =============================================================================

def simple_stem(word: str) -> str:
    """
    Simple suffix-stripping stemmer.
    Removes common English suffixes to normalize words.
    """
    word = word.lower()
    
    # Remove common suffixes
    suffixes = ['ase', 'ases', 'ing', 'ed', 'es', 's', 'tion', 'sion', 'ness', 'ment']
    for suffix in suffixes:
        if len(word) > len(suffix) + MIN_STEM_LENGTH and word.endswith(suffix):
            return word[:-len(suffix)]
    
    return word


def extract_meaningful_tokens(name: str, stopwords: Set[str]) -> List[str]:
    """
    Extract meaningful tokens from a protein name.
    
    Args:
        name: Protein name string
        stopwords: Set of words to ignore
    
    Returns:
        List of stemmed tokens
    """
    # Remove organism, common patterns and punctuation
    name = re.sub(r';\s*[^;]+$', '', name)  # Remove organism
    name = re.sub(r'\{[^}]*\}', '', name)  # Remove {ECO:...} annotations
    name = re.sub(r'\([^)]*\)', '', name)  # Remove parenthetical info
    
    # Split on word boundaries, hyphens, and special chars
    tokens = re.findall(r'[a-zA-Z0-9]+', name.lower())
    
    # Filter and stem
    meaningful_tokens = []
    for token in tokens:
        # Skip numbers, short tokens, and stopwords
        if token.isdigit() or len(token) < 3 or token in stopwords:
            continue
        
        stemmed = simple_stem(token)
        if len(stemmed) >= MIN_STEM_LENGTH:
            meaningful_tokens.append(stemmed)
    
    return meaningful_tokens


def find_common_stems(tokens1: List[str], tokens2: List[str]) -> List[str]:
    """Find common stems between two token lists."""
    set1 = set(tokens1)
    set2 = set(tokens2)
    return sorted(set1 & set2)


# =============================================================================
# Record Parsing
# =============================================================================

class TwilightEntry:
    """Represents a single twilight zone comparison."""
    
    def __init__(self, header_line: str, protein1_line: str, protein2_line: str):
        self.raw_header = header_line
        self.raw_protein1 = protein1_line
        self.raw_protein2 = protein2_line
        
        # Parse header: "135066-235941 s(299) P13386-Q96JQ5 Length: 243/239"
        header_match = re.match(
            r'(\d+)-(\d+)\s+s\((\d+)\)\s+([A-Z0-9]+)-([A-Z0-9]+)\s+Length:\s+(\d+)/(\d+)',
            header_line
        )
        if not header_match:
            raise ValueError(f"Could not parse header: {header_line}")
        
        self.num1 = int(header_match.group(1))
        self.num2 = int(header_match.group(2))
        self.score = int(header_match.group(3))
        self.id1 = header_match.group(4)
        self.id2 = header_match.group(5)
        self.len1 = int(header_match.group(6))
        self.len2 = int(header_match.group(7))
        
        # Parse protein lines: " 135066: High affinity...; Rattus norvegicus (Rat)."
        protein1_match = re.match(r'\s+\d+:\s+(.+)', protein1_line)
        protein2_match = re.match(r'\s+\d+:\s+(.+)', protein2_line)
        
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
        
        # Skip empty lines and summary sections
        if not line or line.startswith('found ') or line.startswith('===') or line.startswith('TOTAL SKIPPED'):
            i += 1
            continue
        
        # Look for header lines (start with digits)
        if re.match(r'^\d+-\d+\s+s\(', line):
            # Need the next two lines for protein names
            if i + 2 < len(lines):
                try:
                    entry = TwilightEntry(line, lines[i+1], lines[i+2])
                    entries.append(entry)
                except ValueError as e:
                    print(f"Warning: {e}")
                i += 3
            else:
                i += 1
        else:
            i += 1
    
    return entries


# =============================================================================
# Filtering Logic
# =============================================================================

def phase0_filter(entry: TwilightEntry) -> Optional[str]:
    """
    Phase 0: Superficial analysis, drop similarities that aren't useful 
    e.g. between unknown proteins, or where the names are really similar.
    Returns:
        Reason string if should be filtered, None if should keep
    """

    if 'toxin' in entry.name1.lower() and 'toxin' in entry.name2.lower():
        return 'toxins'
    if ('uncharacterized' in entry.name1.lower() or 'uncharacterized' in entry.name2.lower() or
        'putative' in entry.name1.lower() or 'putative' in entry.name2.lower()):
        return 'uncharacterized'
    if entry.name1.lower()[:11] == entry.name2.lower()[:11]:
        return 'similar names'
    return None

def phase1_filter(entry: TwilightEntry, stopwords: Set[str]) -> Optional[List[str]]:
    """
    Phase 1: String-based fuzzy matching.
    
    Returns:
        List of matching stems if should be filtered, None if should keep
    """
    tokens1 = extract_meaningful_tokens(entry.name1, stopwords)
    tokens2 = extract_meaningful_tokens(entry.name2, stopwords)
    
    common_stems = find_common_stems(tokens1, tokens2)
    
    if common_stems:
        return common_stems
    
    return None


def extract_similarity_terms(record) -> Set[str]:
    """
    Extract meaningful terms from -!- SIMILARITY: lines in a SwissProt record.
    """
    terms = set()
    
    # Additional stopwords specific to SIMILARITY lines
    similarity_stopwords = STOPWORDS | {
        'protein', 'proteins', 'subfamily', 'group', 'class', 'type', 
        'member', 'contains', 'domain', 'domains', 'repeat', 'repeats',
        'region', 'regions', 'motif', 'motifs', 'sequence', 'sequences'
    }
    
    # Get comments from the record
    if hasattr(record, 'comments'):
        for comment in record.comments:
            # SIMILARITY comments have this pattern
            if comment.startswith('SIMILARITY:'):
                # Remove the prefix
                text = comment[11:].strip()
                
                # Remove common prefixes like "Belongs to the..."
                text = re.sub(r'^Belongs to the\s+', '', text, flags=re.IGNORECASE)
                text = re.sub(r'^Member of the\s+', '', text, flags=re.IGNORECASE)
                
                # Extract significant words (families, superfamilies, etc.)
                # Look for capitalized terms or specific patterns
                words = re.findall(r'\b[A-Z][a-z]+(?:\s+[a-z]+)?\b|\b\w+(?:-\w+)+\b', text)
                
                # Also extract anything in quotes or after "family", "superfamily"
                family_match = re.search(r'([\w-]+)\s+(?:super)?family', text, re.IGNORECASE)
                if family_match:
                    family_term = family_match.group(1).lower()
                    if family_term not in similarity_stopwords and len(family_term) >= 6:
                        terms.add(family_term)
                
                # Add individual significant words (longer than 5 chars, not stopwords)
                for word in words:
                    word = word.lower().strip()
                    if len(word) >= 6 and word not in similarity_stopwords:
                        terms.add(word)
    
    return terms


def extract_family_terms(record) -> Set[str]:
    """
    Extract family names from various record fields.
    Looks near keywords like "Family:", "Belongs to", etc.
    PRESERVES numbers to distinguish subfamilies.
    """
    terms = set()
    
    # Check description for family mentions
    if hasattr(record, 'description'):
        desc = record.description
        
        # Look for "Family: X" pattern - keep numbers!
        family_match = re.search(r'Family:\s*([\w-]+(?:\s+\d+)?)', desc, re.IGNORECASE)
        if family_match:
            terms.add(family_match.group(1).lower())
    
    # Check comments for "Belongs to the X family"
    if hasattr(record, 'comments'):
        for comment in record.comments:
            # Look for family membership - keep numbers!
            belongs_match = re.search(r'Belongs to the\s+([\w-]+(?:\s+[\w-]+)?(?:\s+\d+)?)\s+family', 
                                     comment, re.IGNORECASE)
            if belongs_match:
                family_name = belongs_match.group(1).lower()
                terms.add(family_name)
    
    return terms


def extract_interpro_ids(record) -> Set[str]:
    """
    Extract InterPro IDs from cross-references.
    These are highly specific domain/family identifiers.
    """
    interpro_ids = set()
    
    if hasattr(record, 'cross_references'):
        for xref in record.cross_references:
            if xref[0] == 'InterPro' and len(xref) >= 2:
                interpro_ids.add(xref[1])  # e.g., 'IPR016533'
    
    return interpro_ids

def extract_panther_ids(record) -> Set[str]:
    """
    Extract PANTHER family IDs from cross-references.
    These are protein family/subfamily identifiers.
    
    Note: Extracts only the family ID (e.g., 'PTHR18875'), 
    stripping any subfamily suffix (e.g., ':SF8').
    """
    panther_ids = set()
    
    if hasattr(record, 'cross_references'):
        for xref in record.cross_references:
            if xref[0] == 'PANTHER' and len(xref) >= 2:
                # xref[1] is like 'PTHR18875:SF8' or 'PTHR18875'
                family_id = xref[1].split(':')[0]  # Get just 'PTHR18875'
                panther_ids.add(family_id)
    
    return panther_ids

def extract_domain_terms(record) -> Set[str]:
    """
    Extract domain/repeat names from record annotations.
    Looks for InterPro, Pfam, PROSITE domains.
    """
    terms = set()
    
    # Check cross-references for domain databases
    if hasattr(record, 'cross_references'):
        for xref in record.cross_references:
            db = xref[0]
            # InterPro, Pfam, SMART, PROSITE all contain domain info
            if db in ('InterPro', 'Pfam', 'SMART', 'PROSITE', 'SUPFAM'):
                # xref format is typically: ('Pfam', 'PF00001', 'Domain_name')
                if len(xref) >= 3:
                    domain_name = xref[2].lower()
                    # Extract meaningful part of domain name
                    # Remove version numbers, clean up
                    domain_name = re.sub(r'[._]\d+$', '', domain_name)
                    if len(domain_name) >= 5:
                        terms.add(domain_name)
    
    # Check feature table for domain annotations
    if hasattr(record, 'features'):
        for feature in record.features:
            # feature is a FeatureTable object with attributes, not subscriptable
            if hasattr(feature, 'type') and feature.type in ('DOMAIN', 'REPEAT', 'REGION'):
                if hasattr(feature, 'description'):
                    desc = feature.description.lower()
                    # Extract domain name from description
                    words = re.findall(r'\b[a-z]{5,}\b', desc)
                    terms.update(words)
    
    return terms


def check_common_terms(record1, record2, extractor_func: Callable, min_length: int = 6) -> Optional[str]:
    """
    Generic function to find common terms between two records using a specific extractor.

    Returns:
        The longest common term if found and meets length criteria, else None.
    """
    terms1 = extractor_func(record1)
    terms2 = extractor_func(record2)

    common = terms1 & terms2

    if common:
        longest = max(common, key=len)
        if len(longest) >= min_length:
            return longest
    return None


def check_interpro_ids(record1, record2) -> Optional[str]:
    """
    Compare InterPro IDs between two records.
    Returns the first alphabetically sorted common ID.
    """
    ids1 = extract_interpro_ids(record1)
    ids2 = extract_interpro_ids(record2)

    common = ids1 & ids2

    if common:
        return sorted(common)[0]
    return None


def check_panther_ids(record1, record2) -> Optional[str]:
    """
    Compare Panther IDs between two records.
    """
    ids1 = extract_panther_ids(record1)
    ids2 = extract_panther_ids(record2)

    common = ids1 & ids2

    if common:
        return sorted(common)[0]
    return None

def check_sequential_panther_ids(record1, record2) -> Optional[str]:
    """
    Check if two records have sequential PANTHER family IDs,
    which may indicate similar structure.
    
    Returns:
        String like "PTHR18875/PTHR18876" if sequential IDs found, None otherwise
    """
    ids1 = extract_panther_ids(record1)
    ids2 = extract_panther_ids(record2)
    
    for id1 in ids1:
        # Extract the numeric part
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
                # Return in numerical order
                if num1 < num2:
                    return f"{id1}/{id2}"
                else:
                    return f"{id2}/{id1}"
    
    return None

def phase2_filter(entry: TwilightEntry) -> Optional[str]:
    """
    Phase 2: Full record analysis.

    Retrieves full UniProt records and checks multiple criteria.

    Returns:
        Reason string if should be filtered, None if should keep
    """
    try:
        r1 = sequences.get_protein(entry.num1)
        r2 = sequences.get_protein(entry.num2)

        # Check InterPro IDs first (most specific)
        match = check_interpro_ids(r1.full, r2.full)
        if match:
            return f"InterPro: {match}"

        match = check_panther_ids(r1.full, r2.full)
        if match:
            return f"Panther: {match}"

        # As of 15th Dec 2025 the sequential panther Id check only filters out
        # one match, Panther: PTHR22796/PTHR22797 
        seq_match = check_sequential_panther_ids(r1.full, r2.full)
        if seq_match:
            return f"Panther: {seq_match}"

        # Define checks as (check_func, extractor, prefix) or custom lambda
        checks = [
            (extract_similarity_terms, "-!- SIMILARITY: "),
            (extract_family_terms, "Family: "),
            (extract_domain_terms, "Domain: ")
        ]

        for extractor, prefix in checks:
            match = check_common_terms(r1.full, r2.full, extractor)
            if match:
                return f"{prefix}{match}"

    except Exception as e:
        print(f"Warning: Phase 2 failed for {entry.num1}-{entry.num2}: {e}")

    return None

def phase_compositional_bias(entry, threshold=0.5):
    """
    Phase for compositional bias detection.
    
    Retrieves sequences, performs alignment, and checks for compositional bias.
    
    Args:
        entry: TwilightEntry object
        threshold: Goodness threshold (default 0.5). Values below this are flagged.
    
    Returns:
        str: Reason string if biased (e.g., "Compositional: K-Rich (65%)")
        None: If not biased or alignment failed
    """
    try:
        # Get the protein sequences
        r1 = sequences.get_protein(entry.num1)
        r2 = sequences.get_protein(entry.num2)
        
        # Perform local alignment
        result = align_local_swissprot(
            r1.full.sequence, 
            r2.full.sequence,
            weights='PAM250',
            gap_extend=-10
        )
        
        if not result:
            # No significant alignment found
            return None
        
        # Assess compositional bias
        bias_result = assess_compositional_bias(
            result['aligned_a'],
            result['aligned_b']
        )
        
        # Check if biased
        if bias_result['goodness'] < threshold:
            return f"Compositional: {bias_result['reason']}"
        
        return None
        
    except Exception as e:
        print(f"Warning: Compositional bias check failed for {entry.num1}-{entry.num2}: {e}")
        return None




# =============================================================================
# Output Writing
# =============================================================================

def write_filtered_output(output_file: str, kept_entries: List[TwilightEntry],
                          filtered_count1: int, filtered_count2: int,
                          filtered_bias: int):
    """Write the kept entries to the output file."""
    print(f"\nWriting {len(kept_entries)} kept entries to {output_file}...")
    with open(output_file, 'w') as f:
        f.write(f"Kept {len(kept_entries)} entries after filtering\n")
        f.write(f"Filtered out {filtered_count1} entries\n")
        f.write(f"Filtered out {filtered_count2} entries in phase2\n")
        f.write(f"Filtered out {filtered_bias} entries (compositional bias)\n\n")

        for entry in kept_entries:
            f.write(entry.raw_header + '\n')
            f.write(entry.raw_protein1)
            f.write(entry.raw_protein2)

def write_bias_output( bias_output_file: str, bias_entries: List[TwilightEntry] ):
    # Write bias output if requested
    if bias_output_file and bias_entries:
        print(f"Writing {len(bias_entries)} biased entries to {bias_output_file}...")
        with open(bias_output_file, 'w') as f:
            f.write(f"Composition-biased alignments: {len(bias_entries)} entries\n\n")
            for entry in bias_entries:
                f.write(entry.raw_header + '\n')
                f.write(entry.raw_protein1)
                f.write(entry.raw_protein2)

def write_reasons_output(reasons_file: str, reason_counts: Dict[str, int],
                         filtered_count1: int, filtered_count2: int, filtered_bias: int, kept_count: int):
    """Write the filtering reasons to a file."""
    print(f"Writing reasons to {reasons_file}...")
    with open(reasons_file, 'w') as f:
        f.write("FILTERING REASONS (sorted by length - shortest first)\n")
        f.write("=" * 80 + "\n\n")

        # Sort reasons by length, then alphabetically
        sorted_reasons = sorted(reason_counts.items(),
                              key=lambda x: (len(x[0]), x[0]))

        for reason, count in sorted_reasons:
            f.write(f"{reason:40s} : {count:5d}\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write(f"Total filtered: {filtered_count1 + filtered_count2 + filtered_bias}\n")
        f.write(f"of which: {filtered_count2} in phase2\n")
        f.write(f"of which: {filtered_bias} as biassed\n")
        f.write(f"Total kept: {kept_count}\n")




# =============================================================================
# Main Processing
# =============================================================================

def filter_twilight(input_file, output_file, reasons_file, 
                               bias_output_file=None, use_phase2=False):
    """
    Filtering function with compositional bias detection.
    Excludes known hits.
    Writes biased hits to a separate file.
    
    Args:
        input_file: Input twilight comparison file
        output_file: Output file for kept comparisons
        reasons_file: File for filtering reasons
        bias_output_file: Optional separate file for composition-biased hits
        use_phase2: Whether to use full record analysis
    """
    from collections import defaultdict
    from filter_twilight import (parse_twilight_file, phase1_filter, 
                                 phase2_filter, STOPWORDS)
    
    print(f"Parsing {input_file}...")
    entries = parse_twilight_file(input_file)
    print(f"Found {len(entries)} comparisons")
    
    filtered_count0 = 0  # Phase 0: simple criteria
    filtered_count1 = 0  # Phase 1: string matching
    filtered_count2 = 0  # Phase 2: full record
    filtered_bias = 0    # Compositional bias
    kept_entries = []
    bias_entries = []    # Separate list for biased entries
    reason_counts = defaultdict(int)
    
    print("Filtering...")
    for i, entry in enumerate(entries):
        if (i + 1) % 1000 == 0:
            print(f"  Processed {i + 1}/{len(entries)} entries...")


        # Phase 1: String matching
        simple_reason = phase0_filter(entry)
        if simple_reason:
            filtered_count0 += 1
            reason_counts[simple_reason] += 1
            continue
        
        # Phase 1: String matching
        stems = phase1_filter(entry, STOPWORDS)
        if stems:
            reason = ', '.join(stems)
            filtered_count1 += 1
            reason_counts[reason] += 1
            continue
        
        # Phase 2: Full record analysis
        if use_phase2:
            reason = phase2_filter(entry)
            if reason:
                filtered_count2 += 1
                reason_counts[reason] += 1
                continue
        
        # Phase Compositional Bias: Check alignment composition
        bias_reason = phase_compositional_bias(entry, threshold=0.7)
        if bias_reason:
            filtered_bias += 1
            reason_counts[bias_reason] += 1
            bias_entries.append(entry)  # Save to separate list
            continue
        
        # No filter matched - keep this entry
        kept_entries.append(entry)
    
    # Write main outputs

    write_filtered_output(output_file, kept_entries,
        filtered_count1, filtered_count2, filtered_bias)

    write_bias_output( bias_output_file, bias_entries )
    write_reasons_output(reasons_file, reason_counts,
        filtered_count1, filtered_count2, filtered_bias, len(kept_entries))

    print(f"\nSummary:")
    print(f"  Input:        {len(entries):5d} comparisons")
    print(f"  Filtered0:    {filtered_count0:5d} comparisons ({100*filtered_count0/len(entries):.1f}%)")
    print(f"  Filtered1:    {filtered_count1:5d} comparisons ({100*filtered_count1/len(entries):.1f}%)")
    print(f"  Filtered2:    {filtered_count2:5d} comparisons ({100*filtered_count2/len(entries):.1f}%)")
    print(f"  Bias:         {filtered_bias:5d} comparisons ({100*filtered_bias/len(entries):.1f}%)")
    print(f"  Kept:         {len(kept_entries):5d} comparisons ({100*len(kept_entries)/len(entries):.1f}%)")
    print(f"  Unique reasons: {len(reason_counts)}")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Filter twilight zone protein comparisons'
    )
    
    default_input = PROJECT_ROOT / "sw_results/sw_raw_finds.txt"
    #default_output = PROJECT_ROOT / "sw_results/twilight_filtered.txt"
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
    parser.add_argument('--phase2', action='store_true',
                       help='Enable Phase 2 filtering (full record retrieval)')
    
    parser.set_defaults(phase2=True)
    args = parser.parse_args()
    
    filter_twilight(
        args.input, 
        args.output, 
        args.reasons,
        args.bias_output,
        args.phase2
    )

if __name__ == '__main__':
    main()