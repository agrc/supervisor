# agrc/python

![Build Status](https://github.com/agrc/supervisor/workflows/Build%20and%20Test/badge.svg)
<!-- [![codecov](https://codecov.io/gh/agrc/python/branch/main/graph/badge.svg)](https://codecov.io/gh/agrc/python) -->

A module for watching over scheduled processes: catching errors and sending messages for errors and/or summary logs.

## Rationale

supervisor provides a framework for scripts scheduled through Windows' Task Scheduler to report any errors and/or any logs via the handlers in `messaging.py`. Task Scheduler's built-in email tools require an email server running on the machine(?) and can't handle custom targets like Slack.

- Redirects exception handling to a custom handler
- Provides custom messaging handler to direct errors and any other end-of-script output to e-mail and Slack
  - Works with any SMTP server supported by Python's `smtp` library
- Binds messaging settings and credentials to project (maybe not the best thing? Still have to change them project-by-project, but they will be in a consistent location in each project)

## Usage

1. Set up your working environment
   - `conda activate PROJECT_NAME`
   - `cd c:\root\path\where\you\store\your\code` (ie, `cd c:\gis\git`)
1. Clone the repo and install
   - `git clone https://github.com/agrc/supervisor`
   - `cd supervisor`
   - `pip installe -e .`
1. In your script's entry point code (usually `main.py`), before any arg parsing:
   - Create an `SMTP` object using the proper email server settings
   - Instantiate a `Supervisor` object, passing in your `SMTP` object
   - Call `.manage_exceptions()` on the `Supervisor` object to redirect exception handling
1. Call `.send_report()` on the `Supervisor` object after your business logic:
   - In `main.py` (or wherever you instantiated the object), passing the message and path to the log file
   - —OR—
   - Elsewhere in your business logic, having passed your `Supervisor` object through your logic as needed.

## Development Environment

1. Create new development conda environment
   - `conda create --clone arcgispro-py3 --name supervisor_dev`
1. Clone the repo
   - `git clone https://github.com/agrc/supervisor`
1. Install in development mode
   - `cd supervisor`
   - `pip install -e ".[tests]"`
