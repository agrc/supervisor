import base64
import zipfile
from base64 import b64encode
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import pytest
import sendgrid
from sendgrid.helpers.mail import attachment

from supervisor import message_handlers, models
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


def test_build_message_with_None_attachment(mocker):

    distribution_Mock = mocker.Mock()
    distribution_Mock.version = 0
    distributions = [distribution_Mock]
    mocker.patch('pkg_resources.require', return_value=distributions)

    message_details = MessageDetails()
    message_details.message = 'test_message'
    message_details.subject = 'test_subject'
    message_details.project_name = 'testing'
    message_details.attachments = [None]

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


def test_build_message_with_empty_str_attachment_path(mocker):

    distribution_Mock = mocker.Mock()
    distribution_Mock.version = 0
    distributions = [distribution_Mock]
    mocker.patch('pkg_resources.require', return_value=distributions)

    message_details = MessageDetails()
    message_details.message = 'test_message'
    message_details.subject = 'test_subject'
    message_details.project_name = 'testing'
    message_details.attachments = ['']

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


def test_gzip_not_called_for_empty_str_attachment_path(mocker):

    distribution_Mock = mocker.Mock()
    distribution_Mock.version = 0
    distributions = [distribution_Mock]
    mocker.patch('pkg_resources.require', return_value=distributions)

    message_details = MessageDetails()
    message_details.message = 'test_message'
    message_details.subject = 'test_subject'
    message_details.project_name = 'testing'
    message_details.attachments = ['']

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


class TestSendGridHandlerParts:

    def test_verify_addresses_normal(self, mocker):
        sendgrid_mock = mocker.Mock()
        sendgrid_mock.sendgrid_settings = {'from_address': 'foo@bar.com', 'to_addresses': 'cheddar@baz.com'}
        from_addr, to_addr = message_handlers.SendGridHandler._verify_addresses(sendgrid_mock)
        assert from_addr == 'foo@bar.com'
        assert to_addr == 'cheddar@baz.com'

    def test_verify_addresses_no_to_address(self, mocker):
        sendgrid_mock = mocker.Mock()
        sendgrid_mock.sendgrid_settings = {'from_address': 'foo@bar.com'}
        with pytest.warns(UserWarning, match='To/From address settings do not exist. No emails sent.'):
            from_addr, _ = message_handlers.SendGridHandler._verify_addresses(sendgrid_mock)
            assert from_addr is None

    def test_verify_addresses_no_from_address(self, mocker):
        sendgrid_mock = mocker.Mock()
        sendgrid_mock.sendgrid_settings = {'to_addresses': 'foo@bar.com'}
        with pytest.warns(UserWarning, match='To/From address settings do not exist. No emails sent.'):
            _, to_addr = message_handlers.SendGridHandler._verify_addresses(sendgrid_mock)
            assert to_addr is None

    def test_verify_addresses_empty_from_address(self, mocker):
        sendgrid_mock = mocker.Mock()
        sendgrid_mock.sendgrid_settings = {
            'from_address': '',
            'to_addresses': 'foo@bar.com',
        }
        with pytest.warns(UserWarning, match='To/From address settings exist but are empty. No emails sent.'):
            from_addr, _ = message_handlers.SendGridHandler._verify_addresses(sendgrid_mock)
            assert from_addr is None

    def test_verify_addresses_empty_to_address(self, mocker):
        sendgrid_mock = mocker.Mock()
        sendgrid_mock.sendgrid_settings = {
            'from_address': 'foo@bar.com',
            'to_addresses': '',
        }
        with pytest.warns(UserWarning, match='To/From address settings exist but are empty. No emails sent.'):
            _, to_addr = message_handlers.SendGridHandler._verify_addresses(sendgrid_mock)
            assert to_addr is None

    def test_build_recipient_addresses_one_addr(self, mocker):
        sendgrid_mock = mocker.Mock()
        to_addr = 'foo@bar.com'
        recipient_list = message_handlers.SendGridHandler._build_recipient_addresses(sendgrid_mock, to_addr)
        assert len(recipient_list) == 1
        assert recipient_list[0].email == 'foo@bar.com'

    def test_build_recipient_addresses_multiple_addrs(self, mocker):
        sendgrid_mock = mocker.Mock()
        to_addr = ['foo@bar.com', 'cheddar@baz.com']
        recipient_list = message_handlers.SendGridHandler._build_recipient_addresses(sendgrid_mock, to_addr)
        assert len(recipient_list) == 2
        assert recipient_list[0].email == 'foo@bar.com'
        assert recipient_list[1].email == 'cheddar@baz.com'

    def test_build_subject_no_prefix(self, mocker):
        sendgrid_mock = mocker.Mock()
        sendgrid_mock.sendgrid_settings = {}
        message_details = models.MessageDetails()
        message_details.subject = 'Foo Subject'
        subject = message_handlers.SendGridHandler._build_subject(sendgrid_mock, message_details)
        assert subject == 'Foo Subject'

    def test_build_subject_add_prefix(self, mocker):
        sendgrid_mock = mocker.Mock()
        sendgrid_mock.sendgrid_settings = {}
        sendgrid_mock.sendgrid_settings['prefix'] = 'Bar Prefix—'
        message_details = models.MessageDetails()
        message_details.subject = 'Foo Subject'
        subject = message_handlers.SendGridHandler._build_subject(sendgrid_mock, message_details)
        assert subject == 'Bar Prefix—Foo Subject'

    def test_build_content_with_version(self, mocker):
        sendgrid_mock = mocker.Mock()

        distribution_Mock = mocker.Mock()
        distribution_Mock.version = 0
        distributions = [distribution_Mock]
        mocker.patch('pkg_resources.require', return_value=distributions)

        message_details = models.MessageDetails()
        message_details.message = 'This is a\nmessage with newlines'
        message_details.project_name = 'ProFoo'

        content_object = message_handlers.SendGridHandler._build_content(sendgrid_mock, message_details)
        assert content_object.content == 'This is a\nmessage with newlines\n\nProFoo version: 0'
        assert content_object.mime_type == 'text/plain'

    def test_build_content_without_version(self, mocker):
        sendgrid_mock = mocker.Mock()

        mocker.patch('pkg_resources.require', return_value=[])

        message_details = models.MessageDetails()
        message_details.message = 'This is a\nmessage with newlines'
        message_details.project_name = 'ProFoo'

        content_object = message_handlers.SendGridHandler._build_content(sendgrid_mock, message_details)
        assert content_object.content == 'This is a\nmessage with newlines'
        assert content_object.mime_type == 'text/plain'


