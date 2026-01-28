import base64
import zipfile
from base64 import b64encode
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import pytest
import python_http_client

from supervisor import message_handlers, models
from supervisor.models import MessageDetails


def test_console_handler_prints(mocker, capsys):
    handler_mock = mocker.Mock()
    message_details = MessageDetails()
    message_details.message = "foo"
    message_handlers.ConsoleHandler.send_message(handler_mock, message_details)

    captured = capsys.readouterr()

    assert captured.out == "foo\n"


def test_build_message_without_attachments(mocker):
    message_details = MessageDetails()
    message_details.message = "test_message"
    message_details.subject = "test_subject"

    handler_mock = mocker.Mock()
    handler_mock.email_settings = {
        "to_addresses": "foo@example.com",
        "from_address": "testing@example.com",
    }
    handler_mock.client_name = "testing"
    handler_mock.client_version = 0

    test_message = message_handlers.EmailHandler._build_message(handler_mock, message_details)

    assert test_message.get("Subject") == "test_subject"
    assert test_message.get("To") == "foo@example.com"
    assert test_message.get("From") == "testing@example.com"
    assert test_message.get_payload()[0].get_payload() == "test_message"
    assert test_message.get_payload()[1].get_payload() == "<p>testing version: 0</p>"


def test_build_message_with_None_attachment(mocker):
    message_details = MessageDetails()
    message_details.message = "test_message"
    message_details.subject = "test_subject"
    message_details.attachments = [None]

    handler_mock = mocker.Mock()
    handler_mock.email_settings = {
        "to_addresses": "foo@example.com",
        "from_address": "testing@example.com",
    }
    handler_mock.client_name = "testing"
    handler_mock.client_version = 0

    test_message = message_handlers.EmailHandler._build_message(handler_mock, message_details)

    assert test_message.get("Subject") == "test_subject"
    assert test_message.get("To") == "foo@example.com"
    assert test_message.get("From") == "testing@example.com"
    assert test_message.get_payload()[0].get_payload() == "test_message"
    assert test_message.get_payload()[1].get_payload() == "<p>testing version: 0</p>"


def test_build_message_with_empty_str_attachment_path(mocker):
    message_details = MessageDetails()
    message_details.message = "test_message"
    message_details.subject = "test_subject"
    message_details.attachments = [""]

    handler_mock = mocker.Mock()
    handler_mock.email_settings = {
        "to_addresses": "foo@example.com",
        "from_address": "testing@example.com",
    }
    handler_mock.client_name = "testing"
    handler_mock.client_version = 0

    test_message = message_handlers.EmailHandler._build_message(handler_mock, message_details)

    assert test_message.get("Subject") == "test_subject"
    assert test_message.get("To") == "foo@example.com"
    assert test_message.get("From") == "testing@example.com"
    assert test_message.get_payload()[0].get_payload() == "test_message"
    assert test_message.get_payload()[1].get_payload() == "<p>testing version: 0</p>"


def test_build_message_with_subject_prefix(mocker):
    message_details = MessageDetails()
    message_details.message = "test_message"
    message_details.subject = "test_subject"

    handler_mock = mocker.Mock()
    handler_mock.email_settings = {
        "to_addresses": "foo@example.com",
        "from_address": "testing@example.com",
        "prefix": "test prefix: ",
    }
    handler_mock.client_name = "testing"
    handler_mock.client_version = 0

    test_message = message_handlers.EmailHandler._build_message(handler_mock, message_details)

    assert test_message.get("Subject") == "test prefix: test_subject"
    assert test_message.get("To") == "foo@example.com"
    assert test_message.get("From") == "testing@example.com"
    assert test_message.get_payload()[0].get_payload() == "test_message"
    assert test_message.get_payload()[1].get_payload() == "<p>testing version: 0</p>"


def test_build_message_with_multiple_to_addresses(mocker):
    message_details = MessageDetails()
    message_details.message = "test_message"
    message_details.subject = "test_subject"

    handler_mock = mocker.Mock()
    handler_mock.email_settings = {
        "to_addresses": ["foo@example.com", "bar@example.com", "baz@example.com"],
        "from_address": "testing@example.com",
    }
    handler_mock.client_name = "testing"
    handler_mock.client_version = 0

    test_message = message_handlers.EmailHandler._build_message(handler_mock, message_details)

    assert test_message.get("Subject") == "test_subject"
    assert test_message.get("To") == "foo@example.com,bar@example.com,baz@example.com"
    assert test_message.get("From") == "testing@example.com"
    assert test_message.get_payload()[0].get_payload() == "test_message"
    assert test_message.get_payload()[1].get_payload() == "<p>testing version: 0</p>"


def test_gzip_not_called_for_non_existent_attachments(mocker, tmp_path):
    distribution_Mock = mocker.Mock()
    distribution_Mock.version = 0
    distributions = [distribution_Mock]
    mocker.patch("pkg_resources.require", return_value=distributions)

    message_details = MessageDetails()
    message_details.message = "test_message"
    message_details.subject = "test_subject"
    message_details.project_name = "testing"
    message_details.attachments = [
        tmp_path / "att1",
    ]

    handler_mock = mocker.Mock()
    handler_mock.email_settings = {
        "to_addresses": "foo@example.com",
        "from_address": "testing@example.com",
    }

    message_handlers.EmailHandler._build_message(handler_mock, message_details)

    assert not handler_mock._build_gzip_attachment.called


def test_gzip_not_called_for_empty_str_attachment_path(mocker):
    distribution_Mock = mocker.Mock()
    distribution_Mock.version = 0
    distributions = [distribution_Mock]
    mocker.patch("pkg_resources.require", return_value=distributions)

    message_details = MessageDetails()
    message_details.message = "test_message"
    message_details.subject = "test_subject"
    message_details.project_name = "testing"
    message_details.attachments = [""]

    handler_mock = mocker.Mock()
    handler_mock.email_settings = {
        "to_addresses": "foo@example.com",
        "from_address": "testing@example.com",
    }

    message_handlers.EmailHandler._build_message(handler_mock, message_details)

    assert not handler_mock._build_gzip_attachment.called


