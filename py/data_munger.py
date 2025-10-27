# data_munger.py should use sequences.py to read sequences and filter.

import argparse
from sequences import read_dat_records

# Mapping of common names to scientific names for filtering
ORGANISM_MAP = {
    'human': 'Homo sapiens',
    'rat': 'Rattus norvegicus',
    'ecoli': 'Escherichia coli',
    'yeast': 'Saccharomyces cerevisiae',
    'chicken': 'Gallus gallus',
    'mouse': 'Mus musculus',
}

def filter_proteins(records, organisms=None, require_go=False, require_ec=False, require_pfam=False, no_fragments=True, no_uncharacterized=True):
    """
    Filters a list of protein records based on specified criteria.
    """
    filtered_records = []

    # Keywords to identify uncharacterized proteins
    uncharacterized_keywords = ["Uncharacterized", "Putative", "Predicted"]

    for record in records:
        # Check for reviewed status (must have an ID line)
        if 'ID' not in record or "Reviewed" not in record['ID']:
            continue

        # --- Organism Filter ---
        if organisms:
            os_lines = record.get('OS', [])
            if isinstance(os_lines, str):
                os_lines = [os_lines]
            os_text = ' '.join(os_lines).lower()

            if not any(ORGANISM_MAP[org].lower() in os_text for org in organisms):
                continue

        de_lines = record.get('DE', [])
        if isinstance(de_lines, str):
            de_lines = [de_lines]
        de_text = ' '.join(de_lines)

        # --- Uncharacterized Filter ---
        if no_uncharacterized:
            if any(keyword in de_text for keyword in uncharacterized_keywords):
                continue

        # --- Feature Filter ---
        dr_lines = record.get('DR', [])
        if isinstance(dr_lines, str):
            dr_lines = [dr_lines]

        has_go = any('GO;' in line for line in dr_lines)
        has_ec = 'EC=' in de_text
        has_pfam = any('Pfam;' in line for line in dr_lines)

        # Mandatory filter: must have at least one of GO, EC, or Pfam
        if not (has_go or has_ec or has_pfam):
            continue

        # Optional additional filters from command line
        if require_go and not has_go:
            continue
        if require_ec and not has_ec:
            continue
        if require_pfam and not has_pfam:
            continue

        # --- Fragment Filter ---
        if no_fragments and 'Fragment' in de_text:
            continue

        filtered_records.append(record)

    return filtered_records

def main():
    """
    Command-line interface for filtering protein data.
    """
    parser = argparse.ArgumentParser(description="Filter Swiss-Prot protein data.")
    parser.add_argument('--organisms', nargs='+', choices=list(ORGANISM_MAP.keys()), help="Filter by one or more organisms.")
    parser.add_argument('--require-go', action='store_true', help="Only include proteins with GO terms.")
    parser.add_argument('--require-ec', action='store_true', help="Only include proteins with EC numbers.")
    parser.add_argument('--require-pfam', action='store_true', help="Only include proteins with Pfam domains.")

    args = parser.parse_args()

    print("Reading protein data...")
    all_records = read_dat_records()
    print(f"Read {len(all_records)} total records.")

    filtered = filter_proteins(
        all_records,
        organisms=args.organisms,
        require_go=args.require_go,
        require_ec=args.require_ec,
        require_pfam=args.require_pfam
    )

    print(f"Found {len(filtered)} records matching the criteria.")

    # You can add more output options here, like printing record IDs
    for record in filtered:
        print(record.get('ID', 'No ID'))


if __name__ == '__main__':
    main()
