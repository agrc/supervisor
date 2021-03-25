# Objects

## Supervisor

`models.Supervisor`

The Supervisor is the main object used to coordinate messaging and error handling. Implemented as a singleton.

### Attributes

- `project_name` (str): The name of the client project using Supervisor; used to report version in global exception handler messages
- `message_handlers` (List): Notifications will be sent via all handlers in this list
- `logger` (Logger): Logger object to use in global exception handler
- `log_path` (Path): Path to a logfile to send in exception messages

### Methods

- `add_message_handler(handler)`: Register a new handler for sending messages
- `notify(message)`: Send a notification to all registered handlers

### Usage

#### Instantiation

You'll instantiate a single Supervisor object to handle messaging and exceptions for the client program (whatever program you're wanting to automate through Windows Task Scheduler).

The three arguments on the constructor are used to create messages in the exception handler. `name` is added to the subject of exception messages and should match the client's python module name. The `logger` will be used to log any errors caught by the exception handler. `log_path` will be added as an attachment to any exception messages.

The information in these parameters are not passed to any message handler by default. Any information must be passed as part of a MessageDetails object.

#### Sending Notifications

After you've instantiated a Supervisor object, add whichever MessageHandler objects you want to use to send notifications. Currently, only the EmailHandler and ConsoleHandler handlers have been implemented.

To send a notification, call the `.notify()` method on your Supervisor with a MessageDetails parameter. It will send the details to each registered handler, which handle the formatting and sending depending on each specific implementation.

## MessageDetails

`models.MessageDetails`

MessageDetails is a simple data structure for holding information about your message. Using an object provides dot-access to the message elements and IDE hinting/autocomplete.

### Attributes

- `message` (str): The text of the message
- `attachment` (List): Strings or Paths to any attachments, including log files
- `subject` (str): The message subject
- `project_name` (str): The name of the project that has added the Supervisor object. Used for adding the version to notifications.

### Usage

Instantiate a new MessageDetails object for each notification you want to send. Different handlers will require different elements; verify with the message handler(s) you're using.

Pass the MessageDetails object to the handlers as the parameter of the `Supervisor.notify()` method.

# Handlers

All message handlers are implementations of the MessageHandler abstract base class. They must implement the `send_message()` method which accepts a MessageDetails object, formats it specific to the destination, and sends the message. Hidden helper methods can be used to simplify `send_message()` if necessary.

## EmailHandler

`message_handlers.EmailHandler`

A handler to send MIME emails via smptlib. Supports multiple recipients, HTML-formatted messages, and attachments (which will be gzipped).

### Instantiation

Relies on the `email_settings` parameter to set up the outgoing server settings. This dictionary requires four items:

- `smtpServer`: the outgoing server DNS name or ip address
- `smtpPort`: the outgoing port (usually 25)
- `from_address`: account to send emails from
- `to_addresses`: A string or list of strings specifying the recipient addresses

Optionally supports the `prefix` value, which is a string that will be prepended to the message's subject line. You can use `socket.gethostname()` to include the current hostname.

### Supported MessageDetail Attributes

#### Required

- `message`: The message to send formatted as a single string.
- `subject`: Message subject (will have the email_setting's prefix prepended if present)
- `project_name`: Name of the client program using Supervisor
  - Used to get the current version of the client.

#### Optional

- `attachments`: Path(s) to attachments to include with the email. Will be gzipped prior to attaching.

## SlackHandler

`message_handlers.SlackHandler`

Not yet implemented. Will be used with Slack's API and message format to post messages to Slack.

## ConsoleHandler

`message_handlers.ConsoleHandler`

A fairly redundant handler to write notifications out to the console. Mainly useful for development. Only supports the `message` attribute.

### Supported MessageDetail Attributes

#### Required

- `message`: The message to send formatted as a single string.
