# src/ui/components/renderer.py
"""
Message renderer — creates chat bubbles with role-based styling.
Fully respects STYLE design tokens for consistency.
"""

from __future__ import annotations

import logging
import tkinter as tk
from datetime import datetime
from types import MethodType

from .style import STYLE  # ← Only import STYLE (COLORS doesn't exist)
from ..state import ui_state

logger = logging.getLogger(__name__)

# Fenced code block regex (fallback if not provided in STYLE)
FENCE_RE = STYLE.get("FENCE_RE")
if FENCE_RE is None:
    import re

    FENCE_RE = re.compile(r"```(\w+)?\n([\s\S]*?)```", re.MULTILINE)


def attach_renderer(app) -> None:
    """Bind message rendering helpers onto the app namespace."""
    if not hasattr(app, "_messages"):
        app._messages = {}
    if not hasattr(app, "_next_msg_id"):
        app._next_msg_id = 0

    if not hasattr(app, "_copy_to_clipboard"):

        def _copy_to_clipboard_impl(self, text: str) -> None:
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
            except Exception:
                pass

        app._copy_to_clipboard = MethodType(_copy_to_clipboard_impl, app)

    bindings = {
        "_bubble": _bubble,
        "_on_copy_message": _on_copy_message,
        "_on_delete_message": _on_delete_message,
        "_attach_context_menu": _attach_context_menu,
        "_make_role_badge": _make_role_badge,
        "_bubble_colors_for_role": _bubble_colors_for_role,
        "_timestamp": _timestamp,
        "_extract_segments": _extract_segments,
    }
    for name, func in bindings.items():
        setattr(app, name, MethodType(func, app))


def _bubble(self, role: str, text: str, *, persist: bool = True) -> None:
    # Simple guard: if chat_log doesn't exist, don't render
    if not hasattr(self, "chat_log") or self.chat_log is None:
        preview = (text or "")[:50]
        print(f"DEBUG: chat_log not ready, skipping message: {preview}...")
        return

    colors = STYLE["colors"]
    fonts = STYLE["fonts"]
    spacing = STYLE["spacing"]

    bg, fg, badge_bg, badge_fg = self._bubble_colors_for_role(role)

    outer_frame = tk.Frame(self.chat_log, bg=colors["panel_light"])
    if (role or "").lower() == "user":
        outer_frame.pack(
            fill="x", padx=(spacing["xl"], spacing["s"]), pady=spacing["s"]
        )
    else:
        outer_frame.pack(
            fill="x", padx=(spacing["s"], spacing["xl"]), pady=spacing["s"]
        )

    msg_frame = tk.Frame(outer_frame, bg=bg, highlightthickness=0, bd=0)
    msg_frame.pack(fill="x")

    # Header with role badge
    head = tk.Frame(msg_frame, bg=bg)
    head.pack(fill="x", pady=(spacing["s"], 2), padx=spacing["inner"])
    badge = self._make_role_badge(head, role)
    badge.pack(side="left")

    # Message text
    txt = tk.Text(
        msg_frame,
        wrap="word",
        font=fonts["body"],
        relief="flat",
        bg=bg,
        fg=fg,
        highlightthickness=1,
        highlightbackground=colors.get("border", "#2a3550"),
        bd=0,
        padx=spacing["m"],  # ← was 10
        pady=spacing["s"],  # ← was 6
        height=1,
    )
    txt.insert("end", text or "")
    make_readonly = getattr(self, "_make_readonly_text", None)
    if callable(make_readonly):
        make_readonly(txt)
    else:
        txt.configure(state="disabled")
    try:
        self._attach_context_menu(txt, read_only=True)
    except TypeError:
        if hasattr(self, "_attach_context_menu"):
            self._attach_context_menu(txt)
    txt.pack(fill="x", padx=spacing["inner"], pady=(0, spacing["inner"]))

    # Message record
    msg_id = getattr(self, "_next_msg_id", 0)
    self._next_msg_id = msg_id + 1
    record = {
        "id": msg_id,
        "role": role,
        "text": text or "",
        "frame": outer_frame,
        "text_widget": txt,
    }
    self._messages[msg_id] = record

    # Persist to ui_state if requested
    if persist:
        try:
            cid = str(ui_state.get("active_chat_id", 1))
            messages = ui_state.setdefault("chat_messages", {})
            bucket = messages.setdefault(cid, [])
            bucket.append({"role": role, "text": text or ""})
            if hasattr(self, "_save_chats"):
                self._save_chats()
        except Exception:
            pass

    # Action buttons
    actions = tk.Frame(msg_frame, bg=bg)
    btn_config = {
        "bg": colors["accent"],
        "fg": colors["accent_fg"],
        "highlightthickness": 1,
        "highlightbackground": colors["border"],
        "bd": 0,
        "font": fonts["small"],
    }

    copy_btn = tk.Button(
        actions,
        text="Copy",
        command=lambda mid=msg_id: self._on_copy_message(mid),
        **btn_config,
    )
    del_btn = tk.Button(
        actions,
        text="Delete",
        command=lambda mid=msg_id: self._on_delete_message(mid),
        **btn_config,
    )
    copy_btn.pack(side="left", padx=(0, spacing["inner"]))
    del_btn.pack(side="left")

    # Code copy button (if applicable)
    if any(kind == "code" for kind, _ in _extract_segments(self, text or "")):
        code_btn = tk.Button(
            actions,
            text="Copy Code",
            command=lambda mid=msg_id: self._on_copy_code(mid),
            **btn_config,
        )
        code_btn.pack(side="left", padx=(spacing["inner"], 0))

    actions.pack(anchor="e", pady=(0, spacing["inner"]), padx=spacing["inner"])

    # Timestamp
    if getattr(self, "show_timestamps", True):
        ts = self._timestamp()
        ts_lbl = tk.Label(
            msg_frame,
            text=ts,
            bg=bg,
            fg=colors.get("text_secondary", "#8892a6"),
            font=fonts["small"],
            anchor="e",
            justify="right",
        )
        ts_lbl.pack(anchor="e", pady=(0, spacing["inner"]), padx=spacing["inner"])

    # Scroll to bottom
    try:
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)
    except Exception:
        pass

    # Refresh search highlights
    if (
        hasattr(self, "_search_var")
        and (getattr(self, "_search_var").get() or "").strip()
    ):
        if hasattr(self, "_search_scan"):
            try:
                self._search_scan()
            except Exception:
                pass


