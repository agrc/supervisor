"""
This module holds the classes used by supervisor
"""

from .message_handlers import MessageHandler


class Supervisor:
    """
    Primary class; has the replacement error handler and a Messenger object to handle messaging
    """

    def __init__(self):
        self.message_handlers = []

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