class TestSendGridHandlerWhole:

    def test_send_message_blank_to_addr(self, mocker):

        sendgrid_settings = {
            'from_address': 'foo@bar.com',
            'to_addresses': '',
            'api_key': 'itsasecret',
        }
        recipient_mock = mocker.patch.object(message_handlers.SendGridHandler, '_build_recipient_addresses')
        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings)

        message_details = models.MessageDetails()

        with pytest.warns(UserWarning, match='To/From address settings exist but are empty. No emails sent.'):
            sendgrid_handler.send_message(message_details)
            recipient_mock.assert_not_called()

    def test_send_message_blank_from_addr(self, mocker):

        sendgrid_settings = {
            'from_address': '',
            'to_addresses': 'foo@bar.com',
            'api_key': 'itsasecret',
        }
        recipient_mock = mocker.patch.object(message_handlers.SendGridHandler, '_build_recipient_addresses')
        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings)

        message_details = models.MessageDetails()

        with pytest.warns(UserWarning, match='To/From address settings exist but are empty. No emails sent.'):
            sendgrid_handler.send_message(message_details)
            recipient_mock.assert_not_called()

    def test_send_message_full_integration_with_version(self, mocker):

        sg_api_mock = mocker.patch('sendgrid.SendGridAPIClient')

        distribution_Mock = mocker.Mock()
        distribution_Mock.version = 3.14
        distributions = [distribution_Mock]
        mocker.patch('pkg_resources.require', return_value=distributions)

        sendgrid_settings = {
            'from_address': 'foo@example.com',
            'to_addresses': 'cheddar@example.com',
            'api_key': 'itsasecret',
        }

        message_details = models.MessageDetails()
        message_details.message = 'This is a\nmulti-line\nmessage'
        message_details.project_name = 'ProFoo'

        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings)

        sendgrid_handler.send_message(message_details)

        request_body = sendgrid_handler.sendgrid_client.client.mail.send.post.call_args[1]['request_body']
        assert request_body['from']['email'] == 'foo@example.com'
        assert request_body['personalizations'][0]['to'][0]['email'] == 'cheddar@example.com'
        assert request_body['content'][0]['type'] == 'text/plain'
        assert request_body['content'][0]['value'] == 'This is a\nmulti-line\nmessage\n\nProFoo version: 3.14'
        assert 'attachments' not in request_body

    def test_send_message_full_integration_with_single_file_attachment(self, mocker, tmp_path):

        sg_api_mock = mocker.patch('sendgrid.SendGridAPIClient')

        distribution_Mock = mocker.Mock()
        distribution_Mock.version = 3.14
        distributions = [distribution_Mock]
        mocker.patch('pkg_resources.require', return_value=distributions)

        sendgrid_settings = {
            'from_address': 'foo@example.com',
            'to_addresses': 'cheddar@example.com',
            'api_key': 'itsasecret',
        }

        att_path = tmp_path
        temp_a = att_path / 'single.txt'
        temp_a.write_text('single')

        message_details = models.MessageDetails()
        message_details.message = 'This is a\nmulti-line\nmessage'
        message_details.project_name = 'ProFoo'
        message_details.attachments = [temp_a]

        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings)

        sendgrid_handler.send_message(message_details)

        request_body = sendgrid_handler.sendgrid_client.client.mail.send.post.call_args[1]['request_body']
        assert request_body['from']['email'] == 'foo@example.com'
        assert request_body['personalizations'][0]['to'][0]['email'] == 'cheddar@example.com'
        assert request_body['content'][0]['type'] == 'text/plain'
        assert request_body['content'][0]['value'] == 'This is a\nmulti-line\nmessage\n\nProFoo version: 3.14'
        assert request_body['attachments'][0]['filename'] == temp_a.with_suffix('.zip').name

    def test_send_message_full_integration_with_directory_attachment(self, mocker, tmp_path):

        sg_api_mock = mocker.patch('sendgrid.SendGridAPIClient')

        distribution_Mock = mocker.Mock()
        distribution_Mock.version = 3.14
        distributions = [distribution_Mock]
        mocker.patch('pkg_resources.require', return_value=distributions)

        sendgrid_settings = {
            'from_address': 'foo@example.com',
            'to_addresses': 'cheddar@example.com',
            'api_key': 'itsasecret',
        }

        working_dir = tmp_path
        dir_to_be_attached = working_dir / 'zipme'
        dir_to_be_attached.mkdir()
        temp_a = dir_to_be_attached / 'a.txt'
        temp_a.write_text('a')
        temp_b = dir_to_be_attached / 'b.txt'
        temp_b.write_text('b')

        message_details = models.MessageDetails()
        message_details.message = 'This is a\nmulti-line\nmessage'
        message_details.project_name = 'ProFoo'
        message_details.attachments = [dir_to_be_attached]

        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings)

        sendgrid_handler.send_message(message_details)

        request_body = sendgrid_handler.sendgrid_client.client.mail.send.post.call_args[1]['request_body']
        assert request_body['from']['email'] == 'foo@example.com'
        assert request_body['personalizations'][0]['to'][0]['email'] == 'cheddar@example.com'
        assert request_body['content'][0]['type'] == 'text/plain'
        assert request_body['content'][0]['value'] == 'This is a\nmulti-line\nmessage\n\nProFoo version: 3.14'
        assert request_body['attachments'][0]['filename'] == dir_to_be_attached.with_suffix('.zip').name

    def test_send_message_full_integration_with_directory_and_single_file_attachments(self, mocker, tmp_path):

        sg_api_mock = mocker.patch('sendgrid.SendGridAPIClient')

        distribution_Mock = mocker.Mock()
        distribution_Mock.version = 3.14
        distributions = [distribution_Mock]
        mocker.patch('pkg_resources.require', return_value=distributions)

        sendgrid_settings = {
            'from_address': 'foo@example.com',
            'to_addresses': 'cheddar@example.com',
            'api_key': 'itsasecret',
        }

        working_dir = tmp_path

        single_file = working_dir / 'single.txt'
        single_file.write_text('single')

        dir_to_be_attached = working_dir / 'zipme'
        dir_to_be_attached.mkdir()
        temp_a = dir_to_be_attached / 'a.txt'
        temp_a.write_text('a')
        temp_b = dir_to_be_attached / 'b.txt'
        temp_b.write_text('b')

        message_details = models.MessageDetails()
        message_details.message = 'This is a\nmulti-line\nmessage'
        message_details.project_name = 'ProFoo'
        message_details.attachments = [dir_to_be_attached, single_file]

        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings)

        sendgrid_handler.send_message(message_details)

        request_body = sendgrid_handler.sendgrid_client.client.mail.send.post.call_args[1]['request_body']
        assert request_body['from']['email'] == 'foo@example.com'
        assert request_body['personalizations'][0]['to'][0]['email'] == 'cheddar@example.com'
        assert request_body['content'][0]['type'] == 'text/plain'
        assert request_body['content'][0]['value'] == 'This is a\nmulti-line\nmessage\n\nProFoo version: 3.14'
        attachment_names = [att['filename'] for att in request_body['attachments']]
        # assert request_body['attachments'][0]['filename'] == dir_to_be_attached.with_suffix('.zip').name
        # assert request_body['attachments'][1]['filename'] == single_file.with_suffix('.zip').name
        assert dir_to_be_attached.with_suffix('.zip').name in attachment_names
        assert single_file.with_suffix('.zip').name in attachment_names

    def test_send_message_full_integration_with_single_file_and_directory_attachments(self, mocker, tmp_path):

        sg_api_mock = mocker.patch('sendgrid.SendGridAPIClient')

        distribution_Mock = mocker.Mock()
        distribution_Mock.version = 3.14
        distributions = [distribution_Mock]
        mocker.patch('pkg_resources.require', return_value=distributions)

        sendgrid_settings = {
            'from_address': 'foo@example.com',
            'to_addresses': 'cheddar@example.com',
            'api_key': 'itsasecret',
        }

        working_dir = tmp_path

        single_file = working_dir / 'single.txt'
        single_file.write_text('single')

        dir_to_be_attached = working_dir / 'zipme'
        dir_to_be_attached.mkdir()
        temp_a = dir_to_be_attached / 'a.txt'
        temp_a.write_text('a')
        temp_b = dir_to_be_attached / 'b.txt'
        temp_b.write_text('b')

        message_details = models.MessageDetails()
        message_details.message = 'This is a\nmulti-line\nmessage'
        message_details.project_name = 'ProFoo'
        message_details.attachments = [single_file, dir_to_be_attached]

        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings)

        sendgrid_handler.send_message(message_details)

        request_body = sendgrid_handler.sendgrid_client.client.mail.send.post.call_args[1]['request_body']
        assert request_body['from']['email'] == 'foo@example.com'
        assert request_body['personalizations'][0]['to'][0]['email'] == 'cheddar@example.com'
        assert request_body['content'][0]['type'] == 'text/plain'
        assert request_body['content'][0]['value'] == 'This is a\nmulti-line\nmessage\n\nProFoo version: 3.14'
        attachment_names = [att['filename'] for att in request_body['attachments']]
        # assert request_body['attachments'][0]['filename'] == dir_to_be_attached.with_suffix('.zip').name
        # assert request_body['attachments'][1]['filename'] == single_file.with_suffix('.zip').name
        assert dir_to_be_attached.with_suffix('.zip').name in attachment_names
        assert single_file.with_suffix('.zip').name in attachment_names


