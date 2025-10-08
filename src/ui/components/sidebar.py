# src/ui/components/sidebar.py
"""
Professional, unified sidebar — fully respects STYLE design tokens.
All colors, fonts, and spacing are sourced from STYLE for consistency.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import simpledialog
from types import MethodType
from .style import STYLE
from .widgets import RoundedFrame
from ..state import ui_state


def render_sidebar(app) -> None:
    """Build the project/chat sidebar onto the provided app instance."""
    _attach_sidebar_methods(app)

    colors = STYLE["colors"]
    fonts = STYLE["fonts"]
    pad = STYLE["padding"]

    app.sidebar = RoundedFrame(app.hpanes, bg=colors["panel"])
    app.hpanes.add(app.sidebar, minsize=220, stretch="always")
    app.sidebar.grid_propagate(False)
    app.sidebar.configure(width=280)

    sidebar_body = tk.Frame(app.sidebar, bg=colors["panel"])
    sidebar_body.pack(fill="both", expand=True)

    # ─────────────── Project Controls ───────────────
    project_top = tk.Frame(sidebar_body, bg=colors["panel"])
    project_top.pack(
        side="top", fill="x", padx=pad["widget"], pady=(pad["widget"], pad["inner"])
    )

    tk.Label(
        project_top,
        text="Projects",
        bg=colors["panel"],
        fg=colors["text_secondary"],
        font=fonts.get("subtitle", fonts.get("body", ("TkDefaultFont", 12, "bold"))),
    ).pack(side="left")

    # Project actions: + (new), – (delete), ✎ (rename)
    proj_actions = tk.Frame(project_top, bg=colors["panel"])
    proj_actions.pack(side="right")

    action_btn_config = {
        "width": 2,
        "bg": colors["panel"],
        "fg": colors["text_primary"],
        "highlightthickness": 1,
        "highlightbackground": colors["border"],
        "bd": 0,
        "font": fonts["button"],
    }

    tk.Button(
        proj_actions,
        text="✎",
        command=lambda: app._rename_selected_project_dialog(),
        **action_btn_config,
    ).pack(side="right", padx=(pad["inner"], 0))

    tk.Button(
        proj_actions,
        text="–",
        command=lambda: app._delete_selected_project(),
        bg=colors["accent"],
        fg=colors["accent_fg"],
        highlightthickness=1,
        highlightbackground=colors["border"],
        bd=0,
        font=fonts["button"],
        width=2,
    ).pack(side="right", padx=(pad["inner"], 0))

    tk.Button(
        proj_actions,
        text="+",
        command=app._new_project,
        bg=colors["accent"],
        fg=colors["accent_fg"],
        highlightthickness=1,
        highlightbackground=colors["border"],
        bd=0,
        font=fonts["button"],
        width=2,
    ).pack(side="right")

    # Project List
    app.project_list = tk.Listbox(
        sidebar_body,
        activestyle="dotbox",
        height=4,
        bg=colors["panel"],
        fg=colors["text_primary"],
        highlightthickness=1,
        highlightbackground=colors["border"],
        selectbackground=colors.get("selection_bg", colors["accent"]),
        selectforeground=colors["accent_fg"],
        font=fonts["body"],
    )
    app.project_list.pack(
        side="top", fill="x", padx=pad["widget"], pady=(0, pad["widget"])
    )
    app.project_list.bind("<<ListboxSelect>>", app._on_project_selected)
    app.project_list.bind(
        "<Double-Button-1>", lambda e: app._rename_selected_project_dialog()
    )
    app.project_list.bind("<Return>", lambda e: app._rename_selected_project_dialog())

    # ─────────────── Chat Controls ───────────────
    chat_top = tk.Frame(sidebar_body, bg=colors["panel"])
    chat_top.pack(side="top", fill="x", padx=pad["widget"], pady=(0, pad["inner"]))

    tk.Label(
        chat_top,
        text="Chats",
        bg=colors["panel"],
        fg=colors["text_secondary"],
        font=fonts.get("subtitle", fonts.get("body", ("TkDefaultFont", 12, "bold"))),
    ).pack(side="left")

    chat_actions = tk.Frame(chat_top, bg=colors["panel"])
    chat_actions.pack(side="right")

    tk.Button(
        chat_actions,
        text="✎",
        command=lambda: app._rename_selected_chat_dialog(),
        **action_btn_config,
    ).pack(side="right", padx=(pad["inner"], 0))

    tk.Button(
        chat_actions,
        text="–",
        command=lambda: app._delete_selected_chat(),
        bg=colors["accent"],
        fg=colors["accent_fg"],
        highlightthickness=1,
        highlightbackground=colors["border"],
        bd=0,
        font=fonts["button"],
        width=2,
    ).pack(side="right", padx=(pad["inner"], 0))

    tk.Button(
        chat_actions,
        text="+",
        command=app._new_chat,
        bg=colors["accent"],
        fg=colors["accent_fg"],
        highlightthickness=1,
        highlightbackground=colors["border"],
        bd=0,
        font=fonts["button"],
        width=2,
    ).pack(side="right")

    # Chat Action Buttons (row)
    btn_frame = tk.Frame(sidebar_body, bg=colors["panel"])
    btn_frame.pack(side="top", fill="x", padx=pad["widget"], pady=(0, pad["inner"]))

    for text, cmd in [
        ("Export", app._export_active_chat),
        ("Import", app._import_chat_from_file),
        ("Clear", app._clear_active_chat),
        ("Delete", app._delete_active_chat),
    ]:
        tk.Button(
            btn_frame,
            text=text,
            command=cmd,
            bg=colors["accent"],
            fg=colors["accent_fg"],
            highlightthickness=1,
            highlightbackground=colors["border"],
            bd=0,
            font=fonts["small"],
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, pad["inner"]) if text != "Delete" else (0, 0),
        )

    # Search
    search_frame = tk.Frame(sidebar_body, bg=colors["panel"])
    search_frame.pack(side="top", fill="x", padx=pad["widget"], pady=(0, pad["inner"]))

    app.search_entry = tk.Entry(
        search_frame,
        bg=colors.get("panel_light", colors["panel"]),
        fg=colors["text_primary"],
        highlightthickness=1,
        highlightbackground=colors["border"],
        relief="flat",
        font=fonts["body"],
        insertbackground=colors["text_primary"],
    )
    app.search_entry.pack(fill="x", padx=pad["inner"], pady=(0, pad["inner"]))

    # --- Placeholder (look-only) for search ---
    try:
        from .theme import STYLE as _STYLE_REF

        _ph_fg = _STYLE_REF["colors"].get("composer_placeholder", "#94a3b8")
        _tx_fg = _STYLE_REF["colors"].get("text_primary", "#e2e8f0")
    except Exception:
        _ph_fg, _tx_fg = "#94a3b8", "#e2e8f0"

    app._search_has_ph = False
    _ph_text = "Search chats"

    def _search_apply_placeholder():
        if app.search_entry.get().strip():
            return
        app._search_has_ph = True
        app.search_entry.configure(fg=_ph_fg, insertbackground=_ph_fg)
        app.search_entry.delete(0, "end")
        app.search_entry.insert(0, _ph_text)

    def _search_clear_placeholder(_e=None):
        if app._search_has_ph:
            app.search_entry.delete(0, "end")
        app._search_has_ph = False
        app.search_entry.configure(fg=_tx_fg, insertbackground=_tx_fg)

    def _search_maybe_restore(_e=None):
        if not app.search_entry.get().strip():
            _search_apply_placeholder()

    app.search_entry.bind("<FocusIn>", _search_clear_placeholder, add="+")
    app.search_entry.bind("<FocusOut>", _search_maybe_restore, add="+")
    _search_apply_placeholder()

    # Chat List
    app.chat_list = tk.Listbox(
        sidebar_body,
        activestyle="dotbox",
        bg=colors["panel"],
        fg=colors["text_primary"],
        highlightthickness=1,
        highlightbackground=colors["border"],
        selectbackground=colors.get("selection_bg", colors["accent"]),
        selectforeground=colors["accent_fg"],
        font=fonts["body"],
    )
    app.chat_list.pack(
        side="top",
        fill="both",
        expand=True,
        padx=pad["widget"],
        pady=(0, pad["widget"]),
    )
    _wire_listbox_hover(app.chat_list)

    app.chat_list.bind("<<ListboxSelect>>", app._on_chat_selected)
    app.chat_list.bind(
        "<Double-Button-1>", lambda e: app._rename_selected_chat_dialog()
    )
    app.chat_list.bind("<Return>", lambda e: app._rename_selected_chat_dialog())

    # ─────────────── Initialize UI State ───────────────
    app._populate_project_list()
    active_pid = ui_state.get("active_project_id")
    if active_pid is not None:
        app._select_project_in_list(active_pid)

    app._populate_chat_list()
    active_cid = ui_state.get("active_chat_id")
    if active_cid is not None:
        app._select_chat_in_list(active_cid)

    # ─────────────── Sidebar Toggle Tab ───────────────
    app.sidebar_tab = tk.Frame(
        app.root, bg=colors["accent"], width=10, height=80, cursor="hand2"
    )
    app.sidebar_tab.place(in_=app.sidebar, relx=1, rely=0.5, x=0, y=-40)
    app.sidebar_tab.bind("<Button-1>", app._toggle_sidebar)


def _attach_sidebar_methods(app) -> None:
    methods = {
        "_toggle_sidebar": _toggle_sidebar_impl,
        "_delete_selected_project": _delete_selected_project_impl,
        "_rename_selected_project_dialog": _rename_selected_project_dialog_impl,
        "_delete_selected_chat": _delete_selected_chat_impl,
        "_rename_selected_chat_dialog": _rename_selected_chat_dialog_impl,
    }
    for name, func in methods.items():
        if not hasattr(app, name):
            setattr(app, name, MethodType(func, app))


# ─────────────── Toggle Sidebar ───────────────


def _toggle_sidebar_impl(self, _event=None) -> None:
    """Toggle sidebar visibility."""
    visible = getattr(self, "sidebar_visible", True)
    if visible:
        try:
            self.hpanes.forget(self.sidebar)
        except Exception:
            pass
        self.sidebar_visible = False
        try:
            self.sidebar_tab.place_forget()
            self.sidebar_tab.place(in_=self.root, relx=0, rely=0.5, x=0, y=-40)
        except Exception:
            pass
    else:
        try:
            self.hpanes.add(self.sidebar, minsize=220, stretch="always")
            panes = self.hpanes.panes()
            if panes:
                self.hpanes.paneconfig(self.sidebar, before=panes[0])
        except Exception:
            pass
        self.sidebar_visible = True
        try:
            self.sidebar_tab.place_forget()
            self.sidebar_tab.place(in_=self.sidebar, relx=1, rely=0.5, x=0, y=-40)
        except Exception:
            pass


# ─────────────── Project Helpers ───────────────


def _get_selected_project_id(self) -> int | None:
    sel = getattr(self.project_list, "curselection", lambda: ())()
    if not sel:
        return None
    idx = sel[0]
    projects = ui_state.get("projects", [])
    if idx >= len(projects):
        return None
    return projects[idx].get("id")


def _delete_selected_project_impl(self) -> None:
    pid = _get_selected_project_id(self)
    if pid is None:
        return
    if hasattr(self, "_delete_project"):
        self._delete_project(pid)
        self._populate_project_list()
        self._populate_chat_list()


def _rename_selected_project_dialog_impl(self) -> None:
    pid = _get_selected_project_id(self)
    if pid is None:
        return
    projects = ui_state.get("projects", [])
    current = next((p.get("name") for p in projects if p.get("id") == pid), "Project")
    try:
        new_name = simpledialog.askstring(
            "Rename Project",
            "New project name:",
            initialvalue=current,
            parent=self.root,
        )
    except Exception:
        new_name = None
    if not new_name:
        return
    if hasattr(self, "_rename_project"):
        self._rename_project(pid, new_name.strip())
    self._populate_project_list()
    self._select_project_in_list(pid)


# ─────────────── Chat Helpers ───────────────


def _get_selected_chat_id(self) -> int | None:
    sel = getattr(self.chat_list, "curselection", lambda: ())()
    if not sel:
        return None
    idx = sel[0]
    active_pid = ui_state.get("active_project_id")
    if active_pid is None:
        return None
    project_chats = next(
        (
            p.get("chats", [])
            for p in ui_state.get("projects", [])
            if p.get("id") == active_pid
        ),
        [],
    )
    if idx >= len(project_chats):
        return None
    return project_chats[idx]


def _delete_selected_chat_impl(self) -> None:
    cid = _get_selected_chat_id(self)
    if cid is None:
        return
    try:
        ui_state["active_chat_id"] = cid
    except Exception:
        pass
    if hasattr(self, "_delete_active_chat"):
        self._delete_active_chat()


def _rename_selected_chat_dialog_impl(self) -> None:
    cid = _get_selected_chat_id(self)
    if cid is None:
        return
    chat = next((c for c in ui_state.get("chats", []) if c.get("id") == cid), None)
    current = chat.get("title", f"Chat {cid}") if chat else f"Chat {cid}"
    try:
        new_title = simpledialog.askstring(
            "Rename Chat", "New chat title:", initialvalue=current, parent=self.root
        )
    except Exception:
        new_title = None
    if not new_title:
        return
    new_title = new_title.strip()
    if not new_title:
        return
    for c in ui_state.get("chats", []):
        if c.get("id") == cid:
            c["title"] = new_title
            break
    if hasattr(self, "_save_chats"):
        self._save_chats()
    self._populate_chat_list()
    self._select_chat_in_list(cid)


# --- Sidebar Row Hover Shim (Listbox look-only) ---
def _wire_listbox_hover(lb):
    """
    Visually highlight the row under the mouse without changing
    the real selection unless the user clicks.
    """

    try:
        from .theme import STYLE  # uses the tokens you just added
    except Exception:
        STYLE = {"colors": {}}
    colors = STYLE.get("colors", {})
    hover_bg = colors.get("sidebar_row_hover_bg", "#15213d")
    active_bg = colors.get("sidebar_row_active_bg", "#1a2a4a")
    text_fg = colors.get("text_primary", "#e2e8f0")

    lb._hover_idx = None
    lb._saved_sel = ()
    lb._was_hovering = False

    def _save_selection():
        sel = lb.curselection()
        lb._saved_sel = tuple(sel) if sel else ()

    def _restore_selection():
        lb.configure(selectbackground=active_bg, selectforeground=text_fg)
        lb.selection_clear(0, "end")
        for idx in lb._saved_sel:
            try:
                lb.selection_set(idx)
            except Exception:
                pass

    def _set_hover(idx):
        lb.configure(selectbackground=hover_bg, selectforeground=text_fg)
        lb.selection_clear(0, "end")
        try:
            lb.selection_set(idx)
        except Exception:
            pass

    def _nearest_index(event):
        try:
            return lb.nearest(event.y)
        except Exception:
            return None

    def _on_motion(event):
        idx = _nearest_index(event)
        if idx is None:
            return
        if not lb._was_hovering:
            _save_selection()
            lb._was_hovering = True
        _set_hover(idx)

    def _on_leave(_event=None):
        if lb._was_hovering:
            _restore_selection()
            lb._was_hovering = False

    def _on_click(event):
        idx = _nearest_index(event)
        if idx is None:
            return
        lb.configure(selectbackground=active_bg, selectforeground=text_fg)
        _restore_selection()
        try:
            lb.selection_set(idx)
        except Exception:
            pass
        lb._was_hovering = False

    lb.bind("<Motion>", _on_motion, add="+")
    lb.bind("<Leave>", _on_leave, add="+")
    lb.bind("<Button-1>", _on_click, add="+")

    try:
        lb.configure(cursor="hand2")
        lb.configure(selectbackground=active_bg, selectforeground=text_fg)
    except Exception:
        pass


__all__ = ["render_sidebar"]
