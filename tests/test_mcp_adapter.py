# This is the full content for tests/test_mcp_adapter.py

import unittest
import json
from unittest.mock import patch, MagicMock

# We must import the class we intend to test
from adam_tools.plugins.mcp_adapter import McpAdapter

# --- Test Data ---
MOCK_REGISTRY_CONTENT = {
    "servers": [
        {
            "name": "mock_server",
            "description": "A fake server for testing.",
            "protocol": "local",
            "connection": {"type": "python_module", "module": "fake.module"},
            "tools": [{"name": "mock_tool", "args": {}}],
        }
    ]
}


class TestMcpAdapter(unittest.TestCase):
    @patch(
        "builtins.open",
        new_callable=unittest.mock.mock_open,
        read_data=json.dumps(MOCK_REGISTRY_CONTENT),
    )
    @patch("os.path.exists", return_value=True)
    def setUp(self, mock_exists, mock_open):
        """Set up a fresh adapter instance for each test, mocking the registry file."""
        self.adapter = McpAdapter()

    def test_list_servers(self):
        """Verify that the adapter correctly lists servers from the mock registry."""
        result = self.adapter.run(action="list_servers")
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["data"]), 1)
        self.assertEqual(result["data"][0]["name"], "mock_server")

    def test_list_tools_valid_server(self):
        """Verify listing tools for a known server."""
        result = self.adapter.run(action="list_tools", server_name="mock_server")
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["data"]), 1)
        self.assertEqual(result["data"][0]["name"], "mock_tool")

    def test_list_tools_invalid_server(self):
        """Verify that an error is returned for a non-existent server."""
        result = self.adapter.run(
            action="list_tools", server_name="non_existent_server"
        )
        self.assertFalse(result["ok"])
        self.assertIn("not found", result["error"])

    @patch("importlib.import_module")
    def test_call_tool_success(self, mock_import):
        """Test a successful tool call, mocking the dynamic module import."""
        # Configure the mock module and its 'run_tool' function
        mock_module = MagicMock()
        mock_module.run_tool.return_value = {"status": "success"}
        mock_import.return_value = mock_module

        args = {"param": "value"}
        result = self.adapter.run(
            action="call_tool",
            server_name="mock_server",
            tool_name="mock_tool",
            args=args,
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["data"]["status"], "success")
        # Verify that the correct module was imported and the function was called
        mock_import.assert_called_once_with("fake.module")
        mock_module.run_tool.assert_called_once_with("mock_tool", args, {})

    def test_call_tool_server_not_found(self):
        """Test calling a tool on a non-existent server."""
        result = self.adapter.run(
            action="call_tool", server_name="bad_server", tool_name="any", args={}
        )
        self.assertFalse(result["ok"])
        self.assertIn("not found", result["error"])
