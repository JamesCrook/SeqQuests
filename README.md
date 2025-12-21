# SeqQuests

SeqQuests is a sequence analysis package with a server and client interface.

SeqQuests provides:
* A very fast metal-accelerated Smith-Waterman local similarity search (2 days for 570,000 sequences all-on-all on Mac M4 Pro)
* Tooling for making, browsing and reducing an all-on-all Swissprot protein sequence comparison 
* LCARs (Star Trek TNG) inspired web user interface for protein sequence work.

The code can be run via CLI/bash without using the web UI. However, the web UI makes exploring results easier, by dynamically making alignments, ~~feature maps, and dotplots~~. The server also supports a user interface for jobs. You can create, configure, start, stop and delete jobs, and monitor their progress.

## Project Structure

```
/
├─ c_src/            # C++ and Metal source code for accelerated computations.
├─ data/             # Small sample data files for development (not full data files)
├─ results/          # Selected results found using the search
├─ py/               # Python source code for the application logic and web server.
├─ docs/             # User documentation
│  ├─ explanations/  # SeqQuest splits explanations into for-users and for-devs
│  ├─ how-to/        # Recipes organised by related topics
│  ├─ reference/     # Machine generated manual for the various programs 
│  └─ tutorials/     # Tutorial content, progressing from foundations to special case uses.
└─ static/           # Static assets for the web interface (HTML, CSS, JavaScript).
```

C++/Objective-C provides accelerated versions of code that needs to be fast.

The web UI uses API-endpoints provided by a FastAPI web server. The web UI falls back to using static files and sample data if the API endpoint is not available.

## Getting started

See /GETTING_STARTED.md in this directory and /docs/tutorials/getting_started.md for instructions on getting started.

## Links for AI Assistants
Much of the code was created with AI assistance. One example of this is that the tree of protein relatedness was created as a big text file. An AI assistant then provided a web interface for viewing this file, highlighting different parts in colour, searching it, navigating up and down the tree. The plain file can still be viewed in just a text editor, but the decorated version is much easier to use. 

AI assistants were also used in conversations that progressed a slow database search into a fast one. They are guided to instructions they should follow by text like the text below:

See `/docs/reference/specs/specs.md` for IMPORTANT REQUIREMENTS for AI assistant work.

