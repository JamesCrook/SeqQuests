# Getting Started with SeqQuests

SeqQuests is a sequence analysis package offering high-performance local similarity search (Smith-Waterman), tree building, and interactive data visualization.

## Prerequisites

### 1. Python Environment
*   **Python 3.8+**
*   **Dependencies:** Install via pip:
    ```bash
    pip install -r REQUIREMENTS.txt
    ```

### 2. Apple Metal (Optional but Recommended)
For accelerated Smith-Waterman searches, you need a macOS device with Apple Silicon (M1/M2/M3/M4) or a compatible GPU.
*   **Xcode Command Line Tools:** Ensure `clang` and `xcrun` are available.
*   **metal-cpp:** The project expects the `metal-cpp` headers to be located at `$HOME/metal-cpp`. You can download them from the [Apple Developer website](https://developer.apple.com/metal/cpp/).

## Installation

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd SeqQuests
    ```

2.  **Compile Native Binaries (macOS only):**
    If you have the prerequisites, compile the Metal search engine and C++ tree builder:
    ```bash
    ./compile.sh
    ```
    This will create executables in the `bin/` directory.

3.  **Prepare Data:**
    The system looks for Swiss-Prot data. By default, it expects:
    *   `/data/swissprot.dat.txt`
    *   `/data/swissprot.fasta.txt`

    *Note: The system also checks a user-specific path `/Users/jamescrook/BigData/bio_sequence_data`. You can configure your data location in `py/sequences.py` or ensure the default `/data` directory is populated.*

4.  **Prepare Binary Data (for Metal Search):**
    If using the Metal accelerator, you must generate the binary data files:
    ```bash
    PYTHONPATH=py python c_src/prepare_binary_data.py
    ```

## Running the Application

### Web Server (Dashboard)
The easiest way to use SeqQuests is via the web interface.

1.  **Start the Server:**
    Run the following command from the project root:
    ```bash
    PYTHONPATH=py python py/web_server.py
    ```

2.  **Access the Dashboard:**
    Open your browser and navigate to:
    [http://localhost:8000](http://localhost:8000)

    From here you can:
    *   Create and manage jobs.
    *   View documentation (`/docs`).
    *   Explore match results.

### Command Line Usage
You can run individual components directly.

*   **Tree Builder:**
    ```bash
    PYTHONPATH=py python py/tree_builder.py --help
    ```

*   **Data Integrity Check:**
    ```bash
    PYTHONPATH=py python py/check_fasta_integrity.py
    ```

## Testing

The project uses bespoke verification scripts rather than a standard test runner.

*   **Run Integrity Checks:**
    ```bash
    PYTHONPATH=py python py/check_fasta_integrity.py --test
    ```

*   **Verify Data Filters:**
    ```bash
    PYTHONPATH=py python py/verify_data_filters.py
    ```
