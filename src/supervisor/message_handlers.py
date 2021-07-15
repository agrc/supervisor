"""
message_handlers.py: Holds all the different message handlers
"""

import gzip
import io
import warnings
from abc import ABC, abstractmethod
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from smtplib import SMTP

import pkg_resources


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

        #: Configure outgoing settings
        try:
            from_address = self.email_settings['from_address']
            to_addresses = self.email_settings['to_addresses']
            smtp_server = self.email_settings['smtpServer']
            smtp_port = self.email_settings['smtpPort']

        except KeyError:
            warnings.warn('Required email settings do not exist. No emails sent.')
            return

        for setting in [from_address, to_addresses, smtp_server, smtp_port]:
            if not setting:
                warnings.warn('Required email settings exist but aren\'t populated. No emails sent.')
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

        #: Use body as message if it's already a MIMEMultipart, otherwise create a new MIMEMultipart as the message
        message = MIMEMultipart()
        message.attach(MIMEText(message_details.message, 'html'))

        #: Get the client's version (assuming client has been installed via pip install and setup.py)
        distributions = pkg_resources.require(message_details.project_name)
        if distributions:
            version = distributions[0].version
            version = MIMEText(f'<p>{message_details.project_name} version: {version}</p>', 'html')
            message.attach(version)

        #: Split recipient addresses if needed.
        to_addresses = self.email_settings['to_addresses']
        if not isinstance(to_addresses, str):
            to_addresses_joined = ','.join(to_addresses)
        else:
            to_addresses_joined = to_addresses

        #: Add various elements of the message
        if 'prefix' in self.email_settings:
            message['Subject'] = self.email_settings['prefix'] + message_details.subject
        else:
            message['Subject'] = message_details.subject
        message['From'] = self.email_settings['from_address']
        message['To'] = to_addresses_joined

        #: gzip all attachments and add to message
        for original_path in message_details.attachments:
            if not original_path:  #: Path() doesn't like None and empty string resolves to current dir
                continue

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
    """
    Send a notification to Slack
    """

    def __init__(self, details):
        pass

    def send_message(self, message_details):
        pass


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
