# SeqQuests

SeqQuests is a sequence analysis package with a server and client interface.

A FastAPI web server presents an interface to python and binary workers, which appear as jobs in the user interface. You can create, configure, start, stop and delete jobs, and monitor their progress.

It provides:
* A very fast metal-accelerated NWS local similarity search
* A utility for making a filtered FastA dataset