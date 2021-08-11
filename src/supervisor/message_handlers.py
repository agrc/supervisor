"""
message_handlers.py: Holds all the different message handlers
"""

import gzip
import io
import warnings
from abc import ABC, abstractmethod
from base64 import b64encode
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from shutil import make_archive
from smtplib import SMTP
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

import pkg_resources
import sendgrid
from sendgrid.helpers.mail import Attachment, Content, Email, FileContent, FileName, FileType, Mail, To


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
            have .attachments
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
            Must have .message, .subject, .project_name; may have .attachments

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


class SendGridHandler(MessageHandler):  # pylint: disable=too-few-public-methods
    """Send emails via the SendGrid service.

    Attributes
    ----------
    sendgrid_settings : dict
        'from_address' (str)
        'to_addresses' (str or List): single string or list of strings

    Methods
    -------
    send_message(message_details)
        Build a message and send using the SendGrid API's helper classes
    """

    def __init__(self, sendgrid_settings):
        self.sendgrid_settings = sendgrid_settings
        self.sendgrid_client = sendgrid.SendGridAPIClient(api_key=self.sendgrid_settings['api_key'])

    def send_message(self, message_details):
        """Construct and send an email message with the SendGrid API

        Args:
            message_details : MessageDetails
                Must have .message, .subject, .project_name; may have .attachments
        """

        from_address, to_addresses = self._verify_addresses()
        #: Bail out instead of raising error instead of forcing client to deal with it
        #: Warnings should have been raised from _verify_addresses() and Nones returned.
        if not from_address or not to_addresses:
            return

        sender_address = Email(from_address)
        recipient_addresses = self._build_recipient_addresses(to_addresses)

        subject = self._build_subject(message_details)
        content = self._build_content(message_details)
        attachments = self._process_attachments(message_details.attachments)

        #: Build message object and send it
        mail = Mail(sender_address, recipient_addresses, subject, content)
        response = self.sendgrid_client.client.mail.send.post(request_body=mail.get())

        #: Maybe test the response via response.status_code?

    def _verify_addresses(self):
        """Make sure from/to address keys exist and are not empty

        Returns:
            tuple (str): from and to addresses
        """

        try:
            from_address = self.sendgrid_settings['from_address']
            to_addresses = self.sendgrid_settings['to_addresses']

        except KeyError:
            warnings.warn('To/From address settings do not exist. No emails sent.')
            return None, None

        if not from_address or not to_addresses:
            warnings.warn('To/From address settings exist but are empty. No emails sent.')
            return None, None

        return from_address, to_addresses

    def _build_recipient_addresses(self, to_addresses):  #pylint: disable=no-self-use
        """Craft 'to' addresses into a list of SendGrid 'To' objects

        Args:
            to_addresses (str or List): 'to' addresses, either as a single string or list of strings

        Returns:
            list (To): 'To' objects for future Mail() object
        """

        #: If we just get a string just return that one
        if isinstance(to_addresses, str):
            return [To(to_addresses)]

        recipient_addresses = []
        for address in to_addresses:
            recipient_addresses.append(To(address))
        return recipient_addresses

    def _build_subject(self, message_details):
        """Add prefix to subject if needed

        Args:
            message_details (MessageDetails): Will use .prefix if present

        Returns:
            str: Subject for outgoing email
        """

        subject = message_details.subject
        if 'prefix' in self.sendgrid_settings:
            subject = self.sendgrid_settings['prefix'] + subject

        return subject

    def _build_content(self, message_details):  #pylint: disable=no-self-use
        """Add client version if desired and package into plaintext Content object

        Args:
            message_details (MessageDetails): Uses .project_name to get client version

        Returns:
            Content: Content of email as a SendGrid Content object
        """
        message = message_details.message

        #: Get the client's version (assuming client has been installed via pip install and setup.py)
        distributions = pkg_resources.require(message_details.project_name)
        if distributions:
            version = distributions[0].version
            version = f'\n\n{message_details.project_name} version: {version}'
            message += version

        return Content('text/plain', message)

    def _process_attachments(self, attachments):

        attachment_objects = []
        working_dir = TemporaryDirectory().name

        for attachment in attachments:
            if Path(attachment).is_dir():
                zip_path = self._zip_whole_directory(working_dir, attachment)
            else:
                zip_path = self._zip_single_file(working_dir, attachment)
            attachment_objects.append(self._build_attachment(zip_path))

        return attachment_objects

    def _zip_whole_directory(self, working_dir, dir_to_be_zipped):

        #: Zip a whole directory to the tempdir, return its path
        attachment_dir = Path(dir_to_be_zipped)
        zip_base_name = Path(working_dir, attachment_dir.name)
        zip_out_path = make_archive(zip_base_name, 'zip', root_dir=attachment_dir.parent, base_dir=attachment_dir.name)
        return zip_out_path

    def _zip_single_file(self, working_dir, attachment):

        #: Zip a single file to the tempdir, return its path
        attachment_path = Path(attachment)
        zip_out_path = Path(working_dir, attachment_path.stem).with_suffix('zip')
        with ZipFile(zip_out_path, 'x', compression=ZIP_DEFLATED) as new_zip:
            new_zip.write(attachment_path, zip_out_path.name)
        return zip_out_path

    def _build_attachment(self, zip_path):

        #: Build a SendGrid Attachment object with various fields
        with open(zip_path, 'rb') as zip_file:
            data = zip_file.read()
        encoded = b64encode(data).decode()
        attachment = Attachment()
        attachment.file_content = FileContent(encoded)
        attachment.file_type = FileType('application/zip')
        attachment.file_name = FileName(Path(zip_path).name)
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
