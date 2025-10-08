# src/ui/app.py
"""
Main UI entry point — pure orchestration.
Delegates all logic to components. No business logic, no file I/O.
"""

from __future__ import annotations

import logging
from pathlib import Path
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
from types import SimpleNamespace
from typing import List, Dict, Optional

# Global exception handler for harmless Tcl errors
def _handle_tk_exception(self, exc, val, tb):
    error_msg = str(val)
    if "can't delete Tcl command" in error_msg or "bad window path name" in error_msg:
        return  # Ignore harmless cleanup errors
    # Log other errors normally
    logger = logging.getLogger(__name__)
    logger.error("Unhandled Tkinter exception", exc_info=(exc, val, tb))


tk.Tk.report_callback_exception = _handle_tk_exception


from .state import ensure_defaults
from .components.layout import attach_layout
from .components.sidebar import render_sidebar
from .components.chat import render_chat
from .components.settings import render_settings
from .components.history import attach_history
from .components.renderer import attach_renderer
from .components.search import attach_search
from .components.theme import attach_theme
from .components.model_sync import attach_model_sync
from .components.shortcuts import attach_shortcuts
from .components.style import set_spacing_scale
from .fallback_ui import launch_fallback_ui

logger = logging.getLogger(__name__)


def _configure_root_window(root: tk.Tk) -> None:
    try:
        root.title("Adam — Modern AI Assistant")
        root.geometry("1920x1200")
        root.minsize(1200, 800)
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        screen_width = root.winfo_screenwidth()
        if screen_width >= 3000:
            set_spacing_scale(1.3)
        elif screen_width >= 2000:
            set_spacing_scale(1.15)
        elif screen_width >= 1600:
            set_spacing_scale(1.0)
        else:
            set_spacing_scale(0.9)
    except Exception:
        pass


def main(root: tk.Tk, submit_callback=None, on_ready=None):
    try:
        logger.info("✅ Initializing UI state...")
        ensure_defaults()

        logger.info("✅ Configuring root window...")
        _configure_root_window(root)

        app = SimpleNamespace(root=root, submit_callback=submit_callback)
        app._ui_ready = False
        logger.info("✅ App namespace created")

        logger.info("✅ Attaching history...")
        attach_history(app)
        logger.info("✅ Attaching renderer...")
        attach_renderer(app)
        logger.info("✅ Attaching search...")
        attach_search(app)
        logger.info("✅ Attaching theme...")
        attach_theme(app)
        logger.info("✅ Attaching model sync...")
        attach_model_sync(app)
        logger.info("✅ Attaching shortcuts...")
        attach_shortcuts(app)
        logger.info("✅ Attaching layout...")
        attach_layout(app)

        logger.info("✅ Rendering sidebar...")
        render_sidebar(app)
        logger.info("✅ Rendering settings...")
        render_settings(app)
        logger.info("✅ Rendering chat...")
        render_chat(app)

        app._ui_ready = True

        logger.info("✅ Setting up receive_response hook...")

        def receive_response(text: str):
            app.root.after(0, lambda: app._render_response(text))

        app.receive_response = receive_response

        if callable(on_ready):
            logger.info("✅ Calling on_ready callback...")
            on_ready(app)

        def _on_closing():
            try:
                root.quit()
                root.destroy()
            except Exception:
                pass

        root.protocol("WM_DELETE_WINDOW", _on_closing)

        logger.info("✅ Starting mainloop() — UI should appear now!")
        root.mainloop()
        logger.info("✅ mainloop() exited")
        return app

    except Exception as e:
        logger.critical("❌ Failed to launch main UI", exc_info=True)
        result = launch_fallback_ui(root, submit_callback, reason=str(e))
        logger.info("✅ Fallback UI launched")
        return result


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "ui.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    root = tk.Tk()
    main(root)
