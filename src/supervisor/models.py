"""
This module holds the classes used by supervisor
"""

from .message_handlers import MessageHandler


class Supervisor:
    """
    Primary class; has the replacement error handler and a Messenger object to handle messaging
    """
    pass


class Messenger:
    """
    Keeps track of all the added message handlers and calls their specific messaging functions via its .send_messages method
    """

    def add_handler(self, handler: MessageHandler):
        """
        Adds a message handler to the list of handlers
        """
        pass

    def notify(self, summary, log_path):
        """
        Calls the .send_message() method on every handler
        """
        pass
