

# Main all-on-all Pipeline
* [compile.sh](/reference/compiling.md) - Compile the fast code
* [get_uniprot.sh](/reference/get-uniprot.md) - Download the uniprot datafiles from their site
* [pam_converter.py](/reference/pam-converter.md) - Produce binary version of match matrix
* [prepare_binary_data.py](/reference/pam-converter.md) - Prepare binary version of database
* [sw_search.py](/reference/sw-search.md) - Do the all-on-all search
* [tree_builder.py](/reference/tree-builder.md) - Reduce the search results using maximum scoring tree
* [filter-twilight.py](/reference/filter-twilight.md) - Reduce the maximum scoring tree by excluding some hits

# Additional CLI Tools
* [swiss-to-pdb.py](/reference/swiss-to-pdb.md) - Get from swissprot identifier to pdb identifier
* [kabsch-3d-align.py](/reference/kabsch-3d-align.md) - 

# Web UI

* [command_wrapper](/reference/command-wrapper.md) - A wrapper that turns a text-generating program into a schedulable job that can be paused and restarted and that can be configured via the web and report specific progress to the web UI.
* [job_manager.py](/reference/job-manager.md) - Interface between wrapped programs and scripts and the actual job launching web interface.
* [web_server.py](/reference/web-server.md) - The FastAPI based web-server that serves the bioinformatics web pages.
