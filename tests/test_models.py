import sys
from pathlib import Path

from supervisor import models


def test_supervisor_constructor_does_proper_setup(mocker):
    exceptions_mock = mocker.patch("supervisor.models.Supervisor._manage_exceptions")

    models.Supervisor("test project")

    assert exceptions_mock.called_once()


def test_exception_handler_replacement(mocker, capsys):
    models.Supervisor("test")

    assert "global_exception_handler" in repr(sys.excepthook)


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
    sim_sup = models.Supervisor("test")
    handler_mock = mocker.Mock(name="handler_mock")

    sim_sup.add_message_handler(handler_mock)

    assert len(sim_sup.message_handlers) == 1
    assert sim_sup.message_handlers[-1] == handler_mock


class TestMessageDetails:
    def test_attachments_single_str(self, mocker):
        message = models.MessageDetails()
        message.attachments = r"c:\temp\foo.bar"

        assert message.attachments == [r"c:\temp\foo.bar"]

    def test_attachments_single_Path(self, mocker):
        message = models.MessageDetails()
        message.attachments = Path(r"c:\temp\foo.bar")

        assert message.attachments == [Path(r"c:\temp\foo.bar")]

    def test_attachments_list_of_strs(self, mocker):
        message = models.MessageDetails()
        message.attachments = [r"c:\temp\foo.bar", r"c:\temp\bar.baz"]

        assert message.attachments == [r"c:\temp\foo.bar", r"c:\temp\bar.baz"]

    def test_attachments_list_of_Paths(self, mocker):
        message = models.MessageDetails()
        message.attachments = [Path(r"c:\temp\foo.bar"), Path(r"c:\temp\bar.baz")]

        assert message.attachments == [Path(r"c:\temp\foo.bar"), Path(r"c:\temp\bar.baz")]

    def test_attachments_mixed_list(self, mocker):
        message = models.MessageDetails()
        message.attachments = [r"c:\temp\foo.bar", Path(r"c:\temp\bar.baz")]

        assert message.attachments == [r"c:\temp\foo.bar", Path(r"c:\temp\bar.baz")]

    def test_attachment_empty_list(self, mocker):
        message = models.MessageDetails()
        message.attachments = []

        assert message.attachments == []
