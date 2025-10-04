# src/ui/components/layout.py
"""
Main window layout — horizontal paned structure with sidebar, chat, and canvas.
Respects design tokens for widths, ratios, and spacing.
"""

from __future__ import annotations

import tkinter as tk
from .style import STYLE


def attach_layout(app) -> None:
    """Attach the main horizontal paned layout to the app."""
    layout_tokens = STYLE.get("layout", {})
    sash_width = layout_tokens.get("sash_width", 6)

    app.hpanes = tk.PanedWindow(
        app.root,
        orient="horizontal",
        sashwidth=sash_width,
        sashrelief="raised",
        bg=STYLE["colors"].get("sash", STYLE["colors"]["background"]),
        bd=0,
        showhandle=False,
        opaqueresize=True,
    )
    app.hpanes.grid(row=0, column=0, sticky="nsew")  # padx/pady=0 is default

    # Attach rebalance helper
    app._rebalance_panes = lambda: _rebalance_panes(app)
    app.root.after(80, app._rebalance_panes)

    # Rebalance on window resize
    def _on_root_cfg(_e):
        app._rebalance_panes()

    app.root.bind("<Configure>", _on_root_cfg)


def _rebalance_panes(app) -> None:
    """Maintain sensible proportions between sidebar / chat / canvas."""
    try:
        panes = app.hpanes.panes()
        if not panes:
            return

        # Get layout tokens
        layout_tokens = STYLE.get("layout", {})
        sidebar_width = layout_tokens.get("sidebar_width", 280)
        chat_ratio_with_canvas = layout_tokens.get("chat_ratio_with_canvas", 0.65)
        chat_ratio_solo = layout_tokens.get("chat_ratio_solo", 0.98)

        total_w = max(app.root.winfo_width(), 1)

        sidebar = getattr(app, "sidebar", None)
        canvas_container = getattr(app, "canvas_container", None)

        # Identify chat container (first non-sidebar, non-canvas pane)
        chat_container = None
        for p in panes:
            if sidebar and str(p) == str(sidebar):
                continue
            if canvas_container and str(p) == str(canvas_container):
                continue
            chat_container = p
            break

        # Apply layout logic
        if sidebar and str(sidebar) in panes:
            # Sidebar is visible
            has_canvas = canvas_container and str(canvas_container) in panes
            chat_ratio = chat_ratio_with_canvas if has_canvas else chat_ratio_solo
            chat_w = int((total_w - sidebar_width) * chat_ratio)

            # Position first sash (sidebar/chat)
            app.hpanes.sash_place(0, sidebar_width, 1)

            # Position second sash (chat/canvas) if needed
            if has_canvas and len(panes) >= 3:
                second_sash = sidebar_width + chat_w
                app.hpanes.sash_place(1, second_sash, 1)
        else:
            # Sidebar hidden
            has_canvas = canvas_container and str(canvas_container) in panes
            if has_canvas and len(panes) >= 2:
                chat_w = int(total_w * chat_ratio_with_canvas)
                app.hpanes.sash_place(0, chat_w, 1)
            # else: only one pane → no sash needed
    except Exception:
        pass


__all__ = ["attach_layout"]
