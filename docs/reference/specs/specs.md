# Specs

* separation of concerns is of the utmost importance in this software, and this leads to some of the other principles
* web_server.py should be kept as a thin wrapper over the other functions, so as to facilitate testing without requiring the web server.
* sequences.py should insulate other modules from knowing what file the sequences come from and their underlying format. When initialised, it should check availability at its configured path and if not fall back to using the data in /data
* html and javascript should be in actual files in /static and not mixed in with python code
* javascript should be in its own .js file, not as functions embedded in html
* css should be in its own .css files, not embedded in html
* job_manager.py should not know what job specific parameters there are, only the generic ones like start and end time. Instead different types of job should handle their own state data.

* do not introduce new third party js dependencies
* when new python modules are added, update pyproject.toml