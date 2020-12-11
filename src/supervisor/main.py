#!/usr/bin/env python
# * coding: utf8 *
"""
a description of what this module does.
this file is for testing linting...
"""

import logging
import logging.handlers
from pathlib import Path

from supervisor.message_handlers import EmailHandler
from supervisor.models import Supervisor

TEST = 'test'


def hello():
    """doc string
    """
    print('this is good')

    print(
        'this is a really, really, really, really, really, really, really, really, really, really, really, really,'
        'really long line'
    )

    return 'hi'


if __name__ == '__main__':
    #: the code that executes if you run the file or module directly
    GREETING = hello()

    #: Set up a rotating file handler for the report log
    test_path = Path(r'c:\temp\supervisor_log.txt')
    test_logger = logging.getLogger('supervisor')
    test_handler = logging.handlers.RotatingFileHandler(test_path, backupCount=2)
    test_handler.doRollover()  #: Rotate the log on each run
    test_handler.setLevel(logging.DEBUG)
    test_logger.addHandler(test_handler)
    test_logger.setLevel(logging.DEBUG)

    test_logger.info('test run')

    sim_sup = Supervisor('supervisor', test_path)
    email_settings = {
        'smtpServer': 'send.state.ut.us',
        'smtpPort': 25,
        'from_address': 'noreply@utah.gov',
        'to_addresses': 'jdadams@utah.gov',
    }
    sim_sup.add_message_handler(EmailHandler(email_settings))

    raise ValueError('random error here')
