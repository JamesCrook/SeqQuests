# seq_search.py should gather scores for similarity between a chosen protein and each of the proteins in a chosen databsase.

import argparse
from sequences import read_dat_records
from nws import FastNwsDummy, FastNWS

def main():
    """
    Command-line interface for scoring a protein against all others in the database.
    """
    parser = argparse.ArgumentParser(description="Score a protein against the Swiss-Prot database.")
    parser.add_argument('accession', help="Accession number of the protein to score.")
    parser.add_argument('--use-fastnws', action='store_true', help="Use FastNWS for scoring (untested).")
    args = parser.parse_args()

    all_records = list(read_dat_records())
    target_record = None
    for record in all_records:
        if args.accession in record.accessions:
            target_record = record
            break

    if not target_record:
        print(f"Error: Protein with accession number {args.accession} not found.")
        return

    if args.use_fastnws:
        scorer = FastNWS()
    else:
        scorer = FastNwsDummy()

    print(f"Scoring {target_record.entry_name} against all other proteins...")

    for record in all_records:
        if record == target_record:
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
