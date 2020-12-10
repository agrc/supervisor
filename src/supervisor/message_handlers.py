"""
message_handlers.py: Holds all the different message handlers
"""

import gzip
import io
import logging
from abc import ABC, abstractmethod
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from smtplib import SMTP

import pkg_resources
import requests


class MessageHandler(ABC):  # pylint: disable=too-few-public-methods
    """
    Base class for all message handlers.
    """

    @abstractmethod
    def send_message(self, message_details):
        """
        Send a notification using the target-specific logic (email, slack, etc)

        message_details: A dictionary of the different parts. Available keys:
                            message:    The messages as a string
                            log_path:   A Path object to the log file
                            subject:    Email subject as a string
                            project_name:   Project name as a string
        """
        #: TODO: Should message details be an object so that we can have defaults and dot-notation access?


class EmailHandler(MessageHandler):  # pylint: disable=too-few-public-methods
    """
    Send emails via the provided SMTP object
    """

    def __init__(self, email_settings):
        self.email_settings = email_settings

    def send_message(self, message_details):
        """
        to: string | string[]
        subject: string
        body: string | MIMEMultipart
        attachments: string[] - paths to text files to attach to the email

        Send an email.
        """

        project_name = message_details['project_name']
        log = logging.getLogger(project_name)

        #: Configure outgoing settings
        # email_server = get_config_prop('email')
        from_address = self.email_settings['from_address']
        to_addresses = self.email_settings['to_addresses']
        smtp_server = self.email_settings['smtpServer']
        smtp_port = self.email_settings['smtpPort']

        if None in [from_address, to_addresses, smtp_server, smtp_port]:
            log.warning(
                'Required environment variables for sending emails do not exist. No emails sent. See README.md for more details.'
            )

            return

        #: Split recipient addresses if needed.
        if not isinstance(to_addresses, str):
            to_addresses_joined = ','.join(to_addresses)
        else:
            to_addresses_joined = to_addresses

        #: Use body as message if it's already a MIMEMultipart, otherwise create a new MIMEMultipart as the message
        if isinstance(body, str):
            message = MIMEMultipart()
            message.attach(MIMEText(body, 'html'))
        else:
            message = body

        version = MIMEText(f'<p>{project_name} version: {pkg_resources.require(project_name)[0].version}</p>', 'html')
        message.attach(version)

        #: Add various elements of the message
        message['Subject'] = subject
        message['From'] = from_address
        message['To'] = to_addresses_joined

        #: gzip all attachments (logs) and add to message
        for original_path in attachments:
            path = Path(original_path)  #: convert to a Path if it isn't already
            if path.is_file():
                with (open(path, 'rb')) as log_file, io.BytesIO() as encoded_log:
                    gzipper = gzip.GzipFile(mode='wb', fileobj=encoded_log)
                    gzipper.writelines(log_file)
                    gzipper.close()

                    attachment = MIMEApplication(encoded_log.getvalue(), 'x-gzip')
                    attachment.add_header('Content-Disposition', 'attachment; filename="{}"'.format(path.name + '.gz'))

                    message.attach(attachment)

        #: Send message
        with SMTP(smtp_server, smtp_port) as smtp:
            smtp.sendmail(from_address, to_addresses, message.as_string())

        # return smtp


class SlackHandler(MessageHandler):  # pylint: disable=too-few-public-methods
    """
    Send a notification to Slack
    """

    def __init__(self, details):
        pass

    def send_message(self, message_details):
        pass


class ConsoleHandler(MessageHandler):  # pylint: disable=too-few-public-methods
    """
    Print output to the console
    """

    def send_message(self, message_details):
        print(message_details['message'])
