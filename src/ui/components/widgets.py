# src/ui/components/widgets.py
"""
Shared UI primitives for Adam’s Tk interface — fully respects STYLE design tokens.
"""

from .style import STYLE
import tkinter as tk
from tkinter import font


def _rounded_points(x1, y1, x2, y2, radius):
    """Generate polygon points for a rounded rectangle."""
    return [
        x1 + radius,
        y1,
        x2 - radius,
        y1,
        x2,
        y1,
        x2,
        y1 + radius,
        x2,
        y2 - radius,
        x2,
        y2,
        x2 - radius,
        y2,
        x1 + radius,
        y2,
        x1,
        y2,
        x1,
        y2 - radius,
        x1,
        y1 + radius,
        x1,
        y1,
    ]


def _resolve_radius(value):
    """Resolve radius value: number, 'small', 'medium', or default."""
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        return STYLE.get("radius", {}).get(value, 8)
    # Default to medium
    return STYLE.get("radius", {}).get("medium", 8)


class RoundedButton(tk.Canvas):
    """A stylized button with rounded corners that works like a normal Tk button."""

    def __init__(self, master, text, command, **kwargs):
        colors = STYLE["colors"]
        fonts = STYLE["fonts"]
        spacing = STYLE["spacing"]

        # Resolve colors and fonts with fallbacks
        self.bg = kwargs.pop("bg", colors.get("accent", "#7f5af0"))
        self.fg = kwargs.pop("fg", colors.get("accent_fg", "#ffffff"))
        self.hover_bg = kwargs.pop(
            "activebackground", colors.get("panel_light", "#2c2c44")
        )
        self.font = kwargs.pop("font", fonts.get("button", ("Segoe UI", 11, "bold")))

        # Use spacing tokens for padding
        default_pad_x = spacing.get("l", 16)
        default_pad_y = spacing.get("m", 12)
        padx = kwargs.pop("padx", default_pad_x)
        pady = kwargs.pop("pady", default_pad_y)

        # Resolve radius
        radius_input = kwargs.pop("radius", "medium")
        self.radius = _resolve_radius(radius_input)

        # Calculate size based on text
        font_obj = font.Font(font=self.font)
        text_width = font_obj.measure(text)
        text_height = font_obj.metrics("linespace")
        width = text_width + 2 * padx
        height = text_height + 2 * pady

        # Initialize canvas
        master_bg = master.cget("bg") if master else colors.get("background", "#1e1e2f")
        super().__init__(
            master, width=width, height=height, highlightthickness=0, bg=master_bg
        )

        self.command = command
        self.text = text

        # Draw rounded button
        self.shape = self.create_polygon(
            _rounded_points(0, 0, width, height, self.radius),
            fill=self.bg,
            smooth=True,
            outline="",  # Prevent anti-aliasing artifacts
        )
        self.label = self.create_text(
            width / 2, height / 2, text=text, font=self.font, fill=self.fg
        )

        # Bind events
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_click(self, _event=None):
        if self.command:
            self.command()

    def _on_enter(self, _event=None):
        self.itemconfig(self.shape, fill=self.hover_bg)

    def _on_leave(self, _event=None):
        self.itemconfig(self.shape, fill=self.bg)


class RoundedFrame(tk.Frame):
    """A panel-like frame with rounded background. Lightweight redraw."""

    def __init__(self, master, **kwargs):
        colors = STYLE["colors"]

        # Resolve background and radius
        self._bg_color = kwargs.pop("bg", colors.get("panel", "#25253a"))
        radius_input = kwargs.pop("radius", "medium")
        self._radius = _resolve_radius(radius_input)

        self._bordercolor = kwargs.pop("bordercolor", None)
        self._borderwidth = kwargs.pop("borderwidth", 0)

        # Initialize frame with transparent background
        master_bg = master.cget("bg") if master else colors.get("background", "#1e1e2f")
        super().__init__(master, bg=master_bg, **kwargs)

        # Create background canvas
        self._bg_canvas = tk.Canvas(self, highlightthickness=0, bg=master_bg)
        self._bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Create rounded shape
        self._bg_shape = self._bg_canvas.create_polygon(
            _rounded_points(0, 0, 1, 1, self._radius),
            fill=self._bg_color,
            smooth=True,
            outline=self._bordercolor if self._bordercolor else "",
            width=self._borderwidth if self._bordercolor else 0,
        )

        # Ensure canvas is behind children
        try:
            self._bg_canvas.lower()
        except Exception:
            pass

        self._pending = None

        def _on_cfg(_e):
            # Throttle redraws to ~60fps
            if self._pending:
                self.after_cancel(self._pending)
            self._pending = self.after(16, self._redraw)

        self._bg_canvas.bind("<Configure>", _on_cfg)

    def _redraw(self):
        self._pending = None
        w = max(self._bg_canvas.winfo_width(), 1)
        h = max(self._bg_canvas.winfo_height(), 1)
        self._bg_canvas.coords(
            self._bg_shape, *_rounded_points(0, 0, w, h, self._radius)
        )
