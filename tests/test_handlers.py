import pytest

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
    assert test_message.get_payload()[1].get_payload() == '<p>testing version: 0</p>'


def test_build_message_with_subject_prefix(mocker):

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
        'prefix': 'test prefix: ',
    }

    test_message = message_handlers.EmailHandler._build_message(handler_mock, message_details)

    assert test_message.get('Subject') == 'test prefix: test_subject'
    assert test_message.get('To') == 'foo@example.com'
    assert test_message.get('From') == 'testing@example.com'
    assert test_message.get_payload()[0].get_payload() == 'test_message'
    assert test_message.get_payload()[1].get_payload() == '<p>testing version: 0</p>'


def test_build_message_with_multiple_to_addresses(mocker):

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
        'to_addresses': ['foo@example.com', 'bar@example.com', 'baz@example.com'],
        'from_address': 'testing@example.com',
    }

    test_message = message_handlers.EmailHandler._build_message(handler_mock, message_details)

    assert test_message.get('Subject') == 'test_subject'
    assert test_message.get('To') == 'foo@example.com,bar@example.com,baz@example.com'
    assert test_message.get('From') == 'testing@example.com'
    assert test_message.get_payload()[0].get_payload() == 'test_message'
    assert test_message.get_payload()[1].get_payload() == '<p>testing version: 0</p>'


def test_gzip_not_called_for_non_existant_attachments(mocker, tmp_path):

    distribution_Mock = mocker.Mock()
    distribution_Mock.version = 0
    distributions = [distribution_Mock]
    mocker.patch('pkg_resources.require', return_value=distributions)

    message_details = MessageDetails()
    message_details.message = 'test_message'
    message_details.subject = 'test_subject'
    message_details.project_name = 'testing'
    message_details.attachments = [
        tmp_path / 'att1',
    ]

    handler_mock = mocker.Mock()
    handler_mock.email_settings = {
        'to_addresses': 'foo@example.com',
        'from_address': 'testing@example.com',
    }

    test_message = message_handlers.EmailHandler._build_message(handler_mock, message_details)

    assert not handler_mock._build_gzip_attachment.called


def test_gzip_called_3_times_for_3_attachments(mocker, tmp_path):

    distribution_Mock = mocker.Mock()
    distribution_Mock.version = 0
    distributions = [distribution_Mock]
    mocker.patch('pkg_resources.require', return_value=distributions)

    atts = []
    for i in range(1, 4):
        path = tmp_path / f'att{i}'
        with open(path, 'w') as attfile:
            attfile.write(f'att{i}')
        atts.append(path)

    message_details = MessageDetails()
    message_details.message = 'test_message'
    message_details.subject = 'test_subject'
    message_details.project_name = 'testing'
    message_details.attachments.extend(atts)

    handler_mock = mocker.Mock()
    handler_mock.email_settings = {
        'to_addresses': 'foo@example.com',
        'from_address': 'testing@example.com',
    }

    test_message = message_handlers.EmailHandler._build_message(handler_mock, message_details)

    assert handler_mock._build_gzip_attachment.call_count == 3


def test_gzipper(mocker, tmp_path):
    # with BytesIO(b'test text') as test_bytes:
    #     # mocker.patch.object(message_handlers.EmailHandler._build_gzip_attachment, 'input_file_object', test_bytes)
    #     mocker.patch('sys.open', return_value=test_bytes)

    temp_path = tmp_path / 'test'
    with open(temp_path, 'w') as temp_file:
        temp_file.write('test text')
    temp_name = temp_path.name + '.gz'

    attachment = message_handlers.EmailHandler._build_gzip_attachment(mocker.Mock(), temp_path)

    assert attachment.get_content_type() == 'application/x-gzip'
    assert attachment.get_content_disposition() == 'attachment'
    assert attachment.get_payload()

    # email_settings = {
    #     'smtpServer': 'foo.example',
    #     'smtpPort': 25,
    #     'from_address': 'foo@bar',
    #     'to_addresses': 'baz@bar',
    # }


