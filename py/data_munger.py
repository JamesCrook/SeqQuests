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

def filter_proteins(records, organisms=None, require_go=False, require_ec=False, require_pfam=False, no_fragments=True, no_uncharacterized=True, require_any_feature=True):
    """
    Filters an iterator of protein records based on specified criteria.
    Yields records that match.
    """
    # Keywords to identify uncharacterized proteins
    uncharacterized_keywords = ["Uncharacterized", "Putative", "Predicted"]

    for record in records:
        # Check for reviewed status
        if record.data_class != "Reviewed":
            continue

        # --- Organism Filter ---
        if organisms:
            os_text = record.organism.lower()
            if not any(ORGANISM_MAP[org].lower() in os_text for org in organisms):
                continue

        de_text = record.description

        # --- Uncharacterized Filter ---
        if no_uncharacterized:
            if any(keyword in de_text for keyword in uncharacterized_keywords):
                continue

        # --- Feature Filter ---
        # record.cross_references is a list of tuples, e.g., ('Pfam', 'PF00384', 'AAA', '1')
        has_go = any(ref[0] == 'GO' for ref in record.cross_references)
        # EC numbers are in the DE line (description)
        has_ec = 'EC=' in de_text
        has_pfam = any(ref[0] == 'Pfam' for ref in record.cross_references)

        # Mandatory filter: must have at least one of GO, EC, or Pfam
        if require_any_feature and not (has_go or has_ec or has_pfam):
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

        yield record

def run_data_munging(organisms=None, require_go=False, require_ec=False, require_pfam=False, job=None):
    """
    This function can be called from other modules.
    The 'job' parameter is optional and is used for progress tracking.
    """
    all_records = read_dat_records()

    # Correctly call the generator and convert to a list for processing
    filtered_iterator = filter_proteins(
        all_records,
        organisms=organisms,
        require_go=require_go,
        require_ec=require_ec,
        require_pfam=require_pfam
    )

    sequences_examined = 0
    proteins_processed = 0
    last_ten_accepted = []

    # Iterate through the filtered results
    for record in filtered_iterator:
        sequences_examined += 1
        protein_id = record.accessions[0]
        entry_name = record.entry_name
        name = record.description.split(';')[0]

        most_recent_item = f"{protein_id} {entry_name} {name}"

        proteins_processed += 1
        last_ten_accepted.append(most_recent_item)
        if len(last_ten_accepted) > 10:
            last_ten_accepted.pop(0)



        if job:
            job.update(
                sequences_examined=sequences_examined,
                proteins_processed=proteins_processed,
                most_recent_item=most_recent_item,
                last_ten_accepted=last_ten_accepted,
                progress=f"Done: {proteins_processed}"
            )
        else:
            # Print to console if not a job
            print(most_recent_item)

    if not job:
        print(f"Found {proteins_processed} records matching the criteria.")

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

    print("Filtering protein data...")
    run_data_munging(
        organisms=args.organisms,
        require_go=args.require_go,
        require_ec=args.require_ec,
        require_pfam=args.require_pfam
    )

if __name__ == '__main__':
    main()
