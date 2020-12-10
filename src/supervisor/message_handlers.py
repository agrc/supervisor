"""
message_handlers.py: Holds all the different message handlers
"""

from abc import ABC, abstractmethod


class MessageHandler(ABC):  # pylint: disable=too-few-public-methods
    """
    Base class for all message handlers.
    """

    @abstractmethod
    def send_message(self, message_details):
        """
        Send a notification using the target-specific logic (email, slack, etc)
        """


class EmailHandler(MessageHandler):  # pylint: disable=too-few-public-methods
    """
    Send emails via the provided SMTP object
    """

    def __init__(self, smtp, email_settings):
        self.smtp = smtp
        self.email_settings = email_settings

    def send_message(self, message_details):
        """
        to: string | string[]
        subject: string
        body: string | MIMEMultipart
        attachments: string[] - paths to text files to attach to the email

        Send an email.
        """

        #: Configure outgoing settings
        # email_server = get_config_prop('email')
        from_address = self.email_settings['from_address']
        to = self.email_settings['to_addresses']
        # smtp_server = email_server['smtpServer']
        # smtp_port = email_server['smtpPort']

        if None in [from_address, smtp_server, smtp_port]:
            log.warning(
                'Required environment variables for sending emails do not exist. No emails sent. See README.md for more details.'
            )

            return

        #: Split recipient addresses if needed.
        if not isinstance(to, str):
            to_addresses = ','.join(to)
        else:
            to_addresses = to

        #: Use body as message if it's already a MIMEMultipart, otherwise create a new MIMEMultipart as the message
        if isinstance(body, str):
            message = MIMEMultipart()
            message.attach(MIMEText(body, 'html'))
        else:
            message = body

        version = MIMEText(f'<p>Auditor version: {pkg_resources.require("auditor")[0].version}</p>', 'html')
        message.attach(version)

        #: Add various elements of the message
        message['Subject'] = subject
        message['From'] = from_address
        message['To'] = to_addresses

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
        # smtp = SMTP(smtp_server, smtp_port)
        smtp.sendmail(from_address, to, message.as_string())
        # smtp.quit()

        return smtp


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