def _on_copy_message(self, msg_id: int) -> None:
    record = self._messages.get(msg_id) if hasattr(self, "_messages") else None
    if record and hasattr(self, "_copy_to_clipboard"):
        try:
            self._copy_to_clipboard(record.get("text", ""))
        except Exception:
            pass


def _on_delete_message(self, msg_id: int) -> None:
    record = self._messages.get(msg_id) if hasattr(self, "_messages") else None
    if not record:
        return
    try:
        frame = record.get("frame")
        if frame is not None:
            frame.destroy()
    except Exception:
        pass
    try:
        self._messages.pop(msg_id, None)
    except Exception:
        pass

    try:
        cid = str(ui_state.get("active_chat_id", 1))
        msgs = ui_state.get("chat_messages", {}).get(cid, [])
        role = record.get("role")
        text = record.get("text")
        for i, m in enumerate(msgs):
            if m.get("role") == role and m.get("text") == text:
                msgs.pop(i)
                break
        if hasattr(self, "_save_chats"):
            self._save_chats()
    except Exception:
        pass


def _attach_context_menu(self, widget, read_only: bool = False) -> None:
    menu = tk.Menu(self.root, tearoff=0)

    def do(cmd: str):
        try:
            widget.event_generate(cmd)
        except Exception:
            pass
        return "break"

    if not read_only:
        menu.add_command(label="Cut", command=lambda: do("<<Cut>>"))
    menu.add_command(label="Copy", command=lambda: do("<<Copy>>"))
    if not read_only:
        menu.add_command(label="Paste", command=lambda: do("<<Paste>>"))
    menu.add_separator()

    def select_all():
        try:
            widget.tag_add("sel", "1.0", "end")
        except Exception:
            try:
                widget.selection_range(0, "end")
            except Exception:
                pass

    menu.add_command(label="Select All", command=select_all)

    def popup(event):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            try:
                menu.grab_release()
            except Exception:
                pass

    widget.bind("<Button-3>", popup)
    widget.bind("<Control-Button-1>", popup)


def _make_role_badge(self, parent, role: str):
    text = f"[{(role or 'msg').upper()}]"
    _bg, _fg, bbg, bfg = self._bubble_colors_for_role(role)
    return tk.Label(
        parent,
        text=text,
        bg=bbg,
        fg=bfg,
        font=STYLE["fonts"]["small"],
        padx=STYLE["spacing"]["s"],
        pady=1,
    )


def _bubble_colors_for_role(self, role: str):
    c = STYLE["colors"]
    r = (role or "").lower()
    if r == "user":
        return (
            c.get("background", "#0b1220"),
            c.get("text_primary", "#e6ecff"),
            c.get("panel_light", "#2a3a5a"),
            c.get("accent_fg", "#dbe6ff"),
        )
    if r == "assistant":
        return (
            c.get("panel", "#121a2b"),
            c.get("text_primary", "#e6ecff"),
            c.get("success_bg", "#194d33"),
            c.get("success_fg", "#d9f2e6"),
        )
    # system/other
    return (
        c.get("panel_light", "#0f1524"),
        c.get("text_secondary", "#95a1bb"),
        c.get("border", "#444f6a"),
        c.get("text_primary", "#e6ecff"),
    )


def _timestamp(self) -> str:
    return datetime.now().strftime("%H:%M")


def _extract_segments(self, text: str):
    text = text or ""
    segments = []
    cursor = 0
    try:
        for match in FENCE_RE.finditer(text):
            start, end = match.span()
            if start > cursor:
                chunk = text[cursor:start]
                if chunk.strip():
                    segments.append(("text", chunk))
            lang = (match.group(1) or "code").strip() or "code"
            code = match.group(2) or ""
            segments.append(("code", (lang, code.rstrip())))
            cursor = end
        if cursor < len(text):
            tail = text[cursor:]
            if tail.strip():
                segments.append(("text", tail))
        if not segments and text.strip():
            segments.append(("text", text))
    except Exception:
        if text.strip():
            segments.append(("text", text))
    return segments


__all__ = ["attach_renderer"]