def test_gzip_called_3_times_for_3_attachments(mocker, tmp_path):
    distribution_Mock = mocker.Mock()
    distribution_Mock.version = 0
    distributions = [distribution_Mock]
    mocker.patch("pkg_resources.require", return_value=distributions)

    attributes = []
    for i in range(1, 4):
        path = tmp_path / f"att{i}"
        with open(path, "w") as attribute_file:
            attribute_file.write(f"att{i}")
        attributes.append(path)

    message_details = MessageDetails()
    message_details.message = "test_message"
    message_details.subject = "test_subject"
    message_details.project_name = "testing"
    message_details.attachments.extend(attributes)

    handler_mock = mocker.Mock()
    handler_mock.email_settings = {
        "to_addresses": "foo@example.com",
        "from_address": "testing@example.com",
    }

    message_handlers.EmailHandler._build_message(handler_mock, message_details)

    assert handler_mock._build_gzip_attachment.call_count == 3


def test_gzip(mocker, tmp_path):
    # with BytesIO(b'test text') as test_bytes:
    #     # mocker.patch.object(message_handlers.EmailHandler._build_gzip_attachment, 'input_file_object', test_bytes)
    #     mocker.patch('sys.open', return_value=test_bytes)

    temp_path = tmp_path / "test"
    with open(temp_path, "w") as temp_file:
        temp_file.write("test text")
    # temp_name = temp_path.name + ".gz"

    attachment = message_handlers.EmailHandler._build_gzip_attachment(temp_path)

    assert attachment.get_content_type() == "application/x-gzip"
    assert attachment.get_content_disposition() == "attachment"
    assert attachment.get_payload()

    # email_settings = {
    #     'smtpServer': 'foo.example',
    #     'smtpPort': 25,
    #     'from_address': 'foo@bar',
    #     'to_addresses': 'baz@bar',
    # }


def test_send_message_catches_missing_server(mocker):
    builder_mock = mocker.patch("supervisor.message_handlers.EmailHandler._build_message")
    email_settings = {
        "smtpPort": 25,
        "from_address": "foo@bar",
        "to_addresses": "baz@bar",
    }
    details = mocker.Mock()

    with pytest.warns(UserWarning):
        email_handler = message_handlers.EmailHandler(email_settings)
        email_handler.send_message(details)

    builder_mock.assert_not_called()


def test_send_message_catches_missing_port(mocker):
    builder_mock = mocker.patch("supervisor.message_handlers.EmailHandler._build_message")
    email_settings = {
        "smtpServer": "foo.example",
        "from_address": "foo@bar",
        "to_addresses": "baz@bar",
    }
    details = mocker.Mock()

    with pytest.warns(UserWarning):
        email_handler = message_handlers.EmailHandler(email_settings)
        email_handler.send_message(details)

    builder_mock.assert_not_called()


def test_send_message_catches_missing_from_address(mocker):
    builder_mock = mocker.patch("supervisor.message_handlers.EmailHandler._build_message")
    email_settings = {
        "smtpServer": "foo.example",
        "smtpPort": 25,
        "to_addresses": "baz@bar",
    }
    details = mocker.Mock()

    with pytest.warns(UserWarning):
        email_handler = message_handlers.EmailHandler(email_settings)
        email_handler.send_message(details)

    builder_mock.assert_not_called()


def test_send_message_catches_missing_to_address(mocker):
    builder_mock = mocker.patch("supervisor.message_handlers.EmailHandler._build_message")
    email_settings = {
        "smtpServer": "foo.example",
        "smtpPort": 25,
        "from_address": "foo@bar",
    }
    details = mocker.Mock()

    with pytest.warns(UserWarning):
        email_handler = message_handlers.EmailHandler(email_settings)
        email_handler.send_message(details)

    builder_mock.assert_not_called()


def test_send_message_catches_blank_server(mocker):
    builder_mock = mocker.patch("supervisor.message_handlers.EmailHandler._build_message")
    email_settings = {
        "smtpServer": "",
        "smtpPort": 25,
        "from_address": "foo@bar",
        "to_addresses": "baz@bar",
    }
    details = mocker.Mock()

    with pytest.warns(UserWarning):
        email_handler = message_handlers.EmailHandler(email_settings)
        email_handler.send_message(details)

    builder_mock.assert_not_called()


def test_send_message_catches_blank_port(mocker):
    builder_mock = mocker.patch("supervisor.message_handlers.EmailHandler._build_message")
    email_settings = {
        "smtpServer": "foo.example",
        "smtpPort": None,
        "from_address": "foo@bar",
        "to_addresses": "baz@bar",
    }
    details = mocker.Mock()

    with pytest.warns(UserWarning):
        email_handler = message_handlers.EmailHandler(email_settings)
        email_handler.send_message(details)

    builder_mock.assert_not_called()


def test_send_message_catches_blank_from_address(mocker):
    builder_mock = mocker.patch("supervisor.message_handlers.EmailHandler._build_message")
    email_settings = {
        "smtpServer": "foo.example",
        "smtpPort": 25,
        "from_address": "",
        "to_addresses": "baz@bar",
    }
    details = mocker.Mock()

    with pytest.warns(UserWarning):
        email_handler = message_handlers.EmailHandler(email_settings)
        email_handler.send_message(details)

    builder_mock.assert_not_called()


def test_send_message_catches_blank_to_address(mocker):
    builder_mock = mocker.patch("supervisor.message_handlers.EmailHandler._build_message")
    email_settings = {
        "smtpServer": "foo.example",
        "smtpPort": 25,
        "from_address": "foo@bar",
        "to_addresses": "",
    }
    details = mocker.Mock()

    with pytest.warns(UserWarning):
        email_handler = message_handlers.EmailHandler(email_settings)
        email_handler.send_message(details)

    builder_mock.assert_not_called()


