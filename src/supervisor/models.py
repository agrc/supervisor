"""
This module holds the classes used by supervisor
"""

import os
import sys
import traceback

from .message_handlers import MessageHandler


class Supervisor:
    """Captures exceptions and sends these and other notifications via email or other methods.

    Attributes
    ----------
    project_name : str
        The name of the client project using Supervisor; used to report version in global exception handler messages
    message_handlers : [MessageHandler]
        Notifications will be sent via all handlers in this list
    logger : Logger
        Logger object to use in global exception handler
    log_path : Path
        Path to the logfile

    Methods
    -------
    add_message_handler(handler)
        Register a new handler for sending messages
    notify(message)
        Send a notification to all registered handlers
    _manage_exceptions
        Closure around a replacement for sys.excepthook
    """

    def __init__(self, project_name, logger=None, log_path=None):

        #: Set up our list of MessageHandlers
        self.project_name = project_name
        self.message_handlers = []
        self.logger = logger
        self.log_path = log_path

        #: Catch any uncaught exception with our custom exception handler
        sys.excepthook = self._manage_exceptions()

    def add_message_handler(self, handler: MessageHandler):
        """Register a new handler for sending messages

        Parameters:
        -----------
        handler : MessageHandler
            A MessageHandler instance for the desired notification method.
        """
        self.message_handlers.append(handler)

    def notify(self, message):
        """Send a notification to all registered handlers by calling .send_message()"""
        for handler in self.message_handlers:
            handler.send_message(message)

    def _manage_exceptions(self):
        """Closure around a replacement for sys.excepthook

        A closure ensures global_exception_handler() has access to self.notify to send notifications while still
        maintaining the signature required by sys.excepthook
        """

        def global_exception_handler(exc_class, exc_object, tb):  # pylint: disable=invalid-name
            """Send a notification via self.notify on any uncaught exceptions; log if client provided a Logger

            Parameters
            ----------
            exc_class : Type
                The type of the exception
            exc_object : Exception
                The exception object
            tb : Traceback
                Original traceback

            Used to handle any uncaught exceptions. Formats an error message, logs it, and sends an email.
            """

            error = os.linesep.join(traceback.format_exception(exc_class, exc_object, tb))

            if self.logger:
                last_traceback = (traceback.extract_tb(tb))[-1]
                line_number = last_traceback[1]
                file_name = last_traceback[0].split('.')[0]
                self.logger.error(f'global error handler line: {line_number} ({file_name})')  # pylint: disable=logging-fstring-interpolation
                self.logger.error(error)

            message_details = MessageDetails()
            message_details.message = error
            message_details.subject = 'ERROR'
            message_details.log_file = self.log_path
            message_details.project_name = self.project_name
            self.notify(message_details)

        return global_exception_handler


class MessageDetails:  # pylint: disable=too-few-public-methods
    """Data structure for message details to allow dot-access and null item checks.

    Attributes
    ----------
    message : str
        The text of the message
    attachment : list
        Strings or Paths to any attachments
    log_file : Path
        Path to an on-disk log file
    subject : str
        The message subject
    project_name : str
        The name of the project that has added the Supervisor object. Used for adding the version to notifications.

    TODO: Implement true Null-Object pattern.
    """

    def __init__(self):
        self.message = ''
        self.attachments = []  #: Strings or Paths
        self.log_file = None  #: Path
        self.subject = ''
        self.project_name = ''
