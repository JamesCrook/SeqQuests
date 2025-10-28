# seq_search.py should gather scores for similarity between a chosen protein and each of the proteins in a chosen databsase.

import argparse
from sequences import read_dat_records
from nws import FastNwsDummy, FastNWS

def find_target_record(identifier):
    """
    Finds a specific record in the Swiss-Prot database by accession number or index.
    """
    try:
        # Try to convert to integer for index-based search
        idx = int(identifier)
        for i, record in enumerate(read_dat_records()):
            if i == idx:
                return record
    except ValueError:
        # If not an integer, assume it's an accession number
        for record in read_dat_records():
            if identifier in record.accessions:
                return record
    return None

def main():
    """
    Command-line interface for scoring a protein against all others in the database.
    """
    parser = argparse.ArgumentParser(description="Score a protein against the Swiss-Prot database.")
    parser.add_argument('identifier', help="Accession number or index of the protein to score.")
    parser.add_argument('--use-fastnws', action='store_true', help="Use FastNWS for scoring (untested).")
    args = parser.parse_args()

    target_record = find_target_record(args.identifier)

    if not target_record:
        print(f"Error: Protein with identifier {args.identifier} not found.")
        return

    if args.use_fastnws:
        scorer = FastNWS()
    else:
        scorer = FastNwsDummy()

    print(f"Scoring {target_record.entry_name} against all other proteins...")

    for record in read_dat_records():
        if record.accessions[0] == target_record.accessions[0]:
            continue

        score = scorer.batch_nws([target_record.sequence], [record.sequence])[0][0]

        protein_id = record.accessions[0]
        entry_name = record.entry_name
        if 'RecName: Full=' in record.description:
            name = record.description.split('RecName: Full=')[1].split(';')[0]
        else:
            name = record.description.split(';')[0]

        print(f"{protein_id} {score:.2f} {entry_name} {name}")


if __name__ == '__main__':
    main()
