"""
This module holds the classes used by supervisor
"""

import logging
import os
import sys
import traceback

from .message_handlers import ConsoleHandler, MessageHandler


class Supervisor:
    """
    Primary class; has the replacement error handler and a Messenger object to handle messaging
    """

    def __init__(self, project_name):

        #: Set up our list of MessageHandlers and add a default ConsoleHandler
        self.project_name = project_name
        self.message_handlers = []
        self.message_handlers.append(ConsoleHandler())

        #: Catch any uncaught exception with our custom exception handler
        sys.excepthook = self._manage_exceptions()

    def add_message_handler(self, handler: MessageHandler):
        """
        Adds a message handler to the list of handlers
        """
        self.message_handlers.append(handler)

    def notify(self, message):
        """
        Calls the .send_message() method on every handler
        """
        for handler in self.message_handlers:
            handler.send_message(message)

    def _manage_exceptions(self):
        """
        A closure so that global_exception_handler() has access to self.notify to send notifications while still
        maintaining the signature required by sys.excepthook
        """

        log = logging.getLogger(self.project_name)

        def global_exception_handler(exc_class, exc_object, tb):  # pylint: disable=invalid-name
            """
            exc_class: the type of the exception
            exc_object: the exception object
            tb: Traceback

            Used to handle any uncaught exceptions. Formats an error message, logs it, and sends an email.
            """

            last_traceback = (traceback.extract_tb(tb))[-1]
            line_number = last_traceback[1]
            file_name = last_traceback[0].split('.')[0]
            error = os.linesep.join(traceback.format_exception(exc_class, exc_object, tb))

            log.error(f'global error handler line: {line_number} ({file_name})')  # pylint: disable=logging-fstring-interpolation
            log.error(error)

            log_file = None  # join(dirname(config.config_location), 'forklift.log')
            # messaging.send_email(config.get_config_prop('notify'),
            # f'Forklift Error on {socket.gethostname()}', error, [log_file])
            message_details = {'message': error, 'subject': f'{self.project_name}: ERROR', 'log_path': log_file}
            self.notify(message_details)

        return global_exception_handler


class MessageDetails:  # pylint: disable=too-few-public-methods
    """
    Data structure for message details to allow dot-access and null item checks.

    TODO: Implement true Null-Object pattern.
    """

    def __init__(self):
        self.message = ''
        self.attachments = []  #: Strings or Paths
        self.log_file = None  #: Path
        self.subject = ''
        self.project_name = ''
