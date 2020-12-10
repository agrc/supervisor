from io import StringIO

from supervisor import message_handlers
from supervisor.models import MessageDetails


def test_console_handler_prints(mocker, capsys):

    handler_mock = mocker.Mock()
    message_details = MessageDetails()
    message_details.message = 'foo'
    message_handlers.ConsoleHandler.send_message(handler_mock, message_details)

    captured = capsys.readouterr()

    assert captured.out == 'foo\n'


def test_build_message_without_attachments(mocker):

    distribution_Mock = mocker.Mock()
    distribution_Mock.version = 0
    distributions = [distribution_Mock]
    mocker.patch('pkg_resources.require', return_value=distributions)

    message_details = MessageDetails()
    message_details.message = 'test_message'
    message_details.subject = 'test_subject'
    message_details.project_name = 'testing'

    handler_mock = mocker.Mock()
    handler_mock.email_settings = {
        'to_addresses': 'foo@example.com',
        'from_address': 'testing@example.com',
    }

    test_message = message_handlers.EmailHandler._build_message(handler_mock, message_details)

    assert test_message.get('Subject') == 'test_subject'
    assert test_message.get('To') == 'foo@example.com'
    assert test_message.get('From') == 'testing@example.com'
    assert test_message.get_payload()[0].get_payload() == 'test_message'
    assert test_message.get_payload()[1].get_payload() == '<p>test version: 0</p>'
