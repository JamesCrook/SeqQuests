# SeqQuests

SeqQuests is a sequence analysis package with a server and client interface.

A FastAPI web server presents an interface to python and binary workers, which appear as jobs in the user interface. You can create, configure, start, stop and delete jobs, and monitor their progress.

It provides:
* A very fast metal-accelerated NWS local similarity search
* A utility for making a filtered FastA dataset

## Project Structure

```
/
├── c_src/      # C and Metal source code for accelerated computations.
├── data/       # Small sample data files for development (not full data files)
├── docs/       # Project documentation.
├── metal/      # Python version of metal code, now superseded by the /c-src versions
├── py/         # Python source code for the application logic and web server.
├── specs/      # Project specification (for robots and AI to read).
├── static/     # Static assets for the web interface (HTML, CSS, JavaScript).
└── test/       # Test scripts and resources.
```
