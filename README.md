# agrc/python

![Build Status](https://github.com/agrc/supervisor/workflows/Build%20and%20Test/badge.svg)
<!-- [![codecov](https://codecov.io/gh/agrc/python/branch/main/graph/badge.svg)](https://codecov.io/gh/agrc/python) -->

A module for watching over scheduled processes: catching errors and sending messages for errors and/or summary logs.

## Rationale

supervisor provides a framework for scripts scheduled through Windows' Task Scheduler to send messages via the handlers in `message_handlers.py`. The messages can include gziped log files, progress reports, or execution summaries. The message handlers provide access to email, slack, and any other custom handler. These reporting methods are not supported by Task Scheduler. It also sends any uncaught exceptions via the registered message handlers.

- Redirects exception handling to a custom handler
- Provides custom messaging handler to direct errors and any other end-of-script output to e-mail and (eventually) Slack
  - Works with any SMTP server supported by Python's `smtp` library
  - Works with the SendGrid email API
- Binds messaging settings and credentials to project (maybe not the best thing? Still have to change them project-by-project, but they will be in a consistent location in each project)

## Usage

See `api.md` for an in-depth description of Supervisor and how it's used.

1. Set up your working environment
   - `conda activate PROJECT_NAME`
   - `cd c:\root\path\where\you\store\your\code` (ie, `cd c:\gis\git`)
1. Install supervisor (or add to your project's `setup.py`)
   - `pip install agrc-supervisor`
1. In your script's entry point code (usually `main.py`), as early as possible and generally before any arg parsing:
   - (Optional) Set up a logger, which is used to log any errors your code doesn't handle and `Supervisor` catches.
   - Instantiate a `Supervisor` object, passing the optional logger.
   - Instantiate and register the desired `MessageHandler`s with the `Supervisor Object`
      - Create the appropriate settings dictionaries before creating the `MessageHandler`s
1. Build a `MessageDetails` object with subject, message (as a single string), and optional attachments.
1. Call `.notify()` on the `Supervisor`:
   - In `main.py` (or wherever you instantiated the `Supervisor` object), passing in the MessageDetails object
   - —OR—
   - Elsewhere in your business logic, having passed your `Supervisor` object through your logic and building `MessageDetail` objects as needed.
1. After instantiation, the `Supervisor` object will direct all errors to its custom error handler. This will send messages to every registered handler whenever an error occurs.

## Example Code

```python
import logging
from logging.handlers import RotatingFileHandler

from supervisor.message_handlers import ConsoleHandler, SendGridHandler
from supervisor.models import MessageDetails, Supervisor

my_logger = logging.getLogger('my_project')
log_handler = RotatingFileHandler(r'c:\log.log'), backupCount=10)
my_logger.addHandler(log_handler)

supervisor = Supervisor(logger=my_logger, log_path=r'c:\log.log')
sendgrid_settings = {
   'from_address': 'me@utah.gov',
   'to_address': 'you@utah.gov',
   'api_key': 'its_a_secret!',
}
supervisor.add_message_handler(SendGridHandler(sendgrid_settings=sendgrid_settings, project_name='my_project'))
supervisor.add_message_handler(ConsoleHandler())

#: Do your stuff here...
outcome = my_project.do_things()

summary_message = MessageDetails()
summary_message.subject = 'my_project Update Summary'
summary_message.message = '\n'.join([f'my_project run at {datetime.datetime.now()}', f'Outcome: {outcome}'])
summary_message.attachments = r'c:\log.log'

supervisor.notify(summary_message)
```

## Development Environment

1. Create new development conda environment
   - `conda create --clone arcgispro-py3 --name supervisor_dev`
1. Clone the repo
   - `git clone https://github.com/agrc/supervisor`
1. Install in development mode
   - `cd supervisor`
   - `pip install -e ".[tests]"`

## Update pypi

1. Delete everything in `dist/`
1. Make sure you've updated the version number in `setup.py`
1. Recreate the wheels:
   - `python setup.py sdist bdist_wheel`
1. Re-upload the new files
   - `twine upload dist/*`
