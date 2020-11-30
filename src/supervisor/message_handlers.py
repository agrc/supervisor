"""
message_handlers.py: Holds all the different message handlers
"""

from abc import ABC, abstractmethod


class MessageHandler(ABC):
    """
    Base class for all message handlers.
    """

    @abstractmethod
    def send_message(self, message, log_path):
        pass


class EmailHandler(MessageHandler):
    """
    Send emails via the provided SMTP object
    """

    def __init__(self, smtp):
        pass

    def send_message(self, message, log_path):
        pass


class SlackHandler(MessageHandler):
    """
    Send a notification to Slack
    """

    def __init__(self, details):
        pass

    def send_message(self, message, log_path):
        pass


class ConsoleHandler(MessageHandler):
    """
    Print output to the console
    """

    def send_message(self, message, log_path):
        print(message)
