import os
import sys
import pytest
import yaml
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from adam_tools.plugins.base import call_plugin, PLUGIN_REGISTRY_PATH, LOG_DIR


@pytest.fixture(scope="module", autouse=True)
def setup_teardown():
    # Setup: ensure registry and logs are clean
    if not os.path.exists(os.path.dirname(PLUGIN_REGISTRY_PATH)):
        os.makedirs(os.path.dirname(PLUGIN_REGISTRY_PATH))

    with open(PLUGIN_REGISTRY_PATH, "w") as f:
        yaml.dump(
            {
                "plugins": [
                    {
                        "name": "example_echo",
                        "version": "0.1.0",
                        "entrypoint": "adam_tools.plugins.example_echo",
                        "enabled": True,
                    }
                ]
            },
            f,
        )

    if os.path.exists(LOG_DIR):
        for f in os.listdir(LOG_DIR):
            os.remove(os.path.join(LOG_DIR, f))

    yield

    # Teardown: clean up created files
    if os.path.exists(PLUGIN_REGISTRY_PATH):
        os.remove(PLUGIN_REGISTRY_PATH)
    if os.path.exists(LOG_DIR):
        for f in os.listdir(LOG_DIR):
            os.remove(os.path.join(LOG_DIR, f))


def test_call_echo_plugin_success():
    """Tests a successful call to the example_echo plugin."""
    result = call_plugin("example_echo", {"text": "hello world"})
    assert result == {"ok": True, "data": "hello world", "error": None}


def test_call_nonexistent_plugin():
    """Tests calling a plugin that is not in the registry."""
    result = call_plugin("nonexistent", {})
    assert result["ok"] is False
    assert "not found" in result["error"]


def test_call_plugin_with_error():
    """Tests a plugin call that results in an error."""
    result = call_plugin("example_echo", {"text": 123})  # Invalid input
    assert result["ok"] is False
    assert result["data"] is None
    assert "must be a string" in result["error"]


def test_plugin_logging():
    """Tests that plugin calls are correctly logged."""
    log_file = os.path.join(LOG_DIR, "example_echo.log")
    if os.path.exists(log_file):
        os.remove(log_file)

    call_plugin("example_echo", {"text": "log test"})

    assert os.path.exists(log_file)
    with open(log_file, "r") as f:
        lines = f.readlines()

    assert len(lines) == 2  # start and success
    log_start = json.loads(lines[0])
    log_success = json.loads(lines[1])

    assert log_start["event"] == "call_start"
    assert log_start["payload"]["params"] == {"text": "log test"}
    assert log_success["event"] == "call_success"
    assert log_success["payload"]["result"]["data"] == "log test"
