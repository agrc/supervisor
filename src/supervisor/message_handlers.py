"""
message_handlers.py: Holds all the different message handlers
"""

from abc import ABC, abstractmethod


class MessageHandler(ABC):  # pylint: disable=too-few-public-methods
    """
    Base class for all message handlers.
    """

    @abstractmethod
    def send_message(self, message, log_path):
        """
        Send a notification using the target-specific logic (email, slack, etc)
        """


class EmailHandler(MessageHandler):  # pylint: disable=too-few-public-methods
    """
    Send emails via the provided SMTP object
    """

    def __init__(self, smtp):
        pass

    def send_message(self, message, log_path):
        pass


class SlackHandler(MessageHandler):  # pylint: disable=too-few-public-methods
    """
    Send a notification to Slack
    """

    def __init__(self, details):
        pass

    def send_message(self, message, log_path):
        pass


class ConsoleHandler(MessageHandler):  # pylint: disable=too-few-public-methods
    """
    Print output to the console
    """

    def send_message(self, message, log_path=None):
        print(message)