class TestSendGridHandlerParts:
    def test_verify_addresses_normal(self, mocker):
        sendgrid_mock = mocker.Mock()
        sendgrid_mock.sendgrid_settings = {"from_address": "foo@bar.com", "to_addresses": "cheddar@baz.com"}
        from_addr, to_addr = message_handlers.SendGridHandler._verify_addresses(sendgrid_mock)
        assert from_addr == "foo@bar.com"
        assert to_addr == "cheddar@baz.com"

    def test_verify_addresses_no_to_address(self, mocker):
        sendgrid_mock = mocker.Mock()
        sendgrid_mock.sendgrid_settings = {"from_address": "foo@bar.com"}
        with pytest.warns(UserWarning, match="To/From address settings do not exist. No emails sent."):
            from_addr, _ = message_handlers.SendGridHandler._verify_addresses(sendgrid_mock)
            assert from_addr is None

    def test_verify_addresses_no_from_address(self, mocker):
        sendgrid_mock = mocker.Mock()
        sendgrid_mock.sendgrid_settings = {"to_addresses": "foo@bar.com"}
        with pytest.warns(UserWarning, match="To/From address settings do not exist. No emails sent."):
            _, to_addr = message_handlers.SendGridHandler._verify_addresses(sendgrid_mock)
            assert to_addr is None

    def test_verify_addresses_empty_from_address(self, mocker):
        sendgrid_mock = mocker.Mock()
        sendgrid_mock.sendgrid_settings = {
            "from_address": "",
            "to_addresses": "foo@bar.com",
        }
        with pytest.warns(UserWarning, match="To/From address settings exist but are empty. No emails sent."):
            from_addr, _ = message_handlers.SendGridHandler._verify_addresses(sendgrid_mock)
            assert from_addr is None

    def test_verify_addresses_empty_to_address(self, mocker):
        sendgrid_mock = mocker.Mock()
        sendgrid_mock.sendgrid_settings = {
            "from_address": "foo@bar.com",
            "to_addresses": "",
        }
        with pytest.warns(UserWarning, match="To/From address settings exist but are empty. No emails sent."):
            _, to_addr = message_handlers.SendGridHandler._verify_addresses(sendgrid_mock)
            assert to_addr is None

    def test_build_recipient_addresses_one_addr(self, mocker):
        to_addr = "foo@bar.com"
        recipient_list = message_handlers.SendGridHandler._build_recipient_addresses(to_addr)
        assert len(recipient_list) == 1
        assert recipient_list[0].email == "foo@bar.com"

    def test_build_recipient_addresses_multiple_addresses(self, mocker):
        to_addr = ["foo@bar.com", "cheddar@baz.com"]
        recipient_list = message_handlers.SendGridHandler._build_recipient_addresses(to_addr)
        assert len(recipient_list) == 2
        assert recipient_list[0].email == "foo@bar.com"
        assert recipient_list[1].email == "cheddar@baz.com"

    def test_build_subject_no_prefix(self, mocker):
        sendgrid_mock = mocker.Mock()
        sendgrid_mock.sendgrid_settings = {}
        message_details = models.MessageDetails()
        message_details.subject = "Foo Subject"
        subject = message_handlers.SendGridHandler._build_subject(sendgrid_mock, message_details)
        assert subject == "Foo Subject"

    def test_build_subject_add_prefix(self, mocker):
        sendgrid_mock = mocker.Mock()
        sendgrid_mock.sendgrid_settings = {}
        sendgrid_mock.sendgrid_settings["prefix"] = "Bar Prefix—"
        message_details = models.MessageDetails()
        message_details.subject = "Foo Subject"
        subject = message_handlers.SendGridHandler._build_subject(sendgrid_mock, message_details)
        assert subject == "Bar Prefix—Foo Subject"

    def test_build_content_with_version(self, mocker):
        message_details = models.MessageDetails()
        message_details.message = "This is a\nmessage with newlines"
        client_name = "ProFoo"
        client_version = 0

        content_object = message_handlers.SendGridHandler._build_content(
            message_details.message, client_name, client_version
        )
        assert content_object.content == "This is a\nmessage with newlines\n\nProFoo version: 0"
        assert content_object.mime_type == "text/plain"

    def test_verify_attachments_bad_Path_input(self, mocker):
        attachments = [3]

        error_message, attachments = message_handlers.SendGridHandler._verify_attachments(attachments)

        assert "Cannot get Path() of attachment" in error_message
        assert attachments == []

    def test_verify_attachments_Path_does_not_exist(self, mocker, tmp_path):
        bad_path = tmp_path / "bad.txt"

        attachments = [bad_path]

        error_message, attachments = message_handlers.SendGridHandler._verify_attachments(attachments)

        assert "does not exist" in error_message
        assert attachments == []

    def test_verify_attachments_good_Path(self, mocker, tmp_path):
        good_path = tmp_path / "a.txt"
        good_path.write_text("a")

        attachments = [good_path]

        error_message, attachments = message_handlers.SendGridHandler._verify_attachments(attachments)

        assert error_message == ""
        assert attachments == [Path(good_path)]

    def test_verify_attachments_good_Path_and_bad_Path_input(self, mocker, tmp_path):
        good_path = tmp_path / "a.txt"
        good_path.write_text("a")

        attachments = [good_path, 3]

        error_message, attachments = message_handlers.SendGridHandler._verify_attachments(attachments)

        assert "Cannot get Path() of attachment" in error_message
        assert attachments == [Path(good_path)]

    def test_verify_attachments_good_Path_and_Path_not_exist(self, mocker, tmp_path):
        good_path = tmp_path / "a.txt"
        good_path.write_text("a")
        bad_path = tmp_path / "b.txt"

        attachments = [good_path, bad_path]

        error_message, attachments = message_handlers.SendGridHandler._verify_attachments(attachments)

        assert "does not exist" in error_message
        assert attachments == [Path(good_path)]

    def test_verify_attachments_bad_Path_input_and_Path_not_exist(self, mocker, tmp_path):
        bad_path = tmp_path / "b.txt"

        attachments = [3, bad_path]

        error_message, attachments = message_handlers.SendGridHandler._verify_attachments(attachments)

        assert "does not exist" in error_message
        assert "Cannot get Path() of attachment" in error_message
        assert attachments == []


