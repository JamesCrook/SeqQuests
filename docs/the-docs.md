
# The Docs

SeqQuest is based on the diátaxis framework for documentation:
* **explanations** - why the software is the way it is, assumptions/limitations/rationale
* **how-to** - short recipes for specific tasks such as converting formats
* **reference** - command line options and APIs
* **tutorials** - linear step by step paths using tiny datasets.

```
/
├─ explanations/       # SeqQuest splits explanations into two audiences:
│  ├─ for-developers/  # 1) C++/Metal/Python/Javascript details
│  └─ for-users/       # 2) Details of purpose/motivation/capabilities
├─ how-to/             # Recipes organised by related topics
├─ reference/          # Machine generated manual for the various programs 
│  ├─ specs/           # Instructions for AI coding assistants
│  └─ tooltip-text/    # Additional prompts/tips that appear in the program
└─ tutorials/          # Tutorial content, progressing from foundations to special case uses.
```

New users should start with /docs/tutorials/getting_started.md

There is a much more condensed version of that document at /GETTING_STARTED.md