def test_send_message_catches_missing_server(mocker):

    builder_mock = mocker.patch('supervisor.message_handlers.EmailHandler._build_message')
    email_settings = {
        'smtpPort': 25,
        'from_address': 'foo@bar',
        'to_addresses': 'baz@bar',
    }
    details = mocker.Mock()

    with pytest.warns(UserWarning):
        email_handler = message_handlers.EmailHandler(email_settings)
        email_handler.send_message(details)

    builder_mock.assert_not_called()


def test_send_message_catches_missing_port(mocker):

    builder_mock = mocker.patch('supervisor.message_handlers.EmailHandler._build_message')
    email_settings = {
        'smtpServer': 'foo.example',
        'from_address': 'foo@bar',
        'to_addresses': 'baz@bar',
    }
    details = mocker.Mock()

    with pytest.warns(UserWarning):
        email_handler = message_handlers.EmailHandler(email_settings)
        email_handler.send_message(details)

    builder_mock.assert_not_called()


def test_send_message_catches_missing_from_address(mocker):

    builder_mock = mocker.patch('supervisor.message_handlers.EmailHandler._build_message')
    email_settings = {
        'smtpServer': 'foo.example',
        'smtpPort': 25,
        'to_addresses': 'baz@bar',
    }
    details = mocker.Mock()

    with pytest.warns(UserWarning):
        email_handler = message_handlers.EmailHandler(email_settings)
        email_handler.send_message(details)

    builder_mock.assert_not_called()


def test_send_message_catches_missing_to_address(mocker):

    builder_mock = mocker.patch('supervisor.message_handlers.EmailHandler._build_message')
    email_settings = {
        'smtpServer': 'foo.example',
        'smtpPort': 25,
        'from_address': 'foo@bar',
    }
    details = mocker.Mock()

    with pytest.warns(UserWarning):
        email_handler = message_handlers.EmailHandler(email_settings)
        email_handler.send_message(details)

    builder_mock.assert_not_called()


def test_send_message_catches_blank_server(mocker):

    builder_mock = mocker.patch('supervisor.message_handlers.EmailHandler._build_message')
    email_settings = {
        'smtpServer': '',
        'smtpPort': 25,
        'from_address': 'foo@bar',
        'to_addresses': 'baz@bar',
    }
    details = mocker.Mock()

    with pytest.warns(UserWarning):
        email_handler = message_handlers.EmailHandler(email_settings)
        email_handler.send_message(details)

    builder_mock.assert_not_called()


def test_send_message_catches_blank_port(mocker):

    builder_mock = mocker.patch('supervisor.message_handlers.EmailHandler._build_message')
    email_settings = {
        'smtpServer': 'foo.example',
        'smtpPort': None,
        'from_address': 'foo@bar',
        'to_addresses': 'baz@bar',
    }
    details = mocker.Mock()

    with pytest.warns(UserWarning):
        email_handler = message_handlers.EmailHandler(email_settings)
        email_handler.send_message(details)

    builder_mock.assert_not_called()


def test_send_message_catches_blank_from_address(mocker):

    builder_mock = mocker.patch('supervisor.message_handlers.EmailHandler._build_message')
    email_settings = {
        'smtpServer': 'foo.example',
        'smtpPort': 25,
        'from_address': '',
        'to_addresses': 'baz@bar',
    }
    details = mocker.Mock()

    with pytest.warns(UserWarning):
        email_handler = message_handlers.EmailHandler(email_settings)
        email_handler.send_message(details)

    builder_mock.assert_not_called()


def test_send_message_catches_blank_to_address(mocker):

    builder_mock = mocker.patch('supervisor.message_handlers.EmailHandler._build_message')
    email_settings = {
        'smtpServer': 'foo.example',
        'smtpPort': 25,
        'from_address': 'foo@bar',
        'to_addresses': '',
    }
    details = mocker.Mock()

    with pytest.warns(UserWarning):
        email_handler = message_handlers.EmailHandler(email_settings)
        email_handler.send_message(details)

    builder_mock.assert_not_called()
