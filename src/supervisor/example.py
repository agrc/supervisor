#!/usr/bin/env python
# * coding: utf8 *
"""
An example implementation using Supervisor to catch an error and email both the traceback and the logfile
"""

import datetime
import logging
import logging.handlers
import socket
from pathlib import Path

from supervisor import secrets
from supervisor.message_handlers import EmailHandler, SendGridHandler
from supervisor.models import MessageDetails, Supervisor

if __name__ == '__main__':

    #: Set up a rotating file handler for the report log
    test_path = Path(r'd:\temp\supervisor_log.txt')
    test_logger = logging.getLogger('supervisor')
    test_handler = logging.handlers.RotatingFileHandler(test_path, backupCount=2)
    test_handler.doRollover()  #: Rotate the log on each run
    test_handler.setLevel(logging.DEBUG)
    test_logger.addHandler(test_handler)
    test_logger.setLevel(logging.DEBUG)

    #: Add somethign to the log
    test_logger.info(f'test run: {datetime.datetime.now()}')

    #: Instantiate a Supervisor object
    sim_sup = Supervisor(logger=test_logger, log_path=test_path)

    #: ============
    #: EmailHandler
    #: ============

    #: Specify the email server and addresses
    email_settings = {
        'smtpServer': 'send.state.ut.us',
        'smtpPort': 25,
        'from_address': 'noreply@utah.gov',
        'to_addresses': 'jdadams@utah.gov',
        'prefix': f'Example on {socket.gethostname()}: '
    }

    #: Instantiate a new EmailHandler and register it with our Supervisor
    # sim_sup.add_message_handler(EmailHandler(email_settings, 'agrc-supervisor'))

    #: ===============
    #: SendGridHandler
    #: ===============

    #: Specify the to/from addresses, subject prefix, and sendgrid API key
    sendgrid_settings = {
        'from_address': 'noreply@utah.gov',
        'to_addresses': 'jdadams@utah.gov',
        'prefix': f'Example on {socket.gethostname()}: ',
        'api_key': secrets.SENDGRID_API_KEY,
    }

    #: Instantiate a new SendGridHandler and register it with our Supervisor
    sim_sup.add_message_handler(SendGridHandler(sendgrid_settings, 'agrc-supervisor'))

    #: Send a message with both a directory attachment and a single file attachment
    message = MessageDetails()
    message.subject = '[Supervisor Example]'
    message.message = 'This is an example message\nwith a newline\nor two.'
    message.attachments = [r'd:\temp\agol_items_by_user', r'd:\temp\schools.csv']
    sim_sup.notify(message)

    #: Trigger Supervisor's error handler
    raise ValueError('random error here')
