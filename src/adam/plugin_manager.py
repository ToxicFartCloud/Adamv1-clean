# src/adam/plugin_manager.py

import importlib
import importlib.util
import logging
import pkgutil
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Set

logger = logging.getLogger("adam")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PLUGINS_PATH = PROJECT_ROOT / "plugins"
PLUGINS_PACKAGE = "plugins"

# Enforce strict plugin naming: must be a valid Python identifier
_PLUGIN_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class PluginLoadError(Exception):
    """Raised when a plugin cannot be loaded."""


class PluginManager:
    """A singleton manager for discovering and lazy-loading Adam plugins."""

    def __init__(self):
        """Initializes the manager, discovers plugins, and sets up the cache."""
        self._available_plugins = self._discover()
        self._loaded_plugins = {}
        logger.info(
            f"PluginManager initialized. Found {len(self._available_plugins)} available plugins."
        )

    def _discover(self) -> Set[str]:
        """
        Scans the plugins directory and returns a set of available plugin names.

        Only top-level, non-package, non-private modules (not starting with '_')
        are considered valid plugins.

        Returns:
            A set of plugin names (strings) that are available for loading.
        """
        try:
            plugins_path = PLUGINS_PATH
            if not plugins_path.exists():
                logger.warning("Plugins directory not found at expected location.")
                return set()

            discovered_plugins = set()
            for importer, modname, ispkg in pkgutil.iter_modules([str(plugins_path)]):
                # Skip packages and private modules (e.g., __init__, _utils)
                if (
                    not ispkg
                    and not modname.startswith("_")
                    and _PLUGIN_NAME_PATTERN.match(modname)
                ):
                    discovered_plugins.add(modname)

            return discovered_plugins
        except Exception as e:
            logger.error(f"Error during plugin discovery: {e}")
            return set()

    # In plugin_manager.py, inside PluginManager class:
    def get_available_plugins(self) -> Set[str]:
        """Return a copy of the set of discovered plugin names."""
        return self._available_plugins.copy()

    def _get_plugin_module(self, plugin_name: str) -> Optional[object]:
        """Return the module for the given plugin name, loading it if needed."""
        if not _PLUGIN_NAME_PATTERN.match(plugin_name):
            raise PluginLoadError(
                f"Invalid plugin name format: '{plugin_name}'. Must be a valid Python identifier."
            )

        if plugin_name not in self._available_plugins:
            raise PluginLoadError(f"Plugin '{plugin_name}' not found in available plugins.")

        if plugin_name in self._loaded_plugins:
            return self._loaded_plugins[plugin_name]

        try:
            logger.info(f"Lazy-loading plugin: {plugin_name}")
            module_name = f"{PLUGINS_PACKAGE}.{plugin_name}"
            module_path = PLUGINS_PATH / f"{plugin_name}.py"
            if not module_path.exists():
                raise PluginLoadError(f"Plugin file not found at {module_path}")
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                raise PluginLoadError(
                    f"Could not create spec for plugin '{plugin_name}'"
                )
            plugin_module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = plugin_module
            spec.loader.exec_module(plugin_module)
            self._loaded_plugins[plugin_name] = plugin_module
            return plugin_module
        except PluginLoadError:
            raise
        except Exception as exc:
            raise PluginLoadError(f"Failed to import plugin '{plugin_name}': {exc}")

    def ensure_plugin_loaded(self, plugin_name: str) -> bool:
        """Attempt to load the plugin at startup; return True on success."""
        try:
            self._get_plugin_module(plugin_name)
            return True
        except PluginLoadError as exc:
            logger.error(str(exc))
            return False

    def run_plugin(self, plugin_name: str, **kwargs) -> Dict[str, Any]:
        """
        Lazily loads and executes a plugin's run function.

        This method implements a lazy-loading pattern to improve application
        startup performance. Plugins are only imported when first requested.

        Args:
            plugin_name (str): The name of the plugin to execute. Must be a valid
                               Python identifier (alphanumeric + underscores, not starting with digit).
            **kwargs: Arguments to pass to the plugin's run function.

        Returns:
            A dictionary adhering to the standard plugin response contract:
            {
                "ok": bool,      # True if successful, False otherwise
                "data": Any,     # The result data from the plugin (if successful)
                "error": str     # Error message (if failed), None otherwise
            }
        """
        try:
            plugin_module = self._get_plugin_module(plugin_name)
        except PluginLoadError as exc:
            logger.error(str(exc))
            return {"ok": False, "data": None, "error": str(exc)}

        # Ensure the plugin exports a callable 'run' function
        if not hasattr(plugin_module, "run"):
            error_msg = f"Plugin '{plugin_name}' does not have a 'run' function."
            logger.error(error_msg)
            return {"ok": False, "data": None, "error": error_msg}

        run_func = getattr(plugin_module, "run")
        if not callable(run_func):
            error_msg = (
                f"The 'run' attribute in plugin '{plugin_name}' is not callable."
            )
            logger.error(error_msg)
            return {"ok": False, "data": None, "error": error_msg}

        # Execute the plugin's run function
        try:
            result = run_func(**kwargs)
            # If plugin returns a proper response contract, pass it through
            if isinstance(result, dict) and "ok" in result:
                return result
            else:
                # Wrap non-conforming responses safely
                logger.warning(
                    f"Plugin '{plugin_name}' returned a non-standard response. Wrapping it."
                )
                return {"ok": True, "data": result, "error": None}
        except Exception as e:
            error_msg = f"Plugin '{plugin_name}' execution failed: {e}"
            logger.error(error_msg, exc_info=True)
            return {"ok": False, "data": None, "error": error_msg}


# Create the single, shared instance for the application to use
manager = PluginManager()
