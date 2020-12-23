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

from . import slack


class MessageHandler(ABC):  # pylint: disable=too-few-public-methods
    """Base class for all message handlers.

    Methods
    -------
    send_message(message_details)
        Parse a MessageDetails object and send a message using handler-specific logic
    """

    @abstractmethod
    def send_message(self, message_details):
        """Send a notification using the target-specific logic (email, slack, etc)

        Parameters
        ----------
        message_details : MessageDetails
            The data to be sent in the notification
        """


class EmailHandler(MessageHandler):  # pylint: disable=too-few-public-methods
    """Send a notification via email

    Attributes
    ----------
    email_settings : dict
        From and To addresses, SMTP Server and Port

    Methods
    -------
    send_message(message_details)
        Build a message, create an SMTP object, and send the message
    _build_message(message_details)
        Create email to be sent as a MIMEMultipart object
    _build_gzip_attachment(input_path)
        gzip input_path into a MIMEApplication object
    """

    def __init__(self, email_settings):
        self.email_settings = email_settings

    def send_message(self, message_details):
        """Build a message, create an SMTP object, and send the message

        Parameters
        ----------
        mesage_details : MessageDetails
            Passed through to _build_message. Must have .message, .subject, .project_name; may
            have .log_file and .attachments
        """

        log = logging.getLogger(message_details.project_name)

        #: Configure outgoing settings
        from_address = self.email_settings['from_address']
        to_addresses = self.email_settings['to_addresses']
        smtp_server = self.email_settings['smtpServer']
        smtp_port = self.email_settings['smtpPort']

        if None in [from_address, to_addresses, smtp_server, smtp_port]:
            log.warning('Required environment variables for sending emails do not exist. No emails sent.')

            return

        message = self._build_message(message_details)

        #: Send message
        with SMTP(smtp_server, smtp_port) as smtp:
            smtp.sendmail(from_address, to_addresses, message.as_string())

    def _build_message(self, message_details):
        """Create email to be sent as a MIMEMultipart object

        Parameters
        ----------
        mesage_details : MessageDetails
            Must have .message, .subject, .project_name; may have .log_file and .attachments

        Returns
        -------
        message : MIMEMultipart
            A formatted message that can be passed to smtp.sendmail as message.as_string()
        """

        subject = message_details.subject
        project_name = message_details.project_name

        #: Build attachments list
        attachments = []
        if message_details.log_file:
            attachments.append(message_details.log_file)
        if message_details.attachments:
            attachments.extend(message_details.attachments)

        #: Use body as message if it's already a MIMEMultipart, otherwise create a new MIMEMultipart as the message
        message = MIMEMultipart()
        message.attach(MIMEText(message_details.message, 'html'))

        #: TODO: Not sure how often this is coming comming thorugh, may need more work.
        distributions = pkg_resources.require(project_name)
        if distributions:
            version = distributions[0].version
            version = MIMEText(f'<p>{project_name} version: {version}</p>', 'html')
            message.attach(version)

        #: Split recipient addresses if needed.
        to_addresses = self.email_settings['to_addresses']
        if not isinstance(to_addresses, str):
            to_addresses_joined = ','.join(to_addresses)
        else:
            to_addresses_joined = to_addresses

        #: Add various elements of the message
        message['Subject'] = subject
        message['From'] = self.email_settings['from_address']
        message['To'] = to_addresses_joined

        #: gzip all attachments (logs) and add to message
        for original_path in attachments:
            path = Path(original_path)  #: convert to a Path if it isn't already
            if path.is_file():
                message.attach(self._build_gzip_attachment(path))

        return message

    def _build_gzip_attachment(self, input_path):  #pylint: disable=no-self-use
        """gzip input_path into a MIMEApplication object

        Parameters
        ----------
        input_path : Path
            The on-disk path to the file to gzip. Will be opened in 'rb' mode.

        Returns
        -------
        attachment : MIMEApplication
            The gzip'ed contents of input_path ready to attach to a MIMEMultipart message.
        """
        with (open(input_path, 'rb')) as input_file_object, io.BytesIO() as output_stream:
            gzipper = gzip.GzipFile(mode='wb', fileobj=output_stream)
            gzipper.writelines(input_file_object)
            gzipper.close()
            attachment = MIMEApplication(output_stream.getvalue(), 'x-gzip')
            attachment_filename = input_path.name + '.gz'
            attachment.add_header('Content-Disposition', f'attachment; filename="{attachment_filename}"')

            return attachment


class SlackHandler(MessageHandler):  # pylint: disable=too-few-public-methods
    """Send a notification to Slack

    Attributes
    ----------
    url : str
        The Slack webhook URL

    Methods
    -------
    send_message(message_details)
        Send a message to Slack
    _build_messages(message_details)
        Format message_details into Slack-able formatted Blocks
    _post_messages(messages)
        Post formatted messages to Slack via requests library

    """

    def __init__(self, url, build_method=None):
        self.url = url
        #: FIXME: Replace with an instance of SlackMessageBuilder
        if build_method:
            self.build_method = build_method
        else:
            self.build_method = self._build_messages

    def send_message(self, message_details):
        """Send a message to Slack

        Parameters
        ----------
        message_details : MessageDetails
            The message information
        """
        #: FIXME: Replace with an instance of SlackMessageBuilder
        messages = self._build_messages(message_details)
        self._post_messages(messages)

    #: FIXME: Replace with an instance of SlackMessageBuilder
    def _build_messages(self, message_details):
        """Format message_details into an appropriate slack Message"""
        return 'foo'

    def _post_messages(self, messages):
        """Post messages to slack via the webhook url

        Parameters
        ----------
        messages : list
            the Blocks to send to slack split at the maximum value of 50
        """

        if messages is None or self.url is None:
            return

        #: Make sure messages is a list
        if not isinstance(messages, list):
            messages = [messages]

        #: Post messages
        for message in messages:
            response = requests.post(self.url, data=message, headers={'Content-Type': 'application/json'})

            if response.status_code != 200:
                raise ValueError(
                    f'Request to slack returned an error {response.status_code}, the response is: {response.text}'
                )


class ConsoleHandler(MessageHandler):  # pylint: disable=too-few-public-methods
    """Send a notification to the console.

    Methods
    -------
    send_message(message_details)
        Print message_details.message
    """

    def send_message(self, message_details):
        """Print message_details.message"""
        print(message_details.message)
