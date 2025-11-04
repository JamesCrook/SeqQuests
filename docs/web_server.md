# Web Server Task Manager

The `web_server.py` script launches a web-based user interface for managing and monitoring bioinformatics jobs. It is built using the FastAPI framework which provides a RESTful API.

## Core Functionality

The web server acts as a central control panel for `data_munger` and `nws_search`. It allows users to create, configure, and monitor the progress of these jobs through the web interface.

-   **Configure:** Each job type has a configuration page where users can set and view parameters.
-   **Start:** Initiates a configured job.
-   **Pause & Resume:** Jobs can be temporarily paused and later resumed.
-   **Delete:** Removes a job from the system.

## Progress Monitoring

The web interface provides two levels of detail for monitoring job progress:

1.  **Job List (Summary View):** The dashboard displays a list of all jobs. For each job, a concise **progress string** is shown, providing an at-a-glance status update (e.g., "Processing sequence 100/1000").
2.  **Job Details (Detailed View):** When a user selects a specific job, more detailed information for that job is shown below the job list, for example the last ten lines of output.

## Real-time UI Feedback with `pty`

Standard command-line tools accessed through a pipe will buffer their output and only send updates in large, infrequent chunks. This can make the UI unresponsive.

By running the `nws_search` process within a `pty`, the web server can capture its output character-by-character, as it is generated. This avoids delays from buffering multiple lines.
