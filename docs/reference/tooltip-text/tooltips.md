# Tooltip Text

SeqQuest has tooltips built in to the ui. 'Help' will show arrows indicating what the different parts of the user interface do and are for. These are used both in-program and for the user documentation. Images from the UI are captured using playwright, and include these tooltips.

The tooltips are stored as JSON files, text describing different UI elements and then object identifiers that pick out the relevant DOM element from the html. 

This directory contains the JSON files that have the DOM element identifiers and the associated text.

One detail is that the tooltips can also mark up text within a text box. This is helpful as the CLI tools create text that has structure. The tooltip annotations can therefore mark up the structured text to explain what the different items in the text mean. For example, in 'hit' text showing similarities between items `(s:330)` means that two items have a similarity score of 330 - usually too strong to just be chance matching. In SwissProt datafile text a line starting with `FT` is a feature line, and the text that follows describes what kind of feature and where in the protein the feature is.

These JSON files are machine readable, for the program rather than for users, but developers should be able to relate the UI elements to the tooltip text and add to the collection as the tools are developed.