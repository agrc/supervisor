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

Optionally relies on the `client_name` and `client_version` parameters to report the client program's name and version number in the email.

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

Optionally relies on the `client_name` and `client_version` parameters to report the client program's name and version number in the email.

### Supported MessageDetail Attributes

#### Required

- `message`: The message to send formatted as a single string.
- `subject`: Message subject (will have the `sendgrid_setting` prefix prepended if present)

#### Optional

- `attachments`: Path(s) to attachments to include with the email. Will be zipped prior to attaching.

## SlackHandler

`message_handlers.SlackHandler`

A handler to send notifications to Slack via webhook URLs using Slack's Block Kit. Supports rich message formatting through Message and Block objects and automatically splits messages to comply with Slack's limits.

### Instantiation

Relies on the `slack_settings` parameter to configure the Slack webhook. This dictionary requires:

- `webhook_url`: The Slack incoming webhook URL for your channel (obtained from Slack's webhook configuration)

Optionally relies on the `client_name` and `client_version` parameters to report the client program's name and version number in text fallback messages.

### Using Slack Block Kit

The SlackHandler is designed to work with Slack's Block Kit for rich message formatting. Client applications create `Message` objects and populate them with Block objects, then add them to the `slack_messages` property of `MessageDetails`:

```python
from supervisor.message_handlers import SlackHandler
from supervisor.models import MessageDetails
from supervisor.slack import Message, SectionBlock, ContextBlock, DividerBlock

# Set up Slack handler
slack_settings = {'webhook_url': 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'}
handler = SlackHandler(slack_settings, client_name='my_project', client_version='1.0.0')

# Create message with blocks
message = Message(text='Job Complete')
message.add(SectionBlock(':white_check_mark: *Processing Complete*'))
message.add(ContextBlock(['Status: Success', 'Items processed: 100']))
message.add(DividerBlock())
message.add(SectionBlock('All tasks completed successfully'))

message_details = MessageDetails()
message_details.slack_messages = message

supervisor.add_message_handler(handler)
supervisor.notify(message_details)
```

### Available Block Types

The following Block Kit objects are available in `supervisor.slack`:

- **Message(text="", blocks=None)**: Container for Slack message with blocks
  - `text`: Fallback text for notifications
  - `blocks`: Optional initial blocks (single Block or list)
  - `add(block)`: Add a block to the message
  - `get_messages()`: Get message payloads (automatically splits if >50 blocks)

- **SectionBlock(text=None, fields=None)**: Flexible block for text and fields
  - `text`: Main text content (max 3000 chars)
  - `fields`: Optional list of field texts (max 2000 chars each, 10 fields max)

- **ContextBlock(elements)**: Display contextual information
  - `elements`: List of text elements (max 10 elements, 2000 chars each)

- **DividerBlock()**: Visual separator (like `<hr>`)

- **Text.to_text(text, max_length=None)**: Helper to create markdown text with length limiting

### Text Fallback

If `slack_messages` is empty, the handler automatically falls back to sending a simple text message using the `.message` and `.subject` properties:

```python
message = MessageDetails()
message.subject = 'Simple Alert'
message.message = 'This is a plain text message'
supervisor.notify(message)
```

### Message Splitting

The `Message` class automatically handles splitting when messages exceed Slack's 50 block limit through the `get_messages()` method. The SlackHandler processes each split message separately.

**Text Length Limit** (for fallback mode): When using text fallback, messages exceeding 3000 characters are split into multiple parts:
- The first message includes the subject header
- Middle messages (if any) contain only the message content
- The last message includes the client name and version footer

### Section and Field Limits

Block Kit has built-in limits that are automatically enforced:
- Section text: 3000 characters max
- Section fields: 2000 characters max per field, 10 fields max
- Context elements: 2000 characters max per element, 10 elements max

Text is automatically truncated to these limits when creating Block objects.

### Supported MessageDetail Attributes

#### For Block Kit Messages

- `slack_messages`: List of Message objects (from supervisor.slack)

#### For Text Fallback Messages

- `message`: The message to send formatted as a single string
- `subject`: Message subject (used in the formatted output)

#### Not Supported

- `attachments`: File attachments are not currently supported for Slack messages

### Example Usage

```python
from supervisor.message_handlers import SlackHandler
from supervisor.models import Supervisor, MessageDetails

# Set up Slack handler
slack_settings = {
    'webhook_url': 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
}
supervisor = Supervisor()
supervisor.add_message_handler(SlackHandler(
    slack_settings,
    client_name='my_project',
    client_version='1.0.0'
))

# Send a notification
message = MessageDetails()
message.subject = 'Job Complete'
message.message = 'Processing completed successfully'
supervisor.notify(message)
```

## ConsoleHandler

`message_handlers.ConsoleHandler`

A fairly redundant handler to write notifications out to the console. Mainly useful for development. Only supports the `message` attribute.

### Supported MessageDetail Attributes

#### Required

- `message`: The message to send formatted as a single string.
