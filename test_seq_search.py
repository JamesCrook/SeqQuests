import numpy as np
from py.seq_search import find_target_record
from py.nws import FastNwsDummy

def test_score_protein_3():
    """
    Tests the scoring of protein with index 3 against protein with index 4.
    """
    # Find the protein with index 3 (the fourth protein)
    target_record = find_target_record(3)
    assert target_record is not None, "Protein with index 3 not found."

    # Find another protein to score against (e.g., index 4)
    record_to_score_against = find_target_record(4)
    assert record_to_score_against is not None, "Protein with index 4 not found."

    # Use the dummy scorer for testing
    scorer = FastNwsDummy()

    # Calculate the score
    score = scorer.batch_nws([target_record.sequence], [record_to_score_against.sequence])[0][0]

    # Assert that the score is a float (as a basic check)
    assert isinstance(score, (int, float, np.floating)), f"Score is not a float or int: {score}"

    print(f"Score of protein 3 vs 4 is {score:.2f}")

if __name__ == "__main__":
    test_score_protein_3()
    print("Test passed: Scoring of protein 3 works as expected.")