class TestSendGridHandlerWhole:
    def test_send_message_blank_to_addr(self, mocker):
        sendgrid_settings = {
            "from_address": "foo@bar.com",
            "to_addresses": "",
            "api_key": "its_a_secret",
        }
        recipient_mock = mocker.patch.object(message_handlers.SendGridHandler, "_build_recipient_addresses")
        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings)

        message_details = models.MessageDetails()

        with pytest.warns(UserWarning, match="To/From address settings exist but are empty. No emails sent."):
            sendgrid_handler.send_message(message_details)
            recipient_mock.assert_not_called()

    def test_send_message_blank_from_addr(self, mocker):
        sendgrid_settings = {
            "from_address": "",
            "to_addresses": "foo@bar.com",
            "api_key": "its_a_secret",
        }
        recipient_mock = mocker.patch.object(message_handlers.SendGridHandler, "_build_recipient_addresses")
        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings)

        message_details = models.MessageDetails()

        with pytest.warns(UserWarning, match="To/From address settings exist but are empty. No emails sent."):
            sendgrid_handler.send_message(message_details)
            recipient_mock.assert_not_called()

    def test_send_message_full_integration_catches_400_bad_request(self, mocker):
        distribution_Mock = mocker.Mock()
        distribution_Mock.version = 3.14
        distributions = [distribution_Mock]
        mocker.patch("pkg_resources.require", return_value=distributions)

        sendgrid_settings = {
            "from_address": "foo@example.com",
            "to_addresses": "cheddar@example.com",
            "api_key": "its_a_secret",
        }

        message_details = models.MessageDetails()
        message_details.message = "This is a\nmulti-line\nmessage"

        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings, "ProFoo")
        sendgrid_handler.sendgrid_client = mocker.Mock()
        sendgrid_handler.sendgrid_client.client.mail.send.post.side_effect = python_http_client.BadRequestsError(
            400, "HTTP Error 400: Bad Request", "body", "header"
        )

        with pytest.warns(
            UserWarning, match="SendGrid error 400, might be missing a required Mail component; no e-mail sent."
        ):
            sendgrid_handler.send_message(message_details)

    def test_send_message_full_integration_raises_400_other(self, mocker):
        distribution_Mock = mocker.Mock()
        distribution_Mock.version = 3.14
        distributions = [distribution_Mock]
        mocker.patch("pkg_resources.require", return_value=distributions)

        sendgrid_settings = {
            "from_address": "foo@example.com",
            "to_addresses": "cheddar@example.com",
            "api_key": "its_a_secret",
        }

        message_details = models.MessageDetails()
        message_details.message = "This is a\nmulti-line\nmessage"

        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings, "ProFoo")
        sendgrid_handler.sendgrid_client = mocker.Mock()
        sendgrid_handler.sendgrid_client.client.mail.send.post.side_effect = python_http_client.BadRequestsError(
            400, "HTTP Error 400: Unknown", "body", "header"
        )

        with pytest.raises(python_http_client.BadRequestsError, match="HTTP Error 400: Unknown"):
            sendgrid_handler.send_message(message_details)

    def test_send_message_full_integration_catches_401_unauthorized(self, mocker):
        distribution_Mock = mocker.Mock()
        distribution_Mock.version = 3.14
        distributions = [distribution_Mock]
        mocker.patch("pkg_resources.require", return_value=distributions)

        sendgrid_settings = {
            "from_address": "foo@example.com",
            "to_addresses": "cheddar@example.com",
            "api_key": "its_a_secret",
        }

        message_details = models.MessageDetails()
        message_details.message = "This is a\nmulti-line\nmessage"

        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings, "ProFoo")
        sendgrid_handler.sendgrid_client = mocker.Mock()
        sendgrid_handler.sendgrid_client.client.mail.send.post.side_effect = python_http_client.UnauthorizedError(
            401, "HTTP Error 401: Unauthorized", "body", "header"
        )

        with pytest.warns(UserWarning, match="SendGrid error 401: Unauthorized. Check API key."):
            sendgrid_handler.send_message(message_details)

    def test_send_message_full_integration_raises_401_other(self, mocker):
        distribution_Mock = mocker.Mock()
        distribution_Mock.version = 3.14
        distributions = [distribution_Mock]
        mocker.patch("pkg_resources.require", return_value=distributions)

        sendgrid_settings = {
            "from_address": "foo@example.com",
            "to_addresses": "cheddar@example.com",
            "api_key": "its_a_secret",
        }

        message_details = models.MessageDetails()
        message_details.message = "This is a\nmulti-line\nmessage"

        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings, "ProFoo")
        sendgrid_handler.sendgrid_client = mocker.Mock()
        sendgrid_handler.sendgrid_client.client.mail.send.post.side_effect = python_http_client.UnauthorizedError(
            401, "HTTP Error 401: Unknown", "body", "header"
        )

        with pytest.raises(python_http_client.UnauthorizedError, match="HTTP Error 401: Unknown"):
            sendgrid_handler.send_message(message_details)

    def test_send_message_full_integration_with_version(self, mocker):
        mocker.patch("sendgrid.SendGridAPIClient")

        sendgrid_settings = {
            "from_address": "foo@example.com",
            "to_addresses": "cheddar@example.com",
            "api_key": "its_a_secret",
        }

        message_details = models.MessageDetails()
        message_details.message = "This is a\nmulti-line\nmessage"

        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings, "ProFoo", "3.14")

        sendgrid_handler.send_message(message_details)

        request_body = sendgrid_handler.sendgrid_client.client.mail.send.post.call_args[1]["request_body"]
        assert request_body["from"]["email"] == "foo@example.com"
        assert request_body["personalizations"][0]["to"][0]["email"] == "cheddar@example.com"
        assert request_body["content"][0]["type"] == "text/plain"
        assert request_body["content"][0]["value"] == "This is a\nmulti-line\nmessage\n\nProFoo version: 3.14"
        assert "attachments" not in request_body

    def test_send_message_full_integration_with_single_file_attachment(self, mocker, tmp_path):
        mocker.patch("sendgrid.SendGridAPIClient")

        sendgrid_settings = {
            "from_address": "foo@example.com",
            "to_addresses": "cheddar@example.com",
            "api_key": "its_a_secret",
        }

        att_path = tmp_path
        temp_a = att_path / "single.txt"
        temp_a.write_text("single")

        message_details = models.MessageDetails()
        message_details.message = "This is a\nmulti-line\nmessage"
        message_details.attachments = [temp_a]

        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings, "ProFoo", "3.14")

        sendgrid_handler.send_message(message_details)

        request_body = sendgrid_handler.sendgrid_client.client.mail.send.post.call_args[1]["request_body"]
        assert request_body["from"]["email"] == "foo@example.com"
        assert request_body["personalizations"][0]["to"][0]["email"] == "cheddar@example.com"
        assert request_body["content"][0]["type"] == "text/plain"
        assert request_body["content"][0]["value"] == "This is a\nmulti-line\nmessage\n\nProFoo version: 3.14"
        assert request_body["attachments"][0]["filename"] == temp_a.with_suffix(".zip").name

    def test_send_message_full_integration_with_directory_attachment(self, mocker, tmp_path):
        mocker.patch("sendgrid.SendGridAPIClient")

        sendgrid_settings = {
            "from_address": "foo@example.com",
            "to_addresses": "cheddar@example.com",
            "api_key": "its_a_secret",
        }

        working_dir = tmp_path
        dir_to_be_attached = working_dir / "zip_me"
        dir_to_be_attached.mkdir()
        temp_a = dir_to_be_attached / "a.txt"
        temp_a.write_text("a")
        temp_b = dir_to_be_attached / "b.txt"
        temp_b.write_text("b")

        message_details = models.MessageDetails()
        message_details.message = "This is a\nmulti-line\nmessage"
        message_details.attachments = [dir_to_be_attached]

        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings, "ProFoo", "3.14")

        sendgrid_handler.send_message(message_details)

        request_body = sendgrid_handler.sendgrid_client.client.mail.send.post.call_args[1]["request_body"]
        assert request_body["from"]["email"] == "foo@example.com"
        assert request_body["personalizations"][0]["to"][0]["email"] == "cheddar@example.com"
        assert request_body["content"][0]["type"] == "text/plain"
        assert request_body["content"][0]["value"] == "This is a\nmulti-line\nmessage\n\nProFoo version: 3.14"
        assert request_body["attachments"][0]["filename"] == dir_to_be_attached.with_suffix(".zip").name

    def test_send_message_full_integration_with_directory_and_single_file_attachments(self, mocker, tmp_path):
        mocker.patch("sendgrid.SendGridAPIClient")

        sendgrid_settings = {
            "from_address": "foo@example.com",
            "to_addresses": "cheddar@example.com",
            "api_key": "its_a_secret",
        }

        working_dir = tmp_path

        single_file = working_dir / "single.txt"
        single_file.write_text("single")

        dir_to_be_attached = working_dir / "zip_me"
        dir_to_be_attached.mkdir()
        temp_a = dir_to_be_attached / "a.txt"
        temp_a.write_text("a")
        temp_b = dir_to_be_attached / "b.txt"
        temp_b.write_text("b")

        message_details = models.MessageDetails()
        message_details.message = "This is a\nmulti-line\nmessage"
        message_details.attachments = [dir_to_be_attached, single_file]

        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings, "ProFoo", "3.14")

        sendgrid_handler.send_message(message_details)

        request_body = sendgrid_handler.sendgrid_client.client.mail.send.post.call_args[1]["request_body"]
        assert request_body["from"]["email"] == "foo@example.com"
        assert request_body["personalizations"][0]["to"][0]["email"] == "cheddar@example.com"
        assert request_body["content"][0]["type"] == "text/plain"
        assert request_body["content"][0]["value"] == "This is a\nmulti-line\nmessage\n\nProFoo version: 3.14"
        attachment_names = [att["filename"] for att in request_body["attachments"]]
        assert dir_to_be_attached.with_suffix(".zip").name in attachment_names
        assert single_file.with_suffix(".zip").name in attachment_names

    def test_send_message_full_integration_with_single_file_and_directory_attachments(self, mocker, tmp_path):
        mocker.patch("sendgrid.SendGridAPIClient")

        sendgrid_settings = {
            "from_address": "foo@example.com",
            "to_addresses": "cheddar@example.com",
            "api_key": "its_a_secret",
        }

        working_dir = tmp_path

        single_file = working_dir / "single.txt"
        single_file.write_text("single")

        dir_to_be_attached = working_dir / "zip_me"
        dir_to_be_attached.mkdir()
        temp_a = dir_to_be_attached / "a.txt"
        temp_a.write_text("a")
        temp_b = dir_to_be_attached / "b.txt"
        temp_b.write_text("b")

        message_details = models.MessageDetails()
        message_details.message = "This is a\nmulti-line\nmessage"
        message_details.attachments = [single_file, dir_to_be_attached]

        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings, "ProFoo", "3.14")

        sendgrid_handler.send_message(message_details)

        request_body = sendgrid_handler.sendgrid_client.client.mail.send.post.call_args[1]["request_body"]
        assert request_body["from"]["email"] == "foo@example.com"
        assert request_body["personalizations"][0]["to"][0]["email"] == "cheddar@example.com"
        assert request_body["content"][0]["type"] == "text/plain"
        assert request_body["content"][0]["value"] == "This is a\nmulti-line\nmessage\n\nProFoo version: 3.14"
        attachment_names = [att["filename"] for att in request_body["attachments"]]
        assert dir_to_be_attached.with_suffix(".zip").name in attachment_names
        assert single_file.with_suffix(".zip").name in attachment_names

    def test_send_message_full_integration_with_non_existent_single_file_attachment(self, mocker, tmp_path):
        mocker.patch("sendgrid.SendGridAPIClient")

        sendgrid_settings = {
            "from_address": "foo@example.com",
            "to_addresses": "cheddar@example.com",
            "api_key": "its_a_secret",
        }

        bad_file = tmp_path / "bad.txt"

        message_details = models.MessageDetails()
        message_details.message = "This is a\nmulti-line\nmessage"
        message_details.attachments = [bad_file]

        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings, "ProFoo", "3.14")

        sendgrid_handler.send_message(message_details)

        request_body = sendgrid_handler.sendgrid_client.client.mail.send.post.call_args[1]["request_body"]
        assert request_body["from"]["email"] == "foo@example.com"
        assert request_body["personalizations"][0]["to"][0]["email"] == "cheddar@example.com"
        assert request_body["content"][0]["type"] == "text/plain"
        assert "This is a\nmulti-line\nmessage\n\nProFoo version: 3.14" in request_body["content"][0]["value"]
        assert "does not exist" in request_body["content"][0]["value"]
        assert "attachments" not in request_body

    def test_send_message_full_integration_with_non_path_single_file_attachment(self, mocker):
        mocker.patch("sendgrid.SendGridAPIClient")

        sendgrid_settings = {
            "from_address": "foo@example.com",
            "to_addresses": "cheddar@example.com",
            "api_key": "its_a_secret",
        }

        message_details = models.MessageDetails()
        message_details.message = "This is a\nmulti-line\nmessage"
        message_details.attachments = [3]

        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings, "ProFoo", "3.14")

        sendgrid_handler.send_message(message_details)

        request_body = sendgrid_handler.sendgrid_client.client.mail.send.post.call_args[1]["request_body"]
        assert request_body["from"]["email"] == "foo@example.com"
        assert request_body["personalizations"][0]["to"][0]["email"] == "cheddar@example.com"
        assert request_body["content"][0]["type"] == "text/plain"
        assert "This is a\nmulti-line\nmessage\n\nProFoo version: 3.14" in request_body["content"][0]["value"]
        assert "Cannot get Path() of attachment" in request_body["content"][0]["value"]
        assert "attachments" not in request_body

    def test_send_message_full_integration_with_good_and_bad_single_file_attachment(self, mocker, tmp_path):
        mocker.patch("sendgrid.SendGridAPIClient")

        sendgrid_settings = {
            "from_address": "foo@example.com",
            "to_addresses": "cheddar@example.com",
            "api_key": "its_a_secret",
        }

        good_file = tmp_path / "good.txt"
        good_file.write_text("good")

        message_details = models.MessageDetails()
        message_details.message = "This is a\nmulti-line\nmessage"
        message_details.attachments = [good_file, 3]

        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings, "ProFoo", "3.14")

        sendgrid_handler.send_message(message_details)

        request_body = sendgrid_handler.sendgrid_client.client.mail.send.post.call_args[1]["request_body"]
        assert request_body["from"]["email"] == "foo@example.com"
        assert request_body["personalizations"][0]["to"][0]["email"] == "cheddar@example.com"
        assert request_body["content"][0]["type"] == "text/plain"
        assert "This is a\nmulti-line\nmessage\n\nProFoo version: 3.14" in request_body["content"][0]["value"]
        assert "Cannot get Path() of attachment" in request_body["content"][0]["value"]
        attachment_names = [att["filename"] for att in request_body["attachments"]]
        assert good_file.with_suffix(".zip").name in attachment_names


