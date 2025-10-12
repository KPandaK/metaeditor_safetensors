import pytest

from metaeditor_safetensors.models.metadata import Metadata
from metaeditor_safetensors.services.file_workflow import (
    MODEL_SPEC_VERSION,
    FileWorkflow,
)
from metaeditor_safetensors.services.utility import ModelType


@pytest.fixture
def metadata():
    model = Metadata()
    model.load_data({})
    return model


@pytest.fixture
def config_service(mocker):
    return mocker.Mock()


@pytest.fixture
def safetensors_service(mocker):
    service = mocker.Mock()
    service.is_saving.return_value = False
    service.is_loading.return_value = False
    service.read_metadata_async.return_value = True
    return service


@pytest.fixture
def detection_service(mocker):
    service = mocker.Mock()
    service.detect_model_type.return_value = ModelType.UNKNOWN
    return service


def test_load_file_async_success(
    metadata, safetensors_service, config_service, detection_service, mocker
):
    detection_service.detect_model_type.return_value = ModelType.IMAGE_GENERATION

    workflow = FileWorkflow(
        metadata, safetensors_service, config_service, detection_service
    )

    progress_cb = mocker.Mock()
    success_cb = mocker.Mock()
    error_cb = mocker.Mock()

    dispatch = workflow.load_file(
        "async.safetensors",
        progress_callback=progress_cb,
        success_callback=success_cb,
        error_callback=error_cb,
    )

    assert dispatch.started
    call = safetensors_service.read_metadata_async.call_args
    assert call.args[0] == "async.safetensors"
    progress_wrapper = call.kwargs["progress_callback"]
    success_wrapper = call.kwargs["success_callback"]
    error_wrapper = call.kwargs["error_callback"]

    assert callable(progress_wrapper)
    assert callable(success_wrapper)
    assert callable(error_wrapper)

    progress_wrapper(25)
    progress_cb.assert_called_once_with(25)

    success_wrapper({"modelspec.title": "Async Demo"})

    assert workflow.current_file == "async.safetensors"
    config_service.add_recent_file.assert_called_once_with("async.safetensors")
    detection_service.detect_model_type.assert_called_once()
    success_cb.assert_called_once()
    success_result = success_cb.call_args[0][0]
    assert success_result.success
    assert success_result.filepath == "async.safetensors"
    assert metadata.get_value("modelspec.title") == "Async Demo"
    assert (
        metadata.get_value("metaeditor.model_type") == ModelType.IMAGE_GENERATION.value
    )
    error_cb.assert_not_called()


def test_load_file_async_error(
    metadata, safetensors_service, config_service, detection_service, mocker
):
    workflow = FileWorkflow(
        metadata, safetensors_service, config_service, detection_service
    )

    error_cb = mocker.Mock()
    progress_cb = mocker.Mock()

    dispatch = workflow.load_file(
        "async.safetensors",
        progress_callback=progress_cb,
        success_callback=None,
        error_callback=error_cb,
    )

    assert dispatch.started
    call = safetensors_service.read_metadata_async.call_args
    error_wrapper = call.kwargs["error_callback"]

    error_wrapper("boom")

    assert workflow.current_file is None
    assert metadata.get_all_data() == {}
    error_cb.assert_called_once()
    error_result = error_cb.call_args[0][0]
    assert not error_result.success
    assert error_result.error == "boom"
    config_service.add_recent_file.assert_not_called()


def test_load_file_async_when_service_busy(
    metadata, safetensors_service, config_service, detection_service, mocker
):
    safetensors_service.is_loading.return_value = True

    workflow = FileWorkflow(
        metadata, safetensors_service, config_service, detection_service
    )

    dispatch = workflow.load_file(
        "example.safetensors",
        progress_callback=mocker.Mock(),
        success_callback=mocker.Mock(),
        error_callback=mocker.Mock(),
    )

    assert not dispatch.started
    assert dispatch.message == "Load operation already in progress."
    safetensors_service.read_metadata_async.assert_not_called()


def test_save_dispatches_write(
    metadata, safetensors_service, config_service, detection_service, mocker
):
    metadata.load_data({"modelspec.title": "Demo"})
    safetensors_service.write_metadata_async.return_value = True

    workflow = FileWorkflow(
        metadata, safetensors_service, config_service, detection_service
    )
    workflow.current_file = "current.safetensors"

    progress_cb = mocker.Mock()
    success_cb = mocker.Mock()
    error_cb = mocker.Mock()

    dispatch = workflow.save(progress_cb, success_cb, error_cb)

    assert dispatch.started
    assert dispatch.filepath == "current.safetensors"
    safetensors_service.write_metadata_async.assert_called_once()
    call = safetensors_service.write_metadata_async.call_args
    assert call.kwargs["filepath"] == "current.safetensors"
    assert call.kwargs["metadata"] == metadata.get_all_data()
    progress_wrapper = call.kwargs["progress_callback"]
    success_wrapper = call.kwargs["success_callback"]
    error_wrapper = call.kwargs["error_callback"]

    assert callable(progress_wrapper)
    assert progress_wrapper is not progress_cb
    progress_wrapper(50)
    progress_cb.assert_called_once_with(50)

    assert callable(success_wrapper)
    assert success_wrapper is not success_cb
    assert callable(error_wrapper)
    assert error_wrapper is not error_cb

    config_service.add_recent_file.assert_not_called()

    success_wrapper("current.safetensors")
    config_service.add_recent_file.assert_called_once_with("current.safetensors")
    success_cb.assert_called_once_with("current.safetensors")
    error_cb.assert_not_called()


