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

def run_seq_search(identifier, use_fastnws=False, job=None):
    """
    This function can be called from other modules.
    The 'job' parameter is optional and is used for progress tracking.
    """
    target_record = find_target_record(identifier)

    if not target_record:
        if job:
            job.update(status="failed", errors=[f"Protein with identifier {identifier} not found."])
        else:
            print(f"Error: Protein with identifier {identifier} not found.")
        return

    scorer = FastNWS() if use_fastnws else FastNwsDummy()

    if not job:
        print(f"Scoring {target_record.entry_name} against all other proteins...")

    sequences_examined = 0
    last_ten_accepted = []

    for record in read_dat_records():
        if record.accessions[0] == target_record.accessions[0]:
            continue

        sequences_examined += 1
        protein_id = record.accessions[0]
        entry_name = record.entry_name
        name = record.description.split(';')[0]

        if job:
            job.update(
                sequences_examined=sequences_examined,
                most_recent_item=f"{protein_id} ..... {entry_name} {name}"
            )

        score = scorer.batch_nws([target_record.sequence], [record.sequence])[0][0]
        most_recent_item = f"{protein_id} {score:.2f} {entry_name} {name}"

        last_ten_accepted.append(most_recent_item)
        if len(last_ten_accepted) > 10:
            last_ten_accepted.pop(0)

        if job:
            job.update(
                sequences_examined=sequences_examined,
                most_recent_item=most_recent_item,
                last_ten_accepted=last_ten_accepted
            )
        else:
            print(most_recent_item)

def main():
    """
    Command-line interface for scoring a protein against all others in the database.
    """
    parser = argparse.ArgumentParser(description="Score a protein against the Swiss-Prot database.")
    parser.add_argument('identifier', help="Accession number or index of the protein to score.")
    parser.add_argument('--use-fastnws', action='store_true', help="Use FastNWS for scoring (untested).")
    args = parser.parse_args()

    run_seq_search(args.identifier, use_fastnws=args.use_fastnws)


if __name__ == '__main__':
    main()
