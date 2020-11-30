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

    def __init__(self):

        #: Set up our list of MessageHandlers and add a default ConsoleHandler
        self.message_handlers = []
        self.message_handlers.append(ConsoleHandler())

        #: Catch any uncaught exception with our custom exception handler
        self._manage_exceptions()

    def add_message_handler(self, handler: MessageHandler):
        """
        Adds a message handler to the list of handlers
        """
        self.message_handlers.append(handler)

    def notify(self, message, log_path):
        """
        Calls the .send_message() method on every handler
        """
        for handler in self.message_handlers:
            handler.send_message(message, log_path)

    def _manage_exceptions(self):

        log = logging.getLogger('forklift')

        # Nesting so that we have access to Supervisor's self object
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

            self.notify(error, log_file)

        sys.excepthook = global_exception_handler