def test_save_as_updates_current_file_on_success(
    metadata, safetensors_service, config_service, detection_service, mocker
):
    metadata.load_data({"modelspec.title": "Demo"})
    safetensors_service.write_metadata_async.return_value = True

    workflow = FileWorkflow(
        metadata, safetensors_service, config_service, detection_service
    )
    workflow.current_file = "original.safetensors"

    progress_cb = mocker.Mock()
    success_cb = mocker.Mock()
    error_cb = mocker.Mock()

    dispatch = workflow.save_as(
        "new.safetensors",
        progress_cb,
        success_cb,
        error_cb,
    )

    assert dispatch.started
    assert dispatch.filepath == "new.safetensors"

    call = safetensors_service.write_metadata_async.call_args
    assert call.kwargs["filepath"] == "new.safetensors"
    assert call.kwargs["source_filepath"] == "original.safetensors"
    progress_wrapper = call.kwargs["progress_callback"]
    success_wrapper = call.kwargs["success_callback"]

    assert callable(progress_wrapper)
    assert callable(success_wrapper)

    progress_wrapper(10)
    progress_cb.assert_called_once_with(10)

    assert workflow.current_file == "original.safetensors"

    success_wrapper("new.safetensors")

    assert workflow.current_file == "new.safetensors"
    config_service.add_recent_file.assert_called_once_with("new.safetensors")
    success_cb.assert_called_once_with("new.safetensors")


def test_save_error_callback_invoked(
    metadata, safetensors_service, config_service, detection_service, mocker
):
    metadata.load_data({"modelspec.title": "Demo"})
    safetensors_service.write_metadata_async.return_value = True

    workflow = FileWorkflow(
        metadata, safetensors_service, config_service, detection_service
    )
    workflow.current_file = "current.safetensors"

    progress_cb = mocker.Mock()
    success_cb = mocker.Mock()
    error_cb = mocker.Mock()

    workflow.save(progress_cb, success_cb, error_cb)

    call = safetensors_service.write_metadata_async.call_args
    error_wrapper = call.kwargs["error_callback"]

    error_wrapper("boom")

    error_cb.assert_called_once_with("boom")
    success_cb.assert_not_called()
    config_service.add_recent_file.assert_not_called()


def test_save_when_service_busy_returns_message(
    metadata, safetensors_service, config_service, detection_service, mocker
):
    workflow = FileWorkflow(
        metadata, safetensors_service, config_service, detection_service
    )
    workflow.current_file = "current.safetensors"
    safetensors_service.is_saving.return_value = True

    dispatch = workflow.save(
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
    )

    assert not dispatch.started
    assert dispatch.message == "Save operation already in progress."
    safetensors_service.write_metadata_async.assert_not_called()


def test_clear_current_file_resets_state(
    metadata, safetensors_service, config_service, detection_service
):
    workflow = FileWorkflow(
        metadata, safetensors_service, config_service, detection_service
    )
    workflow.current_file = "example.safetensors"

    workflow.clear_current_file()

    assert workflow.current_file is None


def test_load_file_start_failure_returns_dispatch(
    metadata, safetensors_service, config_service, detection_service, mocker
):
    safetensors_service.read_metadata_async.return_value = False

    workflow = FileWorkflow(
        metadata, safetensors_service, config_service, detection_service
    )

    dispatch = workflow.load_file(
        "failed.safetensors",
        progress_callback=mocker.Mock(),
        success_callback=mocker.Mock(),
        error_callback=mocker.Mock(),
    )

    assert not dispatch.started
    assert dispatch.message == "Load operation already in progress."


def test_save_requires_current_file(
    metadata, safetensors_service, config_service, detection_service, mocker
):
    workflow = FileWorkflow(
        metadata, safetensors_service, config_service, detection_service
    )

    dispatch = workflow.save(mocker.Mock(), mocker.Mock(), mocker.Mock())

    assert not dispatch.started
    assert dispatch.message == "Please open a file first."
    safetensors_service.write_metadata_async.assert_not_called()


def test_dispatch_noop_when_callback_missing(
    metadata, safetensors_service, config_service, detection_service
):
    workflow = FileWorkflow(
        metadata, safetensors_service, config_service, detection_service
    )

    calls = []

    def slot(fn):
        calls.append(fn)

    workflow._invoke_signal.connect(slot)

    workflow._dispatch(None)

    assert calls == []
    workflow._invoke_signal.disconnect(slot)


def test_save_start_failure_returns_message(
    metadata, safetensors_service, config_service, detection_service, mocker
):
    metadata.load_data({"modelspec.title": "Demo"})
    workflow = FileWorkflow(
        metadata, safetensors_service, config_service, detection_service
    )
    workflow.current_file = "current.safetensors"
    safetensors_service.write_metadata_async.return_value = False

    dispatch = workflow.save(mocker.Mock(), mocker.Mock(), mocker.Mock())

    assert not dispatch.started
    assert dispatch.message == "Save operation already in progress."


def test_process_metadata_skips_detection_when_model_type_present(
    metadata, safetensors_service, config_service, detection_service
):
    workflow = FileWorkflow(
        metadata, safetensors_service, config_service, detection_service
    )
    metadata.set_value("metaeditor.model_type", ModelType.TEXT_PREDICTION.value)

    workflow._process_metadata_on_load(
        {"metaeditor.model_type": ModelType.TEXT_PREDICTION.value}
    )

    detection_service.detect_model_type.assert_not_called()


def test_process_metadata_upgrades_modelspec_version(
    metadata, safetensors_service, config_service, detection_service
):
    workflow = FileWorkflow(
        metadata, safetensors_service, config_service, detection_service
    )

    incoming = {
        "modelspec.sai_model_spec": "1.0.0",
        "modelspec.title": "Test Model",
    }

    processed = workflow._process_metadata_on_load(incoming)

    assert processed["modelspec.sai_model_spec"] == MODEL_SPEC_VERSION
