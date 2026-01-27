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

import python_http_client
import requests
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
    project_name : str
        pip-install name of the client project for client version number reporting

    Methods
    -------
    send_message(message_details)
        Build a message, create an SMTP object, and send the message
    _build_message(message_details)
        Create email to be sent as a MIMEMultipart object
    _build_gzip_attachment(input_path)
        gzip input_path into a MIMEApplication object
    """

    def __init__(self, email_settings, client_name="unknown client", client_version="not specified"):
        self.email_settings = email_settings
        self.client_name = client_name
        self.client_version = client_version

    def send_message(self, message_details):
        """Build a message, create an SMTP object, and send the message

        Parameters
        ----------
        message_details : MessageDetails
            Passed through to _build_message. Must have .message, .subject; may have .attachments
        """

        #: Configure outgoing settings
        try:
            from_address = self.email_settings["from_address"]
            to_addresses = self.email_settings["to_addresses"]
            smtp_server = self.email_settings["smtpServer"]
            smtp_port = self.email_settings["smtpPort"]

        except KeyError:
            warnings.warn("Required email settings do not exist. No emails sent.")
            return

        for setting in [from_address, to_addresses, smtp_server, smtp_port]:
            if not setting:
                warnings.warn("Required email settings exist but aren't populated. No emails sent.")
                return

        message = self._build_message(message_details)

        #: Send message
        with SMTP(smtp_server, smtp_port) as smtp:
            smtp.sendmail(from_address, to_addresses, message.as_string())

    def _build_message(self, message_details):
        """Create email to be sent as a MIMEMultipart object

        Parameters
        ----------
        message_details : MessageDetails
            Must have .message, .subject; may have .attachments

        Returns
        -------
        message : MIMEMultipart
            A formatted message that can be passed to smtp.sendmail as message.as_string()
        """

        #: Use body as message if it's already a MIMEMultipart, otherwise create a new MIMEMultipart as the message
        message = MIMEMultipart()
        message.attach(MIMEText(message_details.message, "html"))

        version = MIMEText(f"<p>{self.client_name} version: {self.client_version}</p>", "html")
        message.attach(version)

        #: Split recipient addresses if needed.
        to_addresses = self.email_settings["to_addresses"]
        if not isinstance(to_addresses, str):
            to_addresses_joined = ",".join(to_addresses)
        else:
            to_addresses_joined = to_addresses

        #: Add various elements of the message
        if "prefix" in self.email_settings:
            message["Subject"] = self.email_settings["prefix"] + message_details.subject
        else:
            message["Subject"] = message_details.subject
        message["From"] = self.email_settings["from_address"]
        message["To"] = to_addresses_joined

        #: gzip all attachments and add to message
        for original_path in message_details.attachments:
            if not original_path:  #: Path() doesn't like None and empty string resolves to current dir
                continue

            path = Path(original_path)  #: convert to a Path if it isn't already
            if path.is_file():
                message.attach(self._build_gzip_attachment(path))

        return message

    @staticmethod
    def _build_gzip_attachment(input_path):
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
        with open(input_path, "rb") as input_file_object, io.BytesIO() as output_stream:
            gzipper = gzip.GzipFile(mode="wb", fileobj=output_stream)
            gzipper.writelines(input_file_object)
            gzipper.close()
            attachment = MIMEApplication(output_stream.getvalue(), "x-gzip")
            attachment_filename = input_path.name + ".gz"
            attachment.add_header("Content-Disposition", f'attachment; filename="{attachment_filename}"')

            return attachment


class SendGridHandler(MessageHandler):  # pylint: disable=too-few-public-methods
    """Send emails via the SendGrid service.

    Attributes
    ----------
    sendgrid_settings : dict
        'from_address' (str)
        'to_addresses' (str or List): single string or list of strings
        'api_key' (str): SendGrid api key
    client_name : str (optional, default='unknown client')
        name of the client project for email body
    client_version : str (optional, default='not specified')
        client project's version for email body

    Methods
    -------
    send_message(message_details)
        Build a message and send using the SendGrid API's helper classes
    """

    def __init__(self, sendgrid_settings, client_name="unknown client", client_version="not specified"):
        self.sendgrid_settings = sendgrid_settings
        self.sendgrid_client = sendgrid.SendGridAPIClient(api_key=self.sendgrid_settings["api_key"])
        self.client_name = client_name
        self.client_version = client_version

    def send_message(self, message_details):
        """Construct and send an email message with the SendGrid API

        Args:
            message_details : MessageDetails
                Must have .message, .subject; may have .attachments
        """

        from_address, to_addresses = self._verify_addresses()
        #: Bail out instead of raising error instead of forcing client to deal with it
        #: Warnings should have been raised from _verify_addresses() and Nones returned.
        if not from_address or not to_addresses:
            return

        sender_address = Email(from_address)
        recipient_addresses = self._build_recipient_addresses(to_addresses)

        subject = self._build_subject(message_details)
        attachment_warning, verified_attachments = self._verify_attachments(message_details.attachments)
        new_message = attachment_warning + message_details.message
        content = self._build_content(new_message, self.client_name, self.client_version)
        attachments = self._process_attachments(verified_attachments)

        #: Build message object and send it
        mail = Mail(sender_address, recipient_addresses, subject, content)
        mail.attachment = attachments
        try:
            self.sendgrid_client.client.mail.send.post(request_body=mail.get())
        except python_http_client.BadRequestsError as err:
            if "HTTP Error 400: Bad Request" in str(err):
                warnings.warn("SendGrid error 400, might be missing a required Mail component; no e-mail sent.")
            else:
                raise err
        except python_http_client.UnauthorizedError as err:
            if "HTTP Error 401: Unauthorized" in str(err):
                warnings.warn("SendGrid error 401: Unauthorized. Check API key.")
            else:
                raise err

    def _verify_addresses(self):
        """Make sure from/to address keys exist and are not empty

        Returns:
            tuple (str): from and to addresses
        """

        try:
            from_address = self.sendgrid_settings["from_address"]
            to_addresses = self.sendgrid_settings["to_addresses"]

        except KeyError:
            warnings.warn("To/From address settings do not exist. No emails sent.")
            return None, None

        if not from_address or not to_addresses:
            warnings.warn("To/From address settings exist but are empty. No emails sent.")
            return None, None

        return from_address, to_addresses

    @staticmethod
    def _build_recipient_addresses(to_addresses):
        """Craft 'to' addresses into a list of SendGrid 'To' objects

        Args:
            to_addresses (str or List): 'to' addresses, either as a single string or list of strings

        Returns:
            list (To): 'To' objects for future Mail() object
        """

        #: If we just get a string just return that one
        if isinstance(to_addresses, str):
            return [To(to_addresses)]

        return [To(address) for address in to_addresses]

    def _build_subject(self, message_details):
        """Add prefix to subject if needed

        Args:
            message_details (MessageDetails): Will use .prefix if present

        Returns:
            str: Subject for outgoing email
        """

        subject = message_details.subject
        if "prefix" in self.sendgrid_settings:
            subject = self.sendgrid_settings["prefix"] + subject

        return subject

    @staticmethod
    def _build_content(message, client_name, client_version):
        """Add client version if desired and package into plaintext Content object

        Args:
            message (str): Main message content
            project_name (str): pip-install name of the client project for client version number reporting

        Returns:
            Content: Content of email as a SendGrid Content object
        """

        client_version = f"\n\n{client_name} version: {client_version}"
        message += client_version

        return Content("text/plain", message)

    @staticmethod
    def _verify_attachments(attachments):
        """Make sure attachments are legitimate Paths

        Args:
            attachments (List): strs or Paths of files to be attached

        Returns:
            str, List: Warning message to be appended to main message, list of verified attachments
        """

        error_message = ""
        good_attachments = []
        for attachment in attachments:
            try:
                attachment_path = Path(attachment)
                if not attachment_path.exists():
                    error_message += f'* Attachment "{attachment}" does not exist\n'
                    continue
                good_attachments.append(attachment)
            except TypeError as err:
                if "expected str, bytes or os.PathLike object, not" in str(err):
                    error_message += f'* Cannot get Path() of attachment "{attachment}"\n'

        if error_message:
            error_message = f"{'=' * 20}\n Supervisor Warning\n{'=' * 20}\n{error_message}{'=' * 20}\n\n"

        return error_message, good_attachments

    def _process_attachments(self, attachments):
        """Create Attachment objects containing zipped files from pre-verified attachment paths

        Args:
            attachments (List): Pre-verified strs or Paths to single files and/or directories, will be zipped

        Returns:
            Attachment: Attachment objects ready to be added to Mail
        """

        attachment_objects = []

        #: Note: if we use this context manager, zip files in working_dir don't persist for testing purposes.
        with TemporaryDirectory() as working_dir:
            for attachment in attachments:
                if Path(attachment).is_dir():
                    zip_path = self._zip_whole_directory(working_dir, attachment)
                else:
                    zip_path = self._zip_single_file(working_dir, attachment)
                attachment_objects.append(self._build_attachment(zip_path))

        return attachment_objects

    @staticmethod
    def _zip_whole_directory(working_dir, dir_to_be_zipped):
        """Create a zipfile containing a directory and all its contents

        Args:
            working_dir (str or Path): A directory to store the new zipfile
            dir_to_be_zipped (str or Path): The directory to be zipped

        Returns:
            str: Path to the new zipfile
        """

        attachment_dir = Path(dir_to_be_zipped)
        zip_base_name = Path(working_dir, attachment_dir.name)
        zip_out_path = make_archive(
            str(zip_base_name), "zip", root_dir=attachment_dir.parent, base_dir=attachment_dir.name
        )
        return zip_out_path

    @staticmethod
    def _zip_single_file(working_dir, attachment):
        """Create a zipfile containing a single file

        Args:
            working_dir (str or Path): A directory to store the new zipfile
            attachment (str or Path): The file to be zipped

        Returns:
            Path: Path to the new zipfile
        """
        attachment_path = Path(attachment)
        zip_out_path = Path(working_dir, attachment_path.stem).with_suffix(".zip")
        with ZipFile(zip_out_path, "x", compression=ZIP_DEFLATED) as new_zip:
            new_zip.write(attachment_path, attachment_path.name)
        return zip_out_path

    @staticmethod
    def _build_attachment(zip_path):
        """Create an Attachment object by base64-encoding the specified file-like object

        Args:
            zip_path (str or Path): Path to the file to be attached

        Returns:
            Attachment: Attachment object ready to be added to Mail object.
        """
        #: Build a SendGrid Attachment object with various fields
        with open(zip_path, "rb") as zip_file:
            data = zip_file.read()
        encoded = b64encode(data).decode()
        attachment = Attachment()
        attachment.file_content = FileContent(encoded)
        attachment.file_type = FileType("application/zip")
        attachment.file_name = FileName(Path(zip_path).name)
        return attachment


class SlackHandler(MessageHandler):  # pylint: disable=too-few-public-methods
    """Send a notification to Slack via webhook URL.

    Attributes
    ----------
    slack_settings : dict
        'webhook_url' (str): Slack webhook URL for posting messages
    formatter : callable, optional
        Function that takes a MessageDetails object and returns a dict for Slack's API.
        If not provided, uses a default formatter that creates a simple text message.
    max_length : int
        Maximum character length for a single Slack message (default: 3000)
    client_name : str
        pip-install name of the client project for version reporting
    client_version : str
        client project's version for version reporting

    Methods
    -------
    send_message(message_details)
        Format and send message to Slack, splitting if necessary
    """

    def __init__(
        self, slack_settings, formatter=None, max_length=3000, client_name="unknown client", client_version="not specified"
    ):
        self.slack_settings = slack_settings
        self.formatter = formatter if formatter else self._default_formatter
        self.max_length = max_length
        self.client_name = client_name
        self.client_version = client_version

    def send_message(self, message_details):
        """Format and send message to Slack, splitting if necessary.

        Parameters
        ----------
        message_details : MessageDetails
            Must have .message, .subject; .attachments are not currently supported
        """

        #: Verify webhook URL exists
        try:
            webhook_url = self.slack_settings["webhook_url"]
        except KeyError:
            warnings.warn("Required Slack webhook_url does not exist. No message sent.")
            return

        if not webhook_url:
            warnings.warn("Slack webhook_url exists but is empty. No message sent.")
            return

        #: Format the message using the provided or default formatter
        try:
            formatted_payload = self.formatter(message_details, self.client_name, self.client_version)
        except Exception as err:  # pylint: disable=broad-except
            warnings.warn(f"Error formatting message for Slack: {err}. No message sent.")
            return

        #: Extract text content and blocks to check limits
        message_text = formatted_payload.get("text", "")
        message_blocks = formatted_payload.get("blocks", [])

        #: Check if we need to split based on text length or block count
        #: Slack limits: 3000 chars for text (webhook), 50 blocks max
        needs_split = len(message_text) > self.max_length or len(message_blocks) > 50

        #: If message fits within limits, send as-is
        if not needs_split:
            self._post_to_slack(webhook_url, formatted_payload)
        else:
            #: Split message into chunks and send separately
            self._send_split_messages(webhook_url, message_details)

    def _default_formatter(self, message_details, client_name, client_version):
        """Default formatter for Slack messages.

        Parameters
        ----------
        message_details : MessageDetails
            Must have .message and .subject
        client_name : str
            Name of the client project
        client_version : str
            Version of the client project

        Returns
        -------
        dict
            Slack message payload with text field
        """
        #: Combine subject and message
        full_message = f"*{message_details.subject}*\n\n{message_details.message}"

        #: Add version info
        full_message += f"\n\n_{client_name} version: {client_version}_"

        return {"text": full_message}

    def _send_split_messages(self, webhook_url, message_details):
        """Split a long message into chunks and send each separately.

        Parameters
        ----------
        webhook_url : str
            Slack webhook URL
        message_details : MessageDetails
            Original message details (for subject and message)
        """
        #: Calculate header and footer sizes for overhead calculation
        header = f"*{message_details.subject}*\n\n"
        footer = f"\n\n_{self.client_name} version: {self.client_version}_"
        
        #: First message has header, last has footer, middle messages have neither
        #: Calculate chunk size based on max overhead (header + footer for edge cases)
        max_overhead = len(header) + len(footer)
        chunk_size = self.max_length - max_overhead

        if chunk_size <= 0:
            warnings.warn("Subject and version info too long for Slack message splitting. No message sent.")
            return

        #: Split message into chunks
        message_only = message_details.message
        chunks = [message_only[i : i + chunk_size] for i in range(0, len(message_only), chunk_size)]

        #: Send each chunk
        for i, chunk in enumerate(chunks):
            #: First message gets header, last message gets footer
            if i == 0:
                chunk_message = f"{header}{chunk}"
            else:
                chunk_message = chunk
            
            if i == len(chunks) - 1:
                chunk_message += footer

            payload = {"text": chunk_message}
            self._post_to_slack(webhook_url, payload)

    @staticmethod
    def _post_to_slack(webhook_url, payload):
        """Post a message payload to Slack webhook.

        Parameters
        ----------
        webhook_url : str
            Slack webhook URL
        payload : dict
            Message payload to send
        """
        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
        except Exception as err:  # pylint: disable=broad-except
            warnings.warn(f"Error posting to Slack: {err}")


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