class TestSendGridHandlerAttachments:
    def test_process_attachments_dispatches_single_file(self, mocker, tmp_path):
        temp_file = tmp_path / "test.txt"
        temp_file.write_text("test_process_attachments_single_file")

        def _build_attachment_side_effect(value):
            return value

        sendgrid_mock = mocker.Mock()
        sendgrid_mock._zip_whole_directory.return_value = "directory call"
        sendgrid_mock._zip_single_file.return_value = "single file call"
        sendgrid_mock._build_attachment.side_effect = _build_attachment_side_effect

        attachments = message_handlers.SendGridHandler._process_attachments(sendgrid_mock, [temp_file])

        sendgrid_mock._zip_whole_directory.assert_not_called()
        sendgrid_mock._zip_single_file.assert_called_once()
        assert attachments == ["single file call"]

    def test_process_attachments_dispatches_directory(self, mocker, tmp_path):
        def _build_attachment_side_effect(value):
            return value

        sendgrid_mock = mocker.Mock()
        sendgrid_mock._zip_whole_directory.return_value = "directory call"
        sendgrid_mock._zip_single_file.return_value = "single file call"
        sendgrid_mock._build_attachment.side_effect = _build_attachment_side_effect

        attachments = message_handlers.SendGridHandler._process_attachments(sendgrid_mock, [tmp_path])

        sendgrid_mock._zip_whole_directory.assert_called_once()
        sendgrid_mock._zip_single_file.assert_not_called()
        assert attachments == ["directory call"]

    def test_process_attachments_dispatches_both_file_and_directory(self, mocker, tmp_path):
        temp_file = tmp_path / "test.txt"
        temp_file.write_text("test_process_attachments_single_file")

        def _build_attachment_side_effect(value):
            return value

        sendgrid_mock = mocker.Mock()
        sendgrid_mock._zip_whole_directory.return_value = "directory call"
        sendgrid_mock._zip_single_file.return_value = "single file call"
        sendgrid_mock._build_attachment.side_effect = _build_attachment_side_effect

        attachments = message_handlers.SendGridHandler._process_attachments(sendgrid_mock, [temp_file, tmp_path])

        sendgrid_mock._zip_whole_directory.assert_called_once()
        sendgrid_mock._zip_single_file.assert_called_once()
        assert attachments == ["single file call", "directory call"]

    def test_process_attachments_dispatches_no_attachments(self, mocker):
        sendgrid_mock = mocker.Mock()
        sendgrid_mock._zip_whole_directory.return_value = "directory call"
        sendgrid_mock._zip_single_file.return_value = "single file call"

        attachments = message_handlers.SendGridHandler._process_attachments(sendgrid_mock, [])

        sendgrid_mock._zip_whole_directory.assert_not_called()
        sendgrid_mock._zip_single_file.assert_not_called()
        assert attachments == []

    def test_process_attachments_zips_both_directory_and_single_file(self, mocker, tmp_path):
        working_dir = tmp_path
        dir_to_be_zipped = working_dir / "zip_me"
        dir_to_be_zipped.mkdir()
        temp_a = dir_to_be_zipped / "a.txt"
        temp_a.write_text("a")
        temp_b = dir_to_be_zipped / "b.txt"
        temp_b.write_text("b")

        single_file_to_be_zipped = working_dir / "single.txt"
        single_file_to_be_zipped.write_text("single file")

        def _build_attachment_side_effect(self_obj, value):
            return value

        mocker.patch.object(message_handlers.SendGridHandler, "_build_attachment", _build_attachment_side_effect)
        sendgrid_settings = {"api_key": "its_a_secret"}
        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings)

        attachments = sendgrid_handler._process_attachments([dir_to_be_zipped, single_file_to_be_zipped])

        assert len(attachments) == 2
        att_names = [Path(f).name for f in attachments]
        assert "zip_me.zip" in att_names
        assert "single.zip" in att_names

    def test_process_attachments_zips_both_single_file_and_directory(self, mocker, tmp_path):
        working_dir = tmp_path
        dir_to_be_zipped = working_dir / "zip_me"
        dir_to_be_zipped.mkdir()
        temp_a = dir_to_be_zipped / "a.txt"
        temp_a.write_text("a")
        temp_b = dir_to_be_zipped / "b.txt"
        temp_b.write_text("b")

        single_file_to_be_zipped = working_dir / "single.txt"
        single_file_to_be_zipped.write_text("single file")

        def _build_attachment_side_effect(self_obj, value):
            return value

        mocker.patch.object(message_handlers.SendGridHandler, "_build_attachment", _build_attachment_side_effect)
        sendgrid_settings = {"api_key": "its_a_secret"}
        sendgrid_handler = message_handlers.SendGridHandler(sendgrid_settings)

        attachments = sendgrid_handler._process_attachments([single_file_to_be_zipped, dir_to_be_zipped])

        assert len(attachments) == 2
        att_names = [Path(f).name for f in attachments]
        assert "zip_me.zip" in att_names
        assert "single.zip" in att_names

    def test_zip_whole_directory(self, mocker, tmp_path):
        working_dir = tmp_path
        dir_to_be_zipped = working_dir / "zip_me"
        dir_to_be_zipped.mkdir()
        temp_a = dir_to_be_zipped / "a.txt"
        temp_a.write_text("a")
        temp_b = dir_to_be_zipped / "b.txt"
        temp_b.write_text("b")

        zipped_path = message_handlers.SendGridHandler._zip_whole_directory(working_dir, dir_to_be_zipped)
        zip_name_list = zipfile.ZipFile(zipped_path).namelist()
        assert "zip_me/" in zip_name_list
        assert "zip_me/a.txt" in zip_name_list
        assert "zip_me/b.txt" in zip_name_list
        # assert zipfile.ZipFile(zipped_path).namelist() == ['zip_me/', 'zip_me/a.txt', 'zip_me/b.txt']

    def test_zip_single_file(self, mocker, tmp_path):
        working_dir = tmp_path
        temp_a = working_dir / "a.txt"
        temp_a.write_text("a")

        with TemporaryDirectory() as temp_dir:
            zipped_path = message_handlers.SendGridHandler._zip_single_file(temp_dir, temp_a)

            assert zipfile.ZipFile(zipped_path).namelist() == ["a.txt"]

    def test_build_attachment_mock_file(self, mocker):
        mock_open = mock.mock_open(read_data=b"test data")

        with mock.patch("builtins.open", mock_open):
            attachment = message_handlers.SendGridHandler._build_attachment("foo")

            assert attachment.file_name.get() == "foo"
            assert attachment.file_type.get() == "application/zip"
            assert attachment.file_content.get() == base64.b64encode(b"test data").decode()

    def test_build_attachment_single_file(self, mocker, tmp_path):
        working_dir = tmp_path
        temp_a = working_dir / "a.txt"
        temp_a.write_text("a")

        with TemporaryDirectory() as temp_dir:
            single_zip_path = message_handlers.SendGridHandler._zip_single_file(temp_dir, temp_a)

            with open(single_zip_path, "rb") as single_zip_file:
                data = single_zip_file.read()
            encoded = b64encode(data).decode()

            attachment = message_handlers.SendGridHandler._build_attachment(single_zip_path)

            assert attachment.file_name.get() == "a.zip"
            assert attachment.file_type.get() == "application/zip"
            assert attachment.file_content.get() == encoded

    def test_build_attachment_directory(self, mocker, tmp_path):
        working_dir = tmp_path
        dir_to_be_zipped = working_dir / "zip_me"
        dir_to_be_zipped.mkdir()
        temp_a = dir_to_be_zipped / "a.txt"
        temp_a.write_text("a")
        temp_b = dir_to_be_zipped / "b.txt"
        temp_b.write_text("b")

        dir_zip_path = message_handlers.SendGridHandler._zip_whole_directory(working_dir, dir_to_be_zipped)

        with open(dir_zip_path, "rb") as dir_zip_file:
            data = dir_zip_file.read()
        encoded = b64encode(data).decode()

        attachment = message_handlers.SendGridHandler._build_attachment(dir_zip_path)

        assert attachment.file_name.get() == "zip_me.zip"
        assert attachment.file_type.get() == "application/zip"
        assert attachment.file_content.get() == encoded


