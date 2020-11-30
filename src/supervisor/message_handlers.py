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
    Handler for sending emails via the provided SMTP object
    """

    def __init__(self, smtp):
        pass

    def send_message(self, message, log_path):
        pass


class SlackHandler(MessageHandler):
    """
    Handler for sending a notification to Slack
    """

    def __init__(self, details):
        pass

    def send_message(self, message, log_path):
        pass