class TestSendGridHandlerAttachments:

    def test_process_attachments_dispatches_single_file(self, mocker, tmp_path):
        temp_file = tmp_path / 'test.txt'
        temp_file.write_text('test_process_attachments_single_file')

        def _build_attachment_side_effect(value):
            return value

        sendgrid_mock = mocker.Mock()
        sendgrid_mock._zip_whole_directory.return_value = 'directory call'
        sendgrid_mock._zip_single_file.return_value = 'single file call'
        sendgrid_mock._build_attachment.side_effect = _build_attachment_side_effect

        attachments = message_handlers.SendGridHandler._process_attachments(sendgrid_mock, [temp_file])

        sendgrid_mock._zip_whole_directory.assert_not_called()
        sendgrid_mock._zip_single_file.assert_called_once()
        assert attachments == ['single file call']

    def test_process_attachments_dispatches_directory(self, mocker, tmp_path):

        def _build_attachment_side_effect(value):
            return value

        sendgrid_mock = mocker.Mock()
        sendgrid_mock._zip_whole_directory.return_value = 'directory call'
        sendgrid_mock._zip_single_file.return_value = 'single file call'
        sendgrid_mock._build_attachment.side_effect = _build_attachment_side_effect

        attachments = message_handlers.SendGridHandler._process_attachments(sendgrid_mock, [tmp_path])

        sendgrid_mock._zip_whole_directory.assert_called_once()
        sendgrid_mock._zip_single_file.assert_not_called()
        assert attachments == ['directory call']

    def test_process_attachments_dispatches_both_file_and_directory(self, mocker, tmp_path):
        temp_file = tmp_path / 'test.txt'
        temp_file.write_text('test_process_attachments_single_file')

        def _build_attachment_side_effect(value):
            return value

        sendgrid_mock = mocker.Mock()
        sendgrid_mock._zip_whole_directory.return_value = 'directory call'
        sendgrid_mock._zip_single_file.return_value = 'single file call'
        sendgrid_mock._build_attachment.side_effect = _build_attachment_side_effect

        attachments = message_handlers.SendGridHandler._process_attachments(sendgrid_mock, [temp_file, tmp_path])

        sendgrid_mock._zip_whole_directory.assert_called_once()
        sendgrid_mock._zip_single_file.assert_called_once()
        assert attachments == ['single file call', 'directory call']

    def test_process_attachments_dispatches_no_attachments(self, mocker):
        sendgrid_mock = mocker.Mock()
        sendgrid_mock._zip_whole_directory.return_value = 'directory call'
        sendgrid_mock._zip_single_file.return_value = 'single file call'

        attachments = message_handlers.SendGridHandler._process_attachments(sendgrid_mock, [])

        sendgrid_mock._zip_whole_directory.assert_not_called()
        sendgrid_mock._zip_single_file.assert_not_called()
        assert attachments == []

    def test_process_attachments_zips_both_directory_and_single_file(self, mocker, tmp_path):
        working_dir = tmp_path
        dir_to_be_zipped = working_dir / 'zipme'
        dir_to_be_zipped.mkdir()
        temp_a = dir_to_be_zipped / 'a.txt'
        temp_a.write_text('a')
        temp_b = dir_to_be_zipped / 'b.txt'
        temp_b.write_text('b')

        single_file_to_be_zipped = working_dir / 'single.txt'
        single_file_to_be_zipped.write_text('single file')

        def _build_attachment_side_effect(self_obj, value):
            return value

        attachment_mock = mocker.patch.object(
            message_handlers.SendGridHandler, '_build_attachment', _build_attachment_side_effect
        )
        sendgrid_settings = {'api_key': 'itsasecret'}
        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings)

        attachments = sendgrid_handler._process_attachments([dir_to_be_zipped, single_file_to_be_zipped])

        assert len(attachments) == 2
        att_names = [Path(f).name for f in attachments]
        assert 'zipme.zip' in att_names
        assert 'single.zip' in att_names

    def test_process_attachments_zips_both_single_file_and_directory(self, mocker, tmp_path):
        working_dir = tmp_path
        dir_to_be_zipped = working_dir / 'zipme'
        dir_to_be_zipped.mkdir()
        temp_a = dir_to_be_zipped / 'a.txt'
        temp_a.write_text('a')
        temp_b = dir_to_be_zipped / 'b.txt'
        temp_b.write_text('b')

        single_file_to_be_zipped = working_dir / 'single.txt'
        single_file_to_be_zipped.write_text('single file')

        def _build_attachment_side_effect(self_obj, value):
            return value

        attachment_mock = mocker.patch.object(
            message_handlers.SendGridHandler, '_build_attachment', _build_attachment_side_effect
        )
        sendgrid_settings = {'api_key': 'itsasecret'}
        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings)

        attachments = sendgrid_handler._process_attachments([single_file_to_be_zipped, dir_to_be_zipped])

        assert len(attachments) == 2
        att_names = [Path(f).name for f in attachments]
        assert 'zipme.zip' in att_names
        assert 'single.zip' in att_names

    def test_zip_whole_directory(self, mocker, tmp_path):
        working_dir = tmp_path
        dir_to_be_zipped = working_dir / 'zipme'
        dir_to_be_zipped.mkdir()
        temp_a = dir_to_be_zipped / 'a.txt'
        temp_a.write_text('a')
        temp_b = dir_to_be_zipped / 'b.txt'
        temp_b.write_text('b')

        sendgrid_mock = mocker.Mock()

        zipped_path = message_handlers.SendGridHandler._zip_whole_directory(
            sendgrid_mock, working_dir, dir_to_be_zipped
        )

        assert zipfile.ZipFile(zipped_path).namelist() == ['zipme/', 'zipme/a.txt', 'zipme/b.txt']

    def test_zip_single_file(self, mocker, tmp_path):
        working_dir = tmp_path
        temp_a = working_dir / 'a.txt'
        temp_a.write_text('a')
        sendgrid_mock = mocker.Mock()

        with TemporaryDirectory() as temp_dir:
            zipped_path = message_handlers.SendGridHandler._zip_single_file(sendgrid_mock, temp_dir, temp_a)

            assert zipfile.ZipFile(zipped_path).namelist() == ['a.txt']

    def test_build_attachment_mock_file(self, mocker):
        mock_open = mock.mock_open(read_data=b'test data')
        sendgrid_mock = mocker.Mock()

        with mock.patch('builtins.open', mock_open):
            attachment = message_handlers.SendGridHandler._build_attachment(sendgrid_mock, 'foo')

            assert attachment.file_name.get() == 'foo'
            assert attachment.file_type.get() == 'application/zip'
            assert attachment.file_content.get() == base64.b64encode(b'test data').decode()

    def test_build_attachment_single_file(self, mocker, tmp_path):
        working_dir = tmp_path
        temp_a = working_dir / 'a.txt'
        temp_a.write_text('a')

        sendgrid_mock = mocker.Mock()

        with TemporaryDirectory() as temp_dir:
            single_zip_path = message_handlers.SendGridHandler._zip_single_file(sendgrid_mock, temp_dir, temp_a)

            with open(single_zip_path, 'rb') as single_zip_file:
                data = single_zip_file.read()
            encoded = b64encode(data).decode()

            attachment = message_handlers.SendGridHandler._build_attachment(sendgrid_mock, single_zip_path)

            assert attachment.file_name.get() == 'a.zip'
            assert attachment.file_type.get() == 'application/zip'
            assert attachment.file_content.get() == encoded

    def test_build_attachment_directory(self, mocker, tmp_path):
        working_dir = tmp_path
        dir_to_be_zipped = working_dir / 'zipme'
        dir_to_be_zipped.mkdir()
        temp_a = dir_to_be_zipped / 'a.txt'
        temp_a.write_text('a')
        temp_b = dir_to_be_zipped / 'b.txt'
        temp_b.write_text('b')

        sendgrid_mock = mocker.Mock()
        dir_zip_path = message_handlers.SendGridHandler._zip_whole_directory(
            sendgrid_mock, working_dir, dir_to_be_zipped
        )

        with open(dir_zip_path, 'rb') as dir_zip_file:
            data = dir_zip_file.read()
        encoded = b64encode(data).decode()

        attachment = message_handlers.SendGridHandler._build_attachment(sendgrid_mock, dir_zip_path)

        assert attachment.file_name.get() == 'zipme.zip'
        assert attachment.file_type.get() == 'application/zip'
        assert attachment.file_content.get() == encoded
