"""
This module holds the classes used by supervisor
"""

import os
import sys
import traceback
from abc import ABC, abstractmethod
from enum import Enum
from json import dumps

from .message_handlers import MessageHandler

#: Slack Block Kit constants
MAX_BLOCKS = 50
MAX_CONTEXT_ELEMENTS = 10
MAX_SECTION_FIELD_ELEMENTS = 10
MAX_LENGTH_SECTION = 3000
MAX_LENGTH_SECTION_FIELD = 2000


def split_blocks(arr, size):
    """Split an array into chunks of specified size
    
    Parameters
    ----------
    arr : list
        Array to split
    size : int
        Size of each chunk
        
    Returns
    -------
    list
        List of chunks
    """
    result = []
    while len(arr) > size:
        piece = arr[:size]
        result.append(piece)
        arr = arr[size:]

    result.append(arr)

    return result


class BlockType(Enum):
    """Available block type enums for Slack Block Kit"""

    SECTION = "section"
    DIVIDER = "divider"
    CONTEXT = "context"


class Block(ABC):
    """Base block containing attributes and behavior common to all blocks
    
    Block is an abstract class and cannot be sent directly.
    """

    def __init__(self, block):
        self.type = block

    def _attributes(self):
        return {"type": self.type.value}

    @abstractmethod
    def _resolve(self):
        """Resolve the block to a dictionary for Slack API"""

    def __repr__(self):
        return dumps(self._resolve(), indent=2)


class Text:
    """A text class formatted using Slack's markdown syntax"""

    def __init__(self, text):
        self.text = text

    def _resolve(self):
        text = {
            "type": "mrkdwn",
            "text": self.text,
        }

        return text

    @staticmethod
    def to_text(text, max_length=None):
        """Convert text to Text object with optional length limit
        
        Parameters
        ----------
        text : str
            Text to convert
        max_length : int, optional
            Maximum length for the text
            
        Returns
        -------
        Text
            Text object
        """
        if max_length and len(text) > max_length:
            text = text[:max_length]

        return Text(text=text)

    def __str__(self):
        return dumps(self._resolve(), indent=2)


class SectionBlock(Block):
    """A section is one of the most flexible blocks available"""

    def __init__(self, text=None, fields=None):
        super().__init__(block=BlockType.SECTION)
        self.fields = []
        self.text = None

        if text is not None:
            self.text = Text.to_text(text, MAX_LENGTH_SECTION)
        if fields and len(fields) > 0:
            self.fields = [Text.to_text(field, MAX_LENGTH_SECTION_FIELD) for field in fields]

    def _resolve(self):
        section = self._attributes()

        if self.text:
            section["text"] = self.text._resolve()

        if self.fields and len(self.fields) > 0:
            section["fields"] = [field._resolve() for field in self.fields]

        return section


class ContextBlock(Block):
    """Displays message context. Typically used after a section"""

    def __init__(self, elements):
        super().__init__(block=BlockType.CONTEXT)

        self.elements = []

        for element in elements:
            self.elements.append(Text.to_text(element, MAX_LENGTH_SECTION_FIELD))

        if len(self.elements) > MAX_CONTEXT_ELEMENTS:
            raise ValueError("Context blocks can hold a maximum of ten elements")

    def _resolve(self):
        context = self._attributes()
        context["elements"] = [element._resolve() for element in self.elements]

        return context


class DividerBlock(Block):
    """A content divider like an <hr>"""

    def __init__(self):
        super().__init__(block=BlockType.DIVIDER)

    def _resolve(self):
        return self._attributes()


class Supervisor:
    """Captures exceptions and sends these and other notifications via email or other methods.

    Attributes
    ----------
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

    def __init__(self, handle_errors=True, logger=None, log_path=None):
        #: Set up our list of MessageHandlers
        self.message_handlers = []
        self.logger = logger
        self.log_path = log_path

        #: Catch any uncaught exception with our custom exception handler if desired
        if handle_errors:
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
                file_name = last_traceback[0].split(".")[0]
                self.logger.error(f"global error handler line: {line_number} ({file_name})")  # pylint: disable=logging-fstring-interpolation
                self.logger.error(error)

            message_details = MessageDetails()
            message_details.message = error
            message_details.subject = "ERROR"
            message_details.attachments = [self.log_path]
            self.notify(message_details)

        return global_exception_handler


class MessageDetails:  # pylint: disable=too-few-public-methods
    """Data structure for message details to allow dot-access and null item checks.

    Attributes
    ----------
    message : str
        The text of the message
    attachment : list
        Strings or Paths to any attachments, including log files
    subject : str
        The message subject
    slack_blocks : list
        List of Slack Block objects for SlackHandler

    TODO: Implement true Null-Object pattern.
    """

    def __init__(self):
        self.message = ""
        self._attachments = []  #: Strings or Paths
        self.subject = ""
        self._slack_blocks = []  #: List of Block objects

    @property
    def attachments(self):
        """List of paths of files to attach

        Returns:
            List: Attachment paths
        """
        return self._attachments

    @attachments.setter
    def attachments(self, value):
        if isinstance(value, list):
            self._attachments.extend(value)

        else:
            self._attachments.append(value)

    @property
    def slack_blocks(self):
        """List of Slack Block objects

        Returns:
            List: Slack Block objects
        """
        return self._slack_blocks

    @slack_blocks.setter
    def slack_blocks(self, value):
        if isinstance(value, list):
            self._slack_blocks.extend(value)
        else:
            self._slack_blocks.append(value)
