# src/ui/components/menu.py
"""
Main application menubar — File, Edit, View, Theme, Help.
Provides standard desktop application menu structure.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import simpledialog, messagebox
import sys


def attach_menubar(app) -> None:
    """
    Creates a full application menubar with standard menus.
    Idempotent: safe to call multiple times.
    """
    # Reuse or create menubar
    menubar = getattr(app, "_menubar", None)
    if not isinstance(menubar, tk.Menu):
        menubar = tk.Menu(app.root)
        app.root.configure(menu=menubar)
        app._menubar = menubar

    # Clear existing menus (for refresh)
    try:
        menubar.delete(0, "end")
    except Exception:
        pass

    # ─────────────── File Menu ───────────────
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="File", menu=file_menu)

    # File → New Chat
    file_menu.add_command(label="New Chat", command=app._new_chat, accelerator="Ctrl+N")
    app.root.bind_all("<Control-n>", lambda e: app._new_chat())

    # File → Export Chat
    file_menu.add_command(
        label="Export Chat…", command=app._export_active_chat, accelerator="Ctrl+E"
    )
    app.root.bind_all("<Control-e>", lambda e: app._export_active_chat())

    # File → Import Chat
    file_menu.add_command(
        label="Import Chat…", command=app._import_chat_from_file, accelerator="Ctrl+I"
    )
    app.root.bind_all("<Control-i>", lambda e: app._import_chat_from_file())

    file_menu.add_separator()

    # File → Clear Chat
    file_menu.add_command(
        label="Clear Chat", command=app._clear_active_chat, accelerator="Ctrl+L"
    )
    app.root.bind_all("<Control-l>", lambda e: app._clear_active_chat())

    # File → Delete Chat
    file_menu.add_command(
        label="Delete Chat",
        command=lambda: app._delete_active_chat(),
        accelerator="Ctrl+Shift+D",
    )
    app.root.bind_all("<Control-Shift-D>", lambda e: app._delete_active_chat())

    file_menu.add_separator()

    # File → Exit
    file_menu.add_command(
        label="Exit", command=lambda: sys.exit(0), accelerator="Alt+F4"
    )

    # ─────────────── Edit Menu ───────────────
    edit_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Edit", menu=edit_menu)

    # Edit → Undo/Redo (if supported)
    edit_menu.add_command(label="Undo", state="disabled")  # Optional: implement later
    edit_menu.add_command(label="Redo", state="disabled")
    edit_menu.add_separator()

    # Edit → Cut/Copy/Paste (global)
    def _global_cut():
        try:
            app.root.focus_get().event_generate("<<Cut>>")
        except Exception:
            pass

    def _global_copy():
        try:
            app.root.focus_get().event_generate("<<Copy>>")
        except Exception:
            pass

    def _global_paste():
        try:
            app.root.focus_get().event_generate("<<Paste>>")
        except Exception:
            pass

    edit_menu.add_command(label="Cut", command=_global_cut, accelerator="Ctrl+X")
    edit_menu.add_command(label="Copy", command=_global_copy, accelerator="Ctrl+C")
    edit_menu.add_command(label="Paste", command=_global_paste, accelerator="Ctrl+V")
    app.root.bind_all("<Control-x>", lambda e: _global_cut())
    app.root.bind_all("<Control-c>", lambda e: _global_copy())
    app.root.bind_all("<Control-v>", lambda e: _global_paste())

    # ─────────────── View Menu ───────────────
    view_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="View", menu=view_menu)

    # View → Toggle Sidebar
    view_menu.add_command(
        label="Toggle Sidebar", command=app._toggle_sidebar, accelerator="Ctrl+B"
    )
    app.root.bind_all("<Control-b>", lambda e: app._toggle_sidebar())

    # View → Toggle Canvas
    view_menu.add_command(
        label="Toggle Canvas", command=app._toggle_canvas, accelerator="Ctrl+U"
    )
    app.root.bind_all("<Control-u>", lambda e: app._toggle_canvas())

    # View → Toggle Params
    view_menu.add_command(
        label="Toggle Parameters",
        command=app._toggle_params_panel,
        accelerator="Ctrl+P",
    )
    app.root.bind_all("<Control-p>", lambda e: app._toggle_params_panel())

    # View → Toggle Timestamps
    view_menu.add_command(
        label="Toggle Timestamps", command=app._toggle_timestamps, accelerator="Ctrl+T"
    )
    app.root.bind_all("<Control-t>", lambda e: app._toggle_timestamps())

    view_menu.add_separator()

    # View → Reset Layout
    def _reset_layout():
        if hasattr(app, "_rebalance_panes"):
            app._rebalance_panes()

    view_menu.add_command(label="Reset Layout", command=_reset_layout)

    # ─────────────── Theme Menu ───────────────
    # Only attach if theme system is available
    if all(
        hasattr(app, name)
        for name in (
            "_theme_list",
            "_load_theme",
            "_save_theme",
            "_delete_theme",
            "_apply_theme",
        )
    ):
        theme_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Theme", menu=theme_menu)

        theme_menu.add_command(label="Save as…", command=lambda: _save_theme_as(app))

        # Mode (Dark/Light) — visual only
        try:
            app._theme_mode_var = tk.StringVar(value="dark")
        except Exception:
            app._theme_mode_var = tk.StringVar()
        mode_menu = tk.Menu(theme_menu, tearoff=0)
        theme_menu.add_cascade(label="Mode", menu=mode_menu)
        mode_menu.add_radiobutton(
            label="Dark",
            variable=app._theme_mode_var,
            value="dark",
            command=lambda: app.set_theme_mode("dark"),
        )
        mode_menu.add_radiobutton(
            label="Light",
            variable=app._theme_mode_var,
            value="light",
            command=lambda: app.set_theme_mode("light"),
        )

        # Presets
        presets_menu = tk.Menu(theme_menu, tearoff=0)
        theme_menu.add_cascade(label="Presets…", menu=presets_menu)
        _populate_presets_menu(app, presets_menu)

        # Delete
        delete_menu = tk.Menu(theme_menu, tearoff=0)
        theme_menu.add_cascade(label="Delete preset…", menu=delete_menu)
        _populate_delete_menu(app, delete_menu)

        # Store for refresh
        app._theme_presets_menu = presets_menu
        app._theme_delete_menu = delete_menu

    # ─────────────── Help Menu ───────────────
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Help", menu=help_menu)

    def _show_about():
        messagebox.showinfo("About Adam", "Adam — Modern AI Assistant\n\nVersion 1.0")

    help_menu.add_command(label="About", command=_show_about)

    # Optional: Add documentation link (if you have a website)
    # help_menu.add_command(label="Documentation", command=lambda: webbrowser.open("https://your-docs.com"))


# ─────────────── Theme Helpers (from original) ───────────────


def _populate_presets_menu(app, menu: tk.Menu) -> None:
    _clear_menu(menu)
    try:
        names = app._theme_list() or []
    except Exception:
        names = []

    if not names:
        menu.add_command(label="(no presets)", state="disabled")
        return

    for name in names:
        menu.add_command(
            label=name,
            command=lambda n=name: _load_preset(app, n),
        )


def _populate_delete_menu(app, menu: tk.Menu) -> None:
    _clear_menu(menu)
    try:
        names = app._theme_list() or []
    except Exception:
        names = []

    if not names:
        menu.add_command(label="(no presets)", state="disabled")
        return

    for name in names:
        menu.add_command(
            label=name,
            command=lambda n=name: _delete_preset(app, n),
        )


def _save_theme_as(app) -> None:
    try:
        name = simpledialog.askstring("Save Theme", "Preset name:")
    except Exception:
        name = None
    if not name:
        return
    try:
        app._save_theme(name)
        _populate_presets_menu(app, app._theme_presets_menu)
        _populate_delete_menu(app, app._theme_delete_menu)
        messagebox.showinfo("Theme", f"Saved preset: {name}")
    except Exception:
        messagebox.showerror("Theme", "Failed to save theme.")


def _load_preset(app, name: str) -> None:
    try:
        app._load_theme(name)
        app._apply_theme()
        messagebox.showinfo("Theme", f"Loaded preset: {name}")
    except Exception:
        messagebox.showerror("Theme", f"Failed to load preset: {name}")


def _delete_preset(app, name: str) -> None:
    try:
        if messagebox.askyesno(
            "Delete Theme", f"Delete preset “{name}”? This cannot be undone."
        ):
            app._delete_theme(name)
            _populate_presets_menu(app, app._theme_presets_menu)
            _populate_delete_menu(app, app._theme_delete_menu)
    except Exception:
        messagebox.showerror("Theme", f"Failed to delete preset: {name}")


def _clear_menu(menu: tk.Menu) -> None:
    try:
        menu.delete(0, "end")
    except Exception:
        pass
