# Objects

## Supervisor

`models.Supervisor`

The Supervisor is the main object used to coordinate messaging and error handling. Informally implemented as a singleton.

### Attributes

- `message_handlers` (List): Notifications will be sent via all handlers in this list
- `logger` (Logger, optional): Logger object to use in global exception handler
- `log_path` (Path, optional): Path to a logfile to attach to exception messages sent via `.notify()` (usually emails)

### Methods

- `add_message_handler(handler)`: Register a new handler for sending messages
- `notify(message)`: Send a notification to all registered handlers

### Usage

#### Instantiation

You'll instantiate a single Supervisor object to handle messaging and (optionally) exceptions for the client program (whatever program you're wanting to automate through Windows Task Scheduler).

By default, the Supervisor object will replace the built-in exception handler with one that sends a notification through the registered message handlers. If you don't want this behavior, pass `handle_error=False` when you instantiate the object.

The optional logging arguments on the constructor can be used by the exception handler. The `logger` will be used to log any errors caught by the exception handler. `log_path` can be added as an attachment to any exception messages sent by the registered `MessageHandlers`.

The information in these parameters are not passed to any message handler by default. Any information must be passed as part of a MessageDetails object.

#### Sending Notifications

After you've instantiated a Supervisor object, add whichever MessageHandler objects you want to use to send notifications. Currently, the EmailHandler, SendGridHandler, and ConsoleHandler handlers have been implemented.

To send a notification, call the `.notify()` method on your Supervisor with a MessageDetails parameter. It will send the details to each registered handler, which handle the formatting and sending depending on each specific implementation.

## MessageDetails

`models.MessageDetails`

MessageDetails is a simple data structure for holding information about your message. Using an object provides dot-access to the message elements, property setters, and IDE hinting/autocomplete.

### Attributes

- `message` (str): The text of the message
- `attachment` (List): Strings or Paths to any attachments, including log files
- `subject` (str): The message subject

### Usage

Instantiate a new MessageDetails object for each notification you want to send. Different handlers will require different elements; verify with the message handler(s) you're using.

The `.attachment` property has a setter that will add anything you assign to this value to the attachment list. You can assign either a str or a list of strs and it will handle the list appending/extending internally. You can make additional assignments to `.attachment` in your program to add additional attachments. There is currently no capability to remove items from the list or empty the list.

Pass the MessageDetails object to the handlers as the parameter of the `Supervisor.notify()` method.

# Handlers

All message handlers are implementations of the MessageHandler abstract base class. They must implement the `send_message()` method which accepts a MessageDetails object, formats it specific to the destination, and sends the message. Private helper methods are used to simplify `send_message()`.

## EmailHandler

`message_handlers.EmailHandler`

A handler to send MIME emails via smptlib. Supports multiple recipients, HTML-formatted messages, and attachments (which will be gzipped).

### Instantiation

Relies on the `email_settings` parameter to set up the outgoing server settings. This dictionary requires four items:

- `smtpServer`: The outgoing server DNS name or ip address
- `smtpPort`: The outgoing port (usually 25)
- `from_address`: Account to send emails from
- `to_addresses`: A string or list of strings specifying the recipient addresses

Optionally supports the `prefix` key in `email_settings`, which is a string that will be prepended to the message's subject line. You can use `socket.gethostname()` to include the current hostname.

Optionally relies on the `project_name` parameter to report the client program's name and version number in the email.

### Supported MessageDetail Attributes

#### Required

- `message`: The message to send formatted as a single string.
- `subject`: Message subject (will have the `email_setting` prefix prepended if present)

#### Optional

- `attachments`: Path(s) to attachments to include with the email. Will be gzipped prior to attaching.

## SendGridHandler

`message_handlers.SendGridHandler`

A handler to send plaintext emails via the SendGrid service. Supports multiple recipients, plaintext-formatted messages, and attachments (which will be zipped). As plaintext, it preserves traceback formatting in the message.

### Instantiation

Relies on the `sendgrid_settings` parameter to set up the outgoing server settings. This dictionary requires four items:

- `api_key`: API key for the SendGrid service
- `from_address`: Account to send emails from
- `to_addresses`: A string or list of strings specifying the recipient addresses

Optionally supports the `prefix` key in `sendgrid_settings`, which is a string that will be prepended to the message's subject line. You can use `socket.gethostname()` to include the current hostname.

Optionally relies on the `project_name` parameter to report the client program's name and version number in the email.

### Supported MessageDetail Attributes

#### Required

- `message`: The message to send formatted as a single string.
- `subject`: Message subject (will have the `sendgrid_setting` prefix prepended if present)

#### Optional

- `attachments`: Path(s) to attachments to include with the email. Will be zipped prior to attaching.

## SlackHandler

`message_handlers.SlackHandler`

Not yet implemented. Will be used with Slack's API and message format to post messages to Slack.

## ConsoleHandler

`message_handlers.ConsoleHandler`

A fairly redundant handler to write notifications out to the console. Mainly useful for development. Only supports the `message` attribute.

### Supported MessageDetail Attributes

#### Required

- `message`: The message to send formatted as a single string.
