
# The Docs

SeqQuest documentation is based on the diátaxis framework:
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

The [Getting Started](tutorials/getting-started.md) doc is the best place to start for new users. There is a much terser version, [GETTING_STARTED](../GETTING_STARTED.md) for developers who are expected to read the source code.

## Explanations

Developers have a separate [index of explanations](./explanations/for-developers/index-of-why.md)

* [Overview](./explanations/overview.md) - An overview of the whole SeqQuest system, explaining what it can do and the existing pipelines.
* [Why Smith-Waterman alignment?](./explanations/why-sw.md) - What kinds of similarities it does and does not find. 
* [Exploring the Twilight Zone](./explanations/twilight-zone.md) - How some scores are 'boosted'. Looks at proteins with biassed sequence composition, and sequences with repetitive motifs. 
* [Using AI to help interpret results](./explanations/ai-interpret.md) - Why AI struggles to make discoveries. What it is good for, and where relying on it gets in the way.
* [Why Star Trek?](./explanations/why-star-trek.md) - Why does SeqQuest have a star-trek (TNG) like UI?

## How To

* [All-On-All comparison of your own protein data](./how-to/all-on-all.md).
* [Use a domain-comparison chart in a publication](./how-to/domains-to-svg.md).

## Reference

The [reference](./reference/index-of-reference.md) pages have sections on the main pipeline, the CLI tools and the commands that make the web UI.

## Tutorials

Step by step guides:

* [Getting Started](tutorials/getting-started.md) - The best place to start.
* [Using Help](./tutorials/using-help.md) - There is some built in help in the program, but to get the most from SeqQuest you need to read the docs. This document shows you how to use the built-in help
* [Multiscrollers](./tutorials/multiscrollers.md) - A user interface feature for navigating large quantities of information. This document shows you how to use multiscrollers.

## Suggested Additions

* **Tutorials**:
    *   **Analyzing Results**: A guide on how to interpret the results of a sequence search.
    *   **Customizing the UI**: How to customize the interface to suit your needs.
* **How-To**:
    *   **Converting Data Formats**: How to convert common bioinformatics formats for use with SeqQuest.
    *   **Running on a Remote Server**: Setting up SeqQuest on a remote server.
