import sys
import types

from supervisor import message_handlers, models


def test_supervisor_constructor_does_proper_setup(mocker):
    exceptions_mock = mocker.patch('supervisor.models.Supervisor._manage_exceptions')

    sim_sup = models.Supervisor()

    assert len(sim_sup.message_handlers) == 1
    assert type(sim_sup.message_handlers[0]) == message_handlers.ConsoleHandler
    assert exceptions_mock.called_once()


def test_exception_handler_replacement(mocker, capsys):

    sim_sup = models.Supervisor()

    assert 'global_exception_handler' in repr(sys.excepthook)


#: These next three are difficult/impossible to test if global_exception_handler is a closure/inner method
def test_global_exception_handler_is_called_on_exception(mocker):
    pass


def test_global_exception_handler_calls_notify(mocker):
    # notify = mocker.patch('supervisor.models.Supervisor.notify')
    # models.Supervisor._manage_exceptions(mocker.Mock())

    # sim_sup = models.Supervisor()

    # print(type(sim_sup._manage_exceptions.__code__.co_consts[2].co_name))
    # hacky_handler = types.FunctionType(sim_sup._manage_exceptions.__code__.co_consts[2], globals(), (), None)
    # hacky_handler(mocker.Mock(), mocker.Mock(), mocker.Mock())

    # exception_maker = mocker.Mock(side_effect=ValueError('foo'))
    # exception_maker()

    # assert notify.called_once()
    pass


def test_global_exception_handler_creates_proper_error_message(mocker):
    pass


def test_add_message_handler(mocker):
    sim_sup = models.Supervisor()
    handler_mock = mocker.Mock(name='handler_mock')

    sim_sup.add_message_handler(handler_mock)

    assert len(sim_sup.message_handlers) == 2
    assert sim_sup.message_handlers[-1] == handler_mock
