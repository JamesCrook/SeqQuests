# Web Server Task Manager

The `web_server.py` script launches a web-based user interface for managing and monitoring bioinformatics jobs. It is built using the FastAPI framework, providing a robust RESTful API for interacting with the job management system.

## Core Functionality

The web server acts as a central control panel for various processing tasks, including `data_munger` and `nws_search`. It allows users to create, configure, and monitor the progress of these jobs through a simple web interface.

## Job Lifecycle Management

The UI provides a complete set of controls for managing the lifecycle of a job:

-   **Configure:** Each job type has a dedicated configuration page where users can set parameters before starting a job.
-   **Start:** Initiates a configured job, which will begin processing in the background.
-   **Pause & Resume:** Jobs can be temporarily paused and later resumed, allowing for flexible control over resource usage.
-   **Delete:** Removes a job from the system, cleaning up any associated data and state.

## Progress Monitoring

The web interface provides two levels of detail for monitoring job progress:

1.  **Job List (Summary View):** The main dashboard displays a list of all jobs. For each job, a concise **progress string** is shown, providing a quick, at-a-glance status update (e.g., "Processing sequence 100/1000").
2.  **Job Details (Detailed View):** When a user selects a specific job, a more detailed information panel is displayed. This view provides richer, job-specific output, such as the last ten items found or detailed logs.

## Real-time UI Feedback with `pty`

A key feature for long-running command-line jobs like `nws_search` is the use of a pseudo-terminal (`pty`). Standard command-line tools often buffer their output, meaning they only send updates in large, infrequent chunks. This can make the UI feel unresponsive.

By running the `nws_search` process within a `pty`, the web server can capture its output character-by-character, as it is generated. This allows the server to stream results to the web interface in real-time, providing a much more responsive and informative user experience without delays from line buffering.
