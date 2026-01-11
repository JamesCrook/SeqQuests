
# The Docs

SeqQuests documentation is based on the diátaxis framework:
* **explanations** - why the software is the way it is, assumptions/limitations/rationale
* **how-to** - short recipes for specific tasks such as converting formats
* **reference** - command line options and APIs
* **tutorials** - linear step by step paths using tiny datasets.

I'm working on a nice interface for finding information in the docs. In the meantime, browse them at GitHub <a href="https://github.com/JamesCrook/SeqQuests/tree/master/docs" target="_">⮕⮕⮕ CLICK HERE ⬅⬅⬅</a>

```
/
├─ explanations/       # SeqQuests splits explanations into two audiences:
│  ├─ for-developers/  # 1) C++/Metal/Python/Javascript details
│  └─ for-users/       # 2) Details of purpose/motivation/capabilities
├─ how-to/             # Recipes organised by related topics
├─ reference/          # Machine generated manual for the various programs 
│  ├─ specs/           # Instructions for AI coding assistants
│  └─ tooltip-text/    # Additional prompts/tips that appear in the program
└─ tutorials/          # Tutorial content, progressing from foundations to special case uses.
```

The [GETTING_STARTED](../GETTING_STARTED.md) doc is the best place for developers, people expected to read and work with the source code. [Getting Started](tutorials/getting-started.md) is a work in progress for new users, for when the software is ready for that.

* The reference section is the most complete part of the documentation currently.

## Explanations

Developers have a separate [index of explanations](./explanations/for-developers/index-of-why.md)

* [Overview](./explanations/overview.md) - An overview of the whole SeqQuests system, explaining what it can do and the existing pipelines.
* [Why Smith-Waterman alignment?](./explanations/for-users/why-sw.md) - What kinds of similarities it does and does not find. 
* [Exploring the Twilight Zone](./explanations/for-users/twilight-zone.md) - How some scores are 'boosted'. Looks at proteins with biased sequence composition, and sequences with repetitive motifs. 
* [Using AI to help interpret results](./explanations/for-users/ai-interpret.md) - Why AI struggles to make discoveries. What it is good for, and where relying on it gets in the way.
* [Why Star Trek?](./explanations/for-users/why-star-trek.md) - Why does SeqQuests have a star-trek (TNG) like UI?

## How To

* [All-On-All comparison of your own protein data](./how-to/all-on-all.md).
* [Use a domain-comparison chart in a publication](./how-to/domains-to-svg.md).

## Reference

The [reference](./reference/index-of-reference.md) pages have sections on the main pipeline, the CLI tools and the commands that make the web UI.

## Tutorials

Step by step guides:

* [Getting Started](tutorials/getting-started.md) - The best place to start.
* [Using Help](./tutorials/using-help.md) - There is some built in help in the program, but to get the most from SeqQuests you need to read the docs. This document shows you how to use the built-in help
* [Multiscrollers](./tutorials/multiscrollers.md) - A user interface feature for navigating large quantities of information. This document shows you how to use multiscrollers.

