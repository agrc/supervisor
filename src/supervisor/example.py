#!/usr/bin/env python
# * coding: utf8 *
"""
An example implementation using Supervisor to catch an error and email both the traceback and the logfile
"""

import logging
import logging.handlers
import socket
from pathlib import Path

from supervisor.message_handlers import EmailHandler
from supervisor.models import Supervisor

if __name__ == '__main__':

    #: Set up a rotating file handler for the report log
    test_path = Path(r'c:\temp\supervisor_log.txt')
    test_logger = logging.getLogger('supervisor')
    test_handler = logging.handlers.RotatingFileHandler(test_path, backupCount=2)
    test_handler.doRollover()  #: Rotate the log on each run
    test_handler.setLevel(logging.DEBUG)
    test_logger.addHandler(test_handler)
    test_logger.setLevel(logging.DEBUG)

    #: Add somethign to the log
    test_logger.info('test run')

    #: Instantiate a Supervisor object
    sim_sup = Supervisor('supervisor', log=test_logger, log_path=test_path)

    #: Specify the email server and addresses
    email_settings = {
        'smtpServer': 'send.state.ut.us',
        'smtpPort': 25,
        'from_address': 'noreply@utah.gov',
        'to_addresses': 'jdadams@utah.gov',
        'prefix': f'Example on {socket.gethostname()}: '
    }

    #: Instantiate a new EmailHandler and register it with our Supervisor
    sim_sup.add_message_handler(EmailHandler(email_settings))

    #: Trigger Supervisor's error handler
    raise ValueError('random error here')
