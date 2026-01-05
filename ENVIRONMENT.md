# Environment

* Apple silicon is required for the fast Smith-Waterman search. It isn't required for browsing the results.

* See .env.example and make your own paths, in .env. You should set environment variables such as:

```bash
SEQQUESTS_DATA_DIR=~/data/seqquests
METAL_CPP_PATH=~/metal
```

* SeqQuests runs from the top level directory of the repo. Rather than descend into /py/, run python scripts like so:
```bash
python py/web_server.py
```

* Various tools are used in making SeqQuests.

|Tool|Purpose|
|----|-------|
|XCode|Compilation of SW search and wasm code for in-browser alignments|

AI Should add other reuqired tools to the table.

I use Brew to install some of these tools.