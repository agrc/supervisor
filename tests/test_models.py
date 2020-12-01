import sys

from supervisor import message_handlers, models


def test_supervisor_constructor_does_proper_setup(mocker):
    exceptions_mock = mocker.patch('supervisor.models.Supervisor._manage_exceptions')

    sim_sup = models.Supervisor()

    assert len(sim_sup.message_handlers) == 1
    assert type(sim_sup.message_handlers[0]) == message_handlers.ConsoleHandler
    assert exceptions_mock.called_once()


def test_exception_handler_replacement(mocker):
    global_exception_handler = mocker.patch.object(models.Supervisor._manage_exceptions, 'global_exception_handler')
    item_mock = mocker.Mock()
    models.Supervisor._manage_exceptions(item_mock)

    assert sys.excepthook == global_exception_handler


def test_global_exception_handler_is_called_on_exception(mocker):
    pass


def test_global_exception_handler_calls_notify(mocker):
    pass


def test_global_exception_handler_creates_proper_error_message(mocker):
    pass
