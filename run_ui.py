# run_ui.py (place at project root, alongside src/)
import sys
import time
from pathlib import Path

# Ensure src on path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import tkinter as tk
from ui.app import main

# We'll fill this once UI is ready
_app_ref = {"app": None}


def on_ready(app):
    _app_ref["app"] = app


def submit_callback(user_text: str):
    # Simulate backend work off the UI thread (UI already spawns a thread for submit)
    time.sleep(0.6)
    reply = (
        f"I heard: {user_text}\n\n"
        "```python\n"
        "for i in range(3):\n"
        "    print('hello', i)\n"
        "```\n"
        "_Tip:_ Toggle timestamps with Ctrl+T."
    )
    # Push response into UI
    app = _app_ref["app"]
    if app and hasattr(app, "receive_response"):
        app.receive_response(reply)


if __name__ == "__main__":
    root = tk.Tk()
    main(root, submit_callback=submit_callback, on_ready=on_ready)
