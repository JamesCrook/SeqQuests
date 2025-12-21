# Internal Python API Reference

This document provides documentation for the internal Python modules used in the SeqQuests project.

## `job_manager` Module

The `job_manager` module handles the lifecycle of background jobs.

### `Job` Class (Base)
*   **`__init__(self, job_manager)`**: Initializes a new job.
*   **`start(self)`**: Starts the job execution.
*   **`pause(self)`**: Pauses the job.
*   **`resume(self)`**: Resumes the job.
*   **`delete(self)`**: Deletes the job and cleans up resources.
*   **`get_state(self)`**: Returns the current state of the job (e.g., status, progress).
*   **`configure(self, config)`**: Configures the job with the provided dictionary.

### `JobManager` Class
*   **`create_job(self, job_type)`**: Creates a new job of the specified type.
*   **`get_job(self, job_id)`**: Retrieves a job by ID.
*   **`list_jobs(self)`**: Returns a list of all jobs.
*   **`delete_job(self, job_id)`**: Deletes a job from the manager.

## `sequences` Module

The `sequences` module abstracts sequence data access.

### `DataManager` Class (Singleton)
*   **`get_fasta_cache(self)`**: Returns the singleton `SequenceCache` for FASTA data.
*   **`get_swissprot_cache(self, file_format)`**: Returns the singleton `SequenceCache` for Swiss-Prot data.
*   **`reset(self)`**: Resets the internal caches (useful for testing).

### Helper Functions
*   **`read_fasta_sequences()`**: Returns an iterator over FASTA records.
*   **`read_swissprot_sequences()`**: Returns an iterator over Swiss-Prot records.
*   **`get_sequence_by_identifier(identifier)`**: helper to find a sequence by ID or index.

## `computation` Module

Handles computation jobs, specifically Tree Building.

### `ComputationJob` Class
*   **`run_computation(self)`**: Executes the computation logic (e.g., Tree Building).

## `sw_search` Module

Handles Smith-Waterman search jobs.

### `SwSearchJob` Class
*   **`run_search(self)`**: Executes the search, typically by invoking the `bin/sw_search_metal` executable.

## `tree_builder` Module

### `MaxSpanningTree` Class
*   **`add_link(self, node_a, node_b, score, ...)`**: Adds a link to the MST.
*   **`write_ascii_tree(self, output_file)`**: Exports the tree to an ASCII text file.
*   **`report_twilight(self, f)`**: Writes the "twilight zone" report (weak links).
