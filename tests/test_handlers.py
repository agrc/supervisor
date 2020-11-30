from io import StringIO

from supervisor import message_handlers


def test_console_handler_prints(mocker, capsys):

    handler_mock = mocker.Mock()
    message_handlers.ConsoleHandler.send_message(handler_mock, 'foo')

    captured = capsys.readouterr()

    assert captured.out == 'foo\n'
