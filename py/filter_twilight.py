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
from typing import List, Tuple, Optional, Set
import argparse

import sequences
from config import PROJECT_ROOT

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
    # Remove common patterns and punctuation
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
    
    Args:
        record: Biopython SwissProt record (from record.full)
    
    Returns:
        Set of significant terms from similarity annotations
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


def check_similarity_lines(record1, record2) -> Optional[str]:
    """
    Compare SIMILARITY annotations between two records.
    
    Returns:
        Common term if found, None otherwise
    """
    terms1 = extract_similarity_terms(record1)
    terms2 = extract_similarity_terms(record2)
    
    common = terms1 & terms2
    
    if common:
        # Return the longest common term, but only if >= 6 characters
        longest = max(common, key=len)
        if len(longest) >= 6:
            return longest
    
    return None


def check_family_annotations(record1, record2) -> Optional[str]:
    """
    Compare family annotations between two records.
    
    Returns:
        Common family name if found, None otherwise
    """
    families1 = extract_family_terms(record1)
    families2 = extract_family_terms(record2)
    
    common = families1 & families2
    
    if common:
        longest = max(common, key=len)
        if len(longest) >= 6:
            return longest
    
    return None


def check_domain_annotations(record1, record2) -> Optional[str]:
    """
    Compare domain annotations between two records.
    
    Returns:
        Common domain name if found, None otherwise
    """
    domains1 = extract_domain_terms(record1)
    domains2 = extract_domain_terms(record2)
    
    common = domains1 & domains2
    
    if common:
        longest = max(common, key=len)
        if len(longest) >= 6:
            return longest
    
    return None

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


def check_interpro_ids(record1, record2) -> Optional[str]:
    """
    Compare InterPro IDs between two records.
    
    Returns:
        Common InterPro ID if found, None otherwise
    """
    ids1 = extract_interpro_ids(record1)
    ids2 = extract_interpro_ids(record2)
    
    common = ids1 & ids2
    
    if common:
        # Return first match (they're all equally specific)
        return f"InterPro: {sorted(common)[0]}"
    
    return None


def phase2_filter(entry: TwilightEntry) -> Optional[str]:
    """
    Phase 2: Full record analysis.
    
    Retrieves full UniProt records and looks for:
    - InterPro IDs (most specific!)
    - SIMILARITY lines
    - Family annotations  
    - Domain/repeat annotations
    
    Returns:
        Reason string if should be filtered, None if should keep
    """
    try:
        # Retrieve full records
        r1 = sequences.get_protein(entry.num1)
        r2 = sequences.get_protein(entry.num2)
        
        # Check InterPro IDs first (most specific)
        interpro_match = check_interpro_ids(r1.full, r2.full)
        if interpro_match:
            return interpro_match
        
        # Check SIMILARITY lines
        similarity_match = check_similarity_lines(r1.full, r2.full)
        if similarity_match:
            return f"-!- SIMILARITY: {similarity_match}"
        
        # Check Family annotations
        family_match = check_family_annotations(r1.full, r2.full)
        if family_match:
            return f"Family: {family_match}"
        
        # Check domain annotations
        domain_match = check_domain_annotations(r1.full, r2.full)
        if domain_match:
            return f"Domain: {domain_match}"
        
    except Exception as e:
        print(f"Warning: Phase 2 failed for {entry.num1}-{entry.num2}: {e}")
    
    return None


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


# =============================================================================
# Main Processing
# =============================================================================

def filter_twilight_file(input_file: str, 
                        output_file: str, 
                        reasons_file: str,
                        use_phase2: bool = False):
    """
    Main filtering function.
    
    Args:
        input_file: Path to twilight comparison file
        output_file: Path to write filtered (kept) comparisons
        reasons_file: Path to write filtering reasons
        use_phase2: Whether to use full record retrieval (Phase 2)
    """
    print(f"Parsing {input_file}...")
    entries = parse_twilight_file(input_file)
    print(f"Found {len(entries)} comparisons")
    
    filtered_entries = []
    filtered_entries2 = []
    kept_entries = []
    reason_counts = defaultdict(int)
    
    print("Filtering...")
    for i, entry in enumerate(entries):
        if (i + 1) % 1000 == 0:
            print(f"  Processed {i + 1}/{len(entries)} entries...")
        
        # Phase 1: String matching
        stems = phase1_filter(entry, STOPWORDS)
        
        if stems:
            reason = ', '.join(stems)
            filtered_entries.append((entry, reason))
            reason_counts[reason] += 1
            continue
        
        # Phase 2: Full record analysis (optional)
        if use_phase2:
            reason = phase2_filter(entry)
            if reason:
                filtered_entries2.append((entry, reason))
                reason_counts[reason] += 1
                continue
        
        # No filter matched - keep this entry
        kept_entries.append(entry)
    
    # Write filtered file
    print(f"\nWriting {len(kept_entries)} kept entries to {output_file}...")
    with open(output_file, 'w') as f:
        f.write(f"Kept {len(kept_entries)} entries after filtering\n")
        f.write(f"Filtered out {len(filtered_entries)} entries\n\n")
        f.write(f"Filtered out {len(filtered_entries2)} entries in phase2\n\n")
        
        for entry in kept_entries:
            f.write(entry.raw_header + '\n')
            f.write(entry.raw_protein1)
            f.write(entry.raw_protein2)
    
    # Write reasons file (sorted by length, then alphabetically)
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
        f.write(f"Total filtered: {len(filtered_entries)+len(filtered_entries2)}\n")
        f.write(f"of which: {len(filtered_entries2)} in phase2\n")
        f.write(f"Total kept: {len(kept_entries)}\n")
    
    print(f"\nSummary:")
    print(f"  Input:    {len(entries):5d} comparisons")
    print(f"  Filtered1: {len(filtered_entries):5d} comparisons ({100*len(filtered_entries)/len(entries):.1f}%)")
    print(f"  Filtered2: {len(filtered_entries2):5d} comparisons ({100*len(filtered_entries2)/len(entries):.1f}%)")
    print(f"  Kept:     {len(kept_entries):5d} comparisons ({100*len(kept_entries)/len(entries):.1f}%)")
    print(f"  Unique reasons: {len(reason_counts)}")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Filter twilight zone protein comparisons',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python filter_twilight.py twilight.txt -o filtered.txt -r reasons.txt
  python filter_twilight.py twilight.txt -o filtered.txt -r reasons.txt --phase2
        """
    )
    
    default_input = PROJECT_ROOT / "sw_results/sw_finds.txt"
    default_output = PROJECT_ROOT / "sw_results/twilight_filtered.txt"
    default_reasons = PROJECT_ROOT / "sw_results/filter_reasons.txt"

    parser.add_argument('-i', '--input', default=str(default_input), help='Input twilight comparison file')
    parser.add_argument('-o', '--output', default=str(default_output),
                       help='Output file for kept comparisons (default: twilight_filtered.txt)')
    parser.add_argument('-r', '--reasons', default=str(default_reasons),
                       help='Output file for filtering reasons (default: filter_reasons.txt)')
    parser.add_argument('--phase2', action='store_true',
                       help='Enable Phase 2 filtering (full record retrieval)')
    
    parser.set_defaults(phase2=True)

    args = parser.parse_args()
    
    filter_twilight_file(args.input, args.output, args.reasons, args.phase2)


if __name__ == '__main__':
    main()