class TestSlackHandler:
    def test_send_message_with_blocks(self, mocker):
        """Test sending message with Slack blocks"""
        from supervisor.models import SectionBlock, ContextBlock
        
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.raise_for_status = mocker.Mock()
        mock_post.return_value = mock_response

        slack_settings = {"webhook_url": "https://hooks.slack.com/services/TEST/WEBHOOK/URL"}

        message_details = MessageDetails()
        message_details.subject = "Test Subject"
        message_details.slack_blocks = [
            SectionBlock("Hello from Slack!"),
            ContextBlock(["Context info"])
        ]

        slack_handler = message_handlers.SlackHandler(slack_settings, client_name="TestApp", client_version="1.0.0")
        slack_handler.send_message(message_details)

        #: Verify requests.post was called with blocks
        assert mock_post.call_count == 1
        payload = mock_post.call_args[1]["json"]
        assert "blocks" in payload
        assert len(payload["blocks"]) == 2
        assert payload["text"] == "Test Subject"

    def test_send_message_text_fallback(self, mocker):
        """Test basic message sending with text fallback when no blocks"""
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.raise_for_status = mocker.Mock()
        mock_post.return_value = mock_response

        slack_settings = {"webhook_url": "https://hooks.slack.com/services/TEST/WEBHOOK/URL"}

        message_details = MessageDetails()
        message_details.message = "Test message"
        message_details.subject = "Test Subject"

        slack_handler = message_handlers.SlackHandler(slack_settings, client_name="TestApp", client_version="1.0.0")
        slack_handler.send_message(message_details)

        #: Verify requests.post was called with text
        assert mock_post.call_count == 1
        payload = mock_post.call_args[1]["json"]
        assert "Test Subject" in payload["text"]
        assert "Test message" in payload["text"]
        assert "TestApp version: 1.0.0" in payload["text"]

    def test_send_message_missing_webhook_url(self, mocker):
        """Test that missing webhook_url raises warning and doesn't send"""
        mock_post = mocker.patch("requests.post")

        slack_settings = {}  # Missing webhook_url

        message_details = MessageDetails()
        message_details.message = "Test message"
        message_details.subject = "Test Subject"

        with pytest.warns(UserWarning, match="Required Slack webhook_url does not exist"):
            slack_handler = message_handlers.SlackHandler(slack_settings)
            slack_handler.send_message(message_details)

        #: Verify requests.post was NOT called
        assert mock_post.call_count == 0

    def test_send_message_empty_webhook_url(self, mocker):
        """Test that empty webhook_url raises warning and doesn't send"""
        mock_post = mocker.patch("requests.post")

        slack_settings = {"webhook_url": ""}  # Empty webhook_url

        message_details = MessageDetails()
        message_details.message = "Test message"
        message_details.subject = "Test Subject"

        with pytest.warns(UserWarning, match="Slack webhook_url exists but is empty"):
            slack_handler = message_handlers.SlackHandler(slack_settings)
            slack_handler.send_message(message_details)

        #: Verify requests.post was NOT called
        assert mock_post.call_count == 0

    def test_send_message_post_error(self, mocker):
        """Test handling of HTTP errors when posting to Slack"""
        mock_post = mocker.patch("requests.post")
        mock_post.side_effect = Exception("Network error")

        slack_settings = {"webhook_url": "https://hooks.slack.com/services/TEST/WEBHOOK/URL"}

        message_details = MessageDetails()
        message_details.message = "Test message"
        message_details.subject = "Test Subject"

        with pytest.warns(UserWarning, match="Error posting to Slack"):
            slack_handler = message_handlers.SlackHandler(slack_settings)
            slack_handler.send_message(message_details)

    def test_send_message_long_text_splitting(self, mocker):
        """Test that long text messages are split into multiple requests"""
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.raise_for_status = mocker.Mock()
        mock_post.return_value = mock_response

        slack_settings = {"webhook_url": "https://hooks.slack.com/services/TEST/WEBHOOK/URL"}

        #: Create a message that will exceed 3000 chars
        long_message = "A" * 5000
        message_details = MessageDetails()
        message_details.message = long_message
        message_details.subject = "Long Subject"

        slack_handler = message_handlers.SlackHandler(slack_settings)
        slack_handler.send_message(message_details)

        #: Verify multiple requests were made
        assert mock_post.call_count > 1

        #: Verify first message has header, last has footer
        first_call_payload = mock_post.call_args_list[0][1]["json"]
        last_call_payload = mock_post.call_args_list[-1][1]["json"]
        
        assert "*Long Subject*" in first_call_payload["text"]
        assert "version:" in last_call_payload["text"]

    def test_send_message_many_blocks_splitting(self, mocker):
        """Test that messages with over 50 blocks are split"""
        from supervisor.models import SectionBlock
        
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.raise_for_status = mocker.Mock()
        mock_post.return_value = mock_response

        slack_settings = {"webhook_url": "https://hooks.slack.com/services/TEST/WEBHOOK/URL"}

        message_details = MessageDetails()
        message_details.subject = "Test"
        #: Create 60 blocks (over the 50 limit)
        message_details.slack_blocks = [SectionBlock(f"Block {i}") for i in range(60)]

        slack_handler = message_handlers.SlackHandler(slack_settings)
        slack_handler.send_message(message_details)

        #: Should split the message into multiple posts
        assert mock_post.call_count > 1
        
        #: Verify total blocks sent equals original
        total_blocks = sum(len(call[1]["json"]["blocks"]) for call in mock_post.call_args_list)
        assert total_blocks == 60

    def test_send_message_few_blocks_no_split(self, mocker):
        """Test that messages with blocks under 50 are sent as-is"""
        from supervisor.models import SectionBlock
        
        mock_post = mocker.patch("requests.post")
        mock_response = mocker.Mock()
        mock_response.raise_for_status = mocker.Mock()
        mock_post.return_value = mock_response

        slack_settings = {"webhook_url": "https://hooks.slack.com/services/TEST/WEBHOOK/URL"}

        message_details = MessageDetails()
        message_details.subject = "Test"
        #: Create 30 blocks (under the 50 limit)
        message_details.slack_blocks = [SectionBlock(f"Block {i}") for i in range(30)]

        slack_handler = message_handlers.SlackHandler(slack_settings)
        slack_handler.send_message(message_details)

        #: Should send as-is (not split) since under 50 blocks
        assert mock_post.call_count == 1
        payload = mock_post.call_args[1]["json"]
        assert len(payload.get("blocks", [])) == 30

    def test_subject_version_too_long_for_text_splitting(self, mocker):
        """Test warning when subject and version info exceed max length for text messages"""
        mock_post = mocker.patch("requests.post")

        slack_settings = {"webhook_url": "https://hooks.slack.com/services/TEST/WEBHOOK/URL"}

        message_details = MessageDetails()
        message_details.message = "A" * 200
        message_details.subject = "S" * 2000  # Make subject very long

        #: Use long client name and version to trigger warning
        slack_handler = message_handlers.SlackHandler(
            slack_settings, 
            client_name="C" * 1000,
            client_version="V" * 1000
        )

        with pytest.warns(UserWarning, match="Subject and version info too long for Slack message splitting"):
            slack_handler.send_message(message_details)

        #: Verify no messages were sent due to the warning
        assert mock_post.call_count == 0

    def test_block_types(self):
        """Test that Block Kit objects can be created and resolved"""
        from supervisor.models import SectionBlock, ContextBlock, DividerBlock, Text
        
        #: Test SectionBlock
        section = SectionBlock("Test text")
        resolved = section._resolve()
        assert resolved["type"] == "section"
        assert resolved["text"]["text"] == "Test text"
        
        #: Test SectionBlock with fields
        section_fields = SectionBlock(fields=["Field 1", "Field 2"])
        resolved_fields = section_fields._resolve()
        assert len(resolved_fields["fields"]) == 2
        
        #: Test ContextBlock
        context = ContextBlock(["Element 1", "Element 2"])
        resolved_context = context._resolve()
        assert resolved_context["type"] == "context"
        assert len(resolved_context["elements"]) == 2
        
        #: Test DividerBlock
        divider = DividerBlock()
        resolved_divider = divider._resolve()
        assert resolved_divider["type"] == "divider"
        
        #: Test Text
        text = Text("Test")
        resolved_text = text._resolve()
        assert resolved_text["type"] == "mrkdwn"
        assert resolved_text["text"] == "Test"

    def test_message_details_slack_blocks_property(self):
        """Test that MessageDetails has slack_blocks property"""
        from supervisor.models import SectionBlock
        
        message_details = MessageDetails()
        
        #: Test initial state
        assert message_details.slack_blocks == []
        
        #: Test adding single block
        block1 = SectionBlock("Block 1")
        message_details.slack_blocks = block1
        assert len(message_details.slack_blocks) == 1
        
        #: Test adding list of blocks
        blocks = [SectionBlock("Block 2"), SectionBlock("Block 3")]
        message_details.slack_blocks = blocks
        assert len(message_details.slack_blocks) == 3
