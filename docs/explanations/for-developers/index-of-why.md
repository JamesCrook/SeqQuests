# (For developers) Index of Why

This code is extensively developed with AI help.

AI tends to write code in a verbose fashion, and it tends to struggle as the code base gets large.

The shape of the code has adapted to this. I constantly look for ways to fold code into more generic subroutines that are smaller. Separation of concerns becomes paramount, so that the AI can focus its context on a small piece of the overall code.

This AI force is also behind the CLI/GUI separation. Every workhorse command needs to have a python script. It needs to be runnable from CLI. This makes documentation much easier - the commands can all have man-pages for their argparse-like command lines. Anyone working with the heavy lifting code can do so all in scripted pipelines.

In python I readily use python libraries and their ecosystem. For C++ and javascript as much as possible I avoid third party libraries. This means that all the adaptation layers happen in python which is singularly good at it. AI also struggles less with understanding existing python than with understanding a javascript/html UI. 

## The Index

* [Smith-Waterman core](./smith-waterman-speed.md) - How the speed is achieved in the smith-waterman algorithm.
* [New widgets](./new-widgets.md) - Unifying different widgets, d3.js style
* [Python, JavaScript, C++, Who cares?](./code-translation.md) - Why AI encourages 'the same code' in different formats.