# src/ui/fallback_ui.py
"""Minimal fallback Tk UI — styled to match main Adam UI."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, font as tkfont


def _get_font_family():
    families = tkfont.families()
    for candidate in ["Segoe UI", "Helvetica", "Arial"]:
        if candidate in families:
            return candidate
    return "TkDefaultFont"


class FallbackUI:
    def __init__(
        self, root: tk.Tk, submit_callback=None, reason: str | None = None
    ) -> None:
        self.root = root
        self.submit_callback = submit_callback

        # Theme-like constants (mirroring main UI)
        self.bg = "#1e1e1e"
        self.fg = "#e0e0e0"
        self.accent = "#4dabf7"
        self.input_bg = "#2d2d2d"
        self.chat_bg = "#252526"
        self.error_fg = "#ff6b6b"

        font_family = _get_font_family()
        self.header_font = tkfont.Font(family=font_family, size=12, weight="bold")
        self.body_font = tkfont.Font(family=font_family, size=11)

        self.root.title("Adam — Recovery Console")
        self.root.geometry("700x480")
        self.root.configure(bg=self.bg)

        # Header
        header = tk.Frame(self.root, bg=self.bg)
        header.pack(fill="x", padx=12, pady=(12, 6))

        tk.Label(
            header,
            text="Adam — Recovery Console",
            font=self.header_font,
            bg=self.bg,
            fg=self.fg,
        ).pack(side="left")

        if reason:
            tk.Label(
                header,
                text=f"Startup issue: {reason}",
                fg=self.error_fg,
                bg=self.bg,
                font=self.body_font,
            ).pack(side="right", padx=(0, 10))

        # Chat area
        self.chat = tk.Text(
            self.root,
            wrap="word",
            state="disabled",
            bg=self.chat_bg,
            fg="#d4d4d4",
            font=self.body_font,
            relief="flat",
            padx=10,
            pady=10,
            insertbackground=self.fg,
        )
        self.chat.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Entry row
        bottom = tk.Frame(self.root, bg=self.bg)
        bottom.pack(fill="x", padx=12, pady=(0, 12))

        self.entry = tk.Entry(
            bottom,
            bg=self.input_bg,
            fg=self.fg,
            insertbackground=self.fg,
            relief="flat",
            font=self.body_font,
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.entry.bind("<Return>", self._send_from_event)

        # Style the button
        style = ttk.Style()
        btn_style = "Fallback.Send.TButton"
        style.configure(
            btn_style,
            font=(font_family, 10, "bold"),
            background=self.accent,
            foreground="white",
            borderwidth=0,
            padding=(12, 6),
        )
        style.map(btn_style, background=[("active", "#3399ff")])

        send_btn = ttk.Button(
            bottom, text="Send", command=self._on_send, style=btn_style
        )
        send_btn.pack(side="left", padx=(8, 0))

    def run(self) -> None:
        self.root.mainloop()

    def _on_send(self) -> None:
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self._append_chat("You", text)
        if self.submit_callback:
            try:
                self.submit_callback(text)
            except Exception as e:
                self._append_chat("System", f"Submit failed: {e!r}")

    def _send_from_event(self, _event):
        self._on_send()
        return "break"

    def _append_chat(self, speaker: str, text: str) -> None:
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{speaker}:", "speaker")
        self.chat.insert("end", f" {text}\n", "message")

        self.chat.tag_config("speaker", font=self.header_font, foreground=self.accent)
        self.chat.tag_config("message", font=self.body_font, foreground="#d4d4d4")

        self.chat.see("end")
        self.chat.configure(state="disabled")


def launch_fallback_ui(
    root: tk.Tk, submit_callback=None, reason: str = "Unknown error"
):
    """Clear any existing content and bring up a styled recovery UI."""
    try:
        for child in root.winfo_children():
            child.destroy()
    except Exception:
        pass
    ui = FallbackUI(root, submit_callback=submit_callback, reason=reason)
    ui.run()
    return ui
