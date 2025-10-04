# src/ui/components/chat.py
"""
Professional, unified chat UI — fully respects STYLE design tokens.
All colors, fonts, and spacing are sourced from STYLE to ensure consistency.
"""

from __future__ import annotations

import threading
import tkinter as tk
from types import MethodType

from .style import STYLE
from .widgets import RoundedFrame, RoundedButton
from ..utils.validation import extract_code_blocks


# --- Universal Context Menu (Reusable) ---
def _attach_context_menu(self, widget, read_only=False) -> None:
    """Attach a right-click context menu to any text/entry widget."""
    menu = tk.Menu(
        widget,
        tearoff=0,
        bg=STYLE["colors"]["panel"],
        fg=STYLE["colors"]["text_primary"],
    )

    def _select_all():
        if isinstance(widget, tk.Entry):
            widget.select_range(0, "end")
            widget.icursor("end")
        elif isinstance(widget, tk.Text):
            widget.tag_add("sel", "1.0", "end-1c")

    def _copy():
        original_state = widget.cget("state")
        if original_state == "disabled":
            widget.config(state="normal")
        try:
            if widget.selection_get():
                self.root.clipboard_clear()
                self.root.clipboard_append(widget.selection_get())
        except tk.TclError:
            pass
        if original_state == "disabled":
            widget.config(state="disabled")

    def _paste():
        try:
            widget.insert(tk.INSERT, self.root.clipboard_get())
        except tk.TclError:
            pass

    menu.add_command(label="Copy", command=_copy)
    if not read_only:
        menu.add_command(label="Paste", command=_paste)
    menu.add_separator()
    menu.add_command(label="Select All", command=_select_all)

    def _show_menu(event):
        system = self.root.tk.call("tk", "windowingsystem")
        is_secondary = (
            event.num == 3
            or (system == "aqua" and event.state & 0x4)
            or (system in ("x11", "win32") and event.num == 2)
        )
        if is_secondary:
            original_state = widget.cget("state")
            if original_state == "disabled":
                widget.config(state="normal")
            menu.tk_popup(event.x_root, event.y_root)
            if original_state == "disabled":
                self.root.after(100, lambda: widget.config(state="disabled"))

    widget.bind("<Button-2>", _show_menu)
    widget.bind("<Button-3>", _show_menu)
    widget.bind("<Control-Button-1>", _show_menu)


def _make_readonly_text(self, widget: tk.Text) -> None:
    """Configure a Text widget to behave as read-only while allowing selection/copy."""
    widget.configure(state="normal")
    widget.configure(cursor="xterm")

    def _focus(_event):
        try:
            widget.focus_set()
        except Exception:
            pass

    widget.bind("<Button-1>", _focus, add=True)
    widget.bind("<Button-2>", _focus, add=True)
    widget.bind("<Button-3>", _focus, add=True)

    def _on_key(event):
        keysym = event.keysym.lower() if hasattr(event, "keysym") else ""
        ctrl = bool(event.state & 0x4)
        nav_keys = {"left", "right", "up", "down", "home", "end", "prior", "next"}
        if ctrl and keysym == "a":
            widget.tag_add("sel", "1.0", "end-1c")
            return "break"
        if ctrl and keysym == "c":
            return None  # allow default copy binding
        if keysym in nav_keys:
            return None
        if ctrl and keysym in {"v", "x"}:
            return "break"
        if keysym in {"shift_l", "shift_r"}:
            return None
        return "break"

    widget.bind("<Key>", _on_key, add=True)
    widget.bind("<<Paste>>", lambda _e: "break", add=True)
    widget.bind("<<Cut>>", lambda _e: "break", add=True)
    widget.bind("<<Clear>>", lambda _e: "break", add=True)


# --- Public API ---
def render_chat(app) -> None:
    """Initialize and render the chat interface."""
    _attach_chat_methods(app)
    app._build_chat_area()
    app._build_canvas_panel()
    app._build_input_area()


def _attach_chat_methods(app) -> None:
    """Bind chat-related methods to the app instance."""
    methods = {
        "_attach_context_menu": _attach_context_menu,
        "_make_readonly_text": _make_readonly_text,
        "_build_chat_area": _build_chat_area,
        "_build_canvas_panel": _build_canvas_panel,
        "_build_input_area": _build_input_area,
        "_toggle_canvas": _toggle_canvas,
        "_ensure_canvas_visible": _ensure_canvas_visible,
        "_ui_stop_generation": _ui_stop_generation,
        "_toggle_params_panel": _toggle_params_panel,
        "_build_params_panel": _build_params_panel,
        "_clear_canvas": _clear_canvas,
        "_submit_message": _submit_message,
        "_on_send_shortcut": _on_send_shortcut,
        "_handle_return": _handle_return,
        "_entry_select_all": _entry_select_all,
        "_render_response": _render_response,
        "_add_card": _add_card,
        "_on_copy_code": _on_copy_code,
        "_chat_yscroll": _chat_yscroll,
        "_update_scroll_button": _update_scroll_button,
        "_scroll_to_bottom": _scroll_to_bottom,
        "_toolbar_responsive": _toolbar_responsive,
    }
    for name, func in methods.items():
        setattr(app, name, MethodType(func, app))


# --- Chat Area ---
def _build_chat_area(self) -> None:
    pad = STYLE["spacing"]
    colors = STYLE["colors"]
    fonts = STYLE["fonts"]

    container = tk.Frame(self.hpanes, bg=colors["background"])
    self.hpanes.add(container, minsize=400, stretch="always")
    container.grid_rowconfigure(2, weight=1)
    container.grid_columnconfigure(0, weight=1)
    self.main_container = container

    # --- Top Toolbar ---
    top = tk.Frame(container, bg=colors["background"])
    top.grid(row=0, column=0, sticky="ew", pady=(0, pad["inner"]))
    top.grid_columnconfigure(0, weight=1)

    # Search controls
    search_wrap = tk.Frame(top, bg=colors["background"])
    search_wrap.pack(side="right", padx=(6, 6))
    search_var = getattr(self, "_search_var", tk.StringVar(value=""))
    self._search_var = search_var
    search_entry = tk.Entry(
        search_wrap,
        textvariable=search_var,
        width=18,
        bg=colors["background"],
        fg=colors["text_primary"],
        highlightthickness=1,
        highlightbackground=colors["border"],
        insertbackground=colors["text_primary"],
        font=fonts["body"],
    )
    search_entry.pack(side="left")
    self._attach_context_menu(search_entry)

    btn_config = {
        "bg": colors["accent"],
        "fg": colors["accent_fg"],
        "highlightthickness": 1,
        "highlightbackground": colors["border"],
        "bd": 0,
        "font": fonts["button"],
    }
    prev_btn = tk.Button(search_wrap, text="◀", command=self._search_prev, **btn_config)
    next_btn = tk.Button(search_wrap, text="▶", command=self._search_next, **btn_config)
    clear_btn = tk.Button(
        search_wrap, text="✕", command=self._search_clear, **btn_config
    )
    prev_btn.pack(side="left", padx=(6, 2))
    next_btn.pack(side="left", padx=2)
    clear_btn.pack(side="left", padx=(2, 0))
    search_entry.bind("<Return>", lambda _e: self._search_next())

    # Primary buttons
    self.canvas_button = RoundedButton(
        top,
        text="🎨 Canvas",
        command=self._toggle_canvas,
        bg=colors["accent"],
        fg=colors["accent_fg"],
        font=fonts["button"],
    )
    self.params_button = RoundedButton(
        top,
        text="⚙️ Params",
        command=self._toggle_params_panel,
        bg=colors["panel"],
        fg=colors["text_primary"],
        font=fonts["button"],
    )
    self.stop_button = RoundedButton(
        top,
        text="⏹ Stop",
        command=self._ui_stop_generation,
        bg=colors["accent"],
        fg=colors["accent_fg"],
        font=fonts["button"],
    )
    self.canvas_button.pack(side="right", padx=(0, 0))
    self.params_button.pack(side="right", padx=(6, 0))
    self.stop_button.pack(side="right", padx=(6, 6))

    # Optional buttons (responsive)
    optional_btns = []
    for text, cmd in [
        ("Customize", self._open_theme_dialog),
        ("Refresh Models", self._refresh_models_from_backend),
    ]:
        btn = tk.Button(
            top,
            text=text,
            command=cmd,
            bg=colors["panel"],
            fg=colors["text_primary"],
            highlightthickness=1,
            highlightbackground=colors["border"],
            bd=0,
            font=fonts["button"],
        )
        optional_btns.append(btn)

    self.timestamp_button = tk.Button(
        top,
        text=(
            "Timestamps: ON"
            if getattr(self, "show_timestamps", True)
            else "Timestamps: OFF"
        ),
        command=self._toggle_timestamps,
        bg=colors["panel"],
        fg=colors["text_primary"],
        highlightthickness=1,
        highlightbackground=colors["border"],
        bd=0,
        font=fonts["button"],
    )
    optional_btns.insert(0, self.timestamp_button)  # Keep timestamps first

    for btn in optional_btns:
        btn.pack(side="right", padx=6)

    self._toolbar_optional = [
        (btn, (btn.cget("text"), btn.cget("command"))) for btn in optional_btns
    ]

    # Kebab menu for overflow
    self._toolbar_overflow = tk.Menu(
        top, tearoff=0, bg=colors["panel"], fg=colors["text_primary"]
    )
    self._toolbar_kebab = tk.Menubutton(
        top,
        text="⋮",
        relief="flat",
        bg=colors["panel"],
        fg=colors["text_primary"],
        highlightthickness=1,
        highlightbackground=colors["border"],
        font=fonts["button"],
    )
    self._toolbar_kebab.configure(menu=self._toolbar_overflow)
    self._toolbar_kebab.pack(side="right", padx=(0, 6))
    self._toolbar_kebab.pack_forget()

    def _refresh_kebab_labels():
        label = (
            "Timestamps: ON"
            if getattr(self, "show_timestamps", True)
            else "Timestamps: OFF"
        )
        self.timestamp_button.configure(text=label)

    self._refresh_kebab_labels = _refresh_kebab_labels

    # Store references for responsive layout
    self._toolbar_refs = {
        "top": top,
        "search_wrap": search_wrap,
    }

    # Bind responsive layout with debouncing
    def _on_configure(event):
        if hasattr(self, "_resize_timer"):
            top.after_cancel(self._resize_timer)
        self._resize_timer = top.after(50, self._toolbar_responsive)

    top.bind("<Configure>", _on_configure)
    self._toolbar_responsive()  # Initial layout

    chat_wrapper = RoundedFrame(container, bg=colors["panel_light"])
    chat_wrapper.grid(row=2, column=0, sticky="nsew")
    chat_body = tk.Frame(chat_wrapper, bg=colors["panel_light"])
    chat_body.pack(fill="both", expand=True, padx=2, pady=2)

    self.chat_canvas = tk.Canvas(
        chat_body, bg=colors["panel_light"], highlightthickness=0
    )
    scrollbar = tk.Scrollbar(
        chat_body, orient="vertical", command=self.chat_canvas.yview
    )
    self.chat_log = tk.Frame(self.chat_canvas, bg=colors["panel_light"])
    print("DEBUG: chat_log created:", self.chat_log)
    self.chat_log.bind(
        "<Configure>",
        lambda _e: self.chat_canvas.configure(
            scrollregion=self.chat_canvas.bbox("all")
        ),
    )
    self.chat_canvas.create_window((0, 0), window=self.chat_log, anchor="nw")
    self.chat_canvas.configure(yscrollcommand=scrollbar.set)

    self.chat_canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    print("DEBUG: _build_chat_area completed")
    # Process any pending messages...


# --- Responsive Toolbar Function ---
def _toolbar_responsive(self, _e=None):
    try:
        refs = getattr(self, "_toolbar_refs", {})
        top = refs.get("top")
        search_wrap = refs.get("search_wrap")

        if not top or not top.winfo_exists():
            return

        if not search_wrap or not search_wrap.winfo_exists():
            return

        avail = max(0, top.winfo_width() - 20)
        try:
            fixed_width = (
                search_wrap.winfo_reqwidth()
                + self.canvas_button.winfo_reqwidth()
                + self.params_button.winfo_reqwidth()
                + self.stop_button.winfo_reqwidth()
                + 40
            )
        except tk.TclError:
            return  # Widget destroyed

        total = fixed_width + sum(
            btn.winfo_reqwidth() + 12
            for btn, _ in self._toolbar_optional
            if hasattr(btn, "winfo_exists") and btn.winfo_exists()
        )
        hidden = []

        for btn, (label, cmd) in reversed(self._toolbar_optional):
            if not hasattr(btn, "winfo_exists") or not btn.winfo_exists():
                continue
            try:
                btn.pack_forget()
                if total <= avail:
                    btn.pack(side="right", padx=6)
                else:
                    hidden.append((label, cmd))
                total -= btn.winfo_reqwidth() + 12
            except tk.TclError:
                continue  # Skip destroyed buttons

        try:
            self._toolbar_overflow.delete(0, "end")
        except tk.TclError:
            pass

        for label, cmd in hidden:
            try:
                self._toolbar_overflow.add_command(label=label, command=cmd)
            except tk.TclError:
                pass

        if hidden:
            try:
                self._toolbar_kebab.pack(side="right", padx=(0, 6))
            except tk.TclError:
                pass
        else:
            try:
                self._toolbar_kebab.pack_forget()
            except tk.TclError:
                pass

    except Exception:
        pass


# --- Canvas Panel ---
def _build_canvas_panel(self) -> None:
    pad = STYLE["spacing"]
    colors = STYLE["colors"]
    fonts = STYLE["fonts"]

    self.canvas_container = RoundedFrame(self.hpanes, bg=colors["panel"])
    self.hpanes.add(self.canvas_container, minsize=320, stretch="always")
    self.canvas_container.grid_propagate(False)

    container_body = tk.Frame(self.canvas_container, bg=colors["panel"])
    container_body.pack(fill="both", expand=True)

    header = tk.Frame(container_body, bg=colors["panel"])
    header.pack(fill="x", padx=pad["widget"], pady=pad["widget"])
    tk.Label(
        header,
        text="Code Canvas",
        bg=colors["panel"],
        fg=colors["text_primary"],
        font=fonts["subtitle"],
    ).pack(side="left", padx=pad["inner"])

    clear_button = RoundedButton(
        header,
        text="Clear",
        command=self._clear_canvas,
        bg=colors["accent"],
        fg=colors["accent_fg"],
        font=fonts["button"],
        padx=12,
        pady=4,
    )
    clear_button.pack(side="right")

    body = tk.Frame(container_body, bg=colors["panel"])
    body.pack(fill="both", expand=True)

    self.canvas_canvas = tk.Canvas(body, bg=colors["panel"], highlightthickness=0)
    scrollbar = tk.Scrollbar(body, orient="vertical", command=self.canvas_canvas.yview)
    self.canvas_cards = tk.Frame(self.canvas_canvas, bg=colors["panel"])
    self.canvas_cards.bind(
        "<Configure>",
        lambda _e: self.canvas_canvas.configure(
            scrollregion=self.canvas_canvas.bbox("all")
        ),
    )
    self.canvas_canvas.create_window((0, 0), window=self.canvas_cards, anchor="nw")
    self.canvas_canvas.configure(yscrollcommand=scrollbar.set)
    self.canvas_canvas.pack(side="left", fill="both", expand=True, pady=pad["widget"])
    scrollbar.pack(side="right", fill="y", pady=pad["widget"])

    self.canvas_container.grid_remove()


# --- Input Area ---
def _build_input_area(self) -> None:
    pad = STYLE["spacing"]
    colors = STYLE["colors"]
    fonts = STYLE["fonts"]

    parent = getattr(self, "main_container", self.root)
    parent.grid_rowconfigure(3, weight=0)

    self.input_frame = tk.Frame(parent, bg=colors["background"])
    self.input_frame.grid(
        row=3, column=0, sticky="ew", padx=pad["outer"], pady=(0, pad["outer"])
    )
    self.input_frame.grid_columnconfigure(0, weight=1)

    entry_frame = RoundedFrame(
        self.input_frame, bg=colors["panel"], radius=STYLE.get("radius", 8)
    )
    entry_body = tk.Frame(entry_frame, bg=colors["panel"])
    entry_body.pack(fill="both", expand=True)

    self.entry = tk.Text(
        entry_body,
        height=3,
        wrap="word",
        bg=colors["panel"],
        fg=colors["text_primary"],
        insertbackground=colors["text_primary"],
        relief="flat",
        bd=0,
        highlightthickness=0,
        font=fonts["body"],
        padx=pad["inner"],
        pady=pad["inner"],
    )
    self.entry.pack(fill="x", padx=2, pady=2)
    self._attach_context_menu(self.entry)

    entry_frame.grid(row=0, column=0, sticky="nsew")

    self.send_button = RoundedButton(
        self.input_frame,
        text="Send ⮞",
        command=self._submit_message,
        bg=colors["accent"],
        fg=colors["accent_fg"],
        font=fonts["button"],
    )
    self.send_button.grid(row=0, column=1, padx=(pad["inner"], 0), sticky="s", pady=5)


# --- UI Helpers ---
def _toggle_canvas(self) -> None:
    visible = getattr(self, "canvas_visible", False)
    if visible:
        self.hpanes.forget(self.canvas_container)
        self.canvas_visible = False
    else:
        self.hpanes.add(self.canvas_container, minsize=340, stretch="always")
        self.canvas_visible = True
    if hasattr(self, "_rebalance_panes"):
        self._rebalance_panes()


def _ensure_canvas_visible(self) -> None:
    if not getattr(self, "canvas_visible", False):
        self._toggle_canvas()


def _ui_stop_generation(self) -> None:
    if not getattr(self, "_ui_ready", False):
        return

    self._bubble("assistant", "[stop] generation requested")


def _toggle_params_panel(self) -> None:
    if not getattr(self, "_ui_ready", False):
        return

    is_open = getattr(self, "_params_open", False)
    if is_open:
        self.params_frame.grid_remove()
        self._params_open = False
    else:
        self.params_frame.grid()
        self._params_open = True


def _build_params_panel(self, parent) -> None:
    pad = STYLE["spacing"]
    colors = STYLE["colors"]
    fonts = STYLE["fonts"]

    self.temp_var = tk.DoubleVar(value=0.7)
    self.topp_var = tk.DoubleVar(value=0.9)
    self.topk_var = tk.IntVar(value=40)
    self.rep_var = tk.DoubleVar(value=1.1)
    self.max_tokens_var = tk.IntVar(value=256)

    def add_slider(label, var, frm, to, resolution):
        row = tk.Frame(parent, bg=colors["panel"])
        row.pack(fill="x", padx=pad["inner"], pady=4)
        tk.Label(
            row,
            text=label,
            bg=colors["panel"],
            fg=colors["text_secondary"],
            font=fonts["body"],
        ).pack(side="left")
        tk.Scale(
            row,
            from_=frm,
            to=to,
            orient="horizontal",
            variable=var,
            showvalue=True,
            length=260,
            resolution=resolution,
            bg=colors["panel"],
            highlightthickness=0,
            fg=colors["text_primary"],
            troughcolor=colors["border"],
        ).pack(side="right")

    add_slider("Temperature", self.temp_var, 0.0, 2.0, 0.01)
    add_slider("Top-p", self.topp_var, 0.0, 1.0, 0.01)
    add_slider("Top-k", self.topk_var, 0, 200, 1)
    add_slider("Repetition", self.rep_var, 0.8, 2.0, 0.01)
    add_slider("Max tokens", self.max_tokens_var, 32, 4096, 32)


def _clear_canvas(self) -> None:
    # This loop destroys each widget currently on the canvas
    for child in self.canvas_cards.winfo_children():
        child.destroy()  # This line was likely missing and needs to be indented

    # This line also needs to be indented to be part of the function
    self.canvas_canvas.configure(scrollregion=self.canvas_canvas.bbox("all"))


# --- Messaging ---
def _submit_message(self) -> None:
    if not getattr(self, "_ui_ready", False):
        return

    text = self.entry.get("1.0", "end").strip()
    if not text:
        return
    self.entry.delete("1.0", "end")
    self._bubble("user", text)
    if self.submit_callback:
        threading.Thread(target=self.submit_callback, args=(text,), daemon=True).start()


def _on_send_shortcut(self) -> None:
    self._submit_message()


def _handle_return(self, event):
    SHIFT_MASK = 0x0001
    if event.state & SHIFT_MASK:
        return None
    self._submit_message()
    return "break"


def _entry_select_all(self) -> None:
    self.entry.tag_add("sel", "1.0", "end-1c")
    self.entry.focus_set()


def _render_response(self, response: str) -> None:
    response = response or "(no content returned)"
    segments = self._extract_segments(response)
    showed_text = False
    for kind, payload in segments:
        if kind == "text":
            fragment = payload.strip()
            if fragment:
                self._bubble("assistant", fragment)
                showed_text = True
        else:
            lang, code = payload
            self._add_card(lang, code)
    if not showed_text and any(kind == "code" for kind, _ in segments):
        self._bubble("assistant", "(code copied to Canvas)")


def _add_card(self, lang: str, code: str) -> None:
    pad = STYLE["spacing"]
    colors = STYLE["colors"]
    fonts = STYLE["fonts"]

    self._ensure_canvas_visible()
    card = RoundedFrame(
        self.canvas_cards,
        bg=colors["panel_light"],
        bordercolor=colors["border"],
        borderwidth=1,
    )
    card_body = tk.Frame(card, bg=colors["panel_light"])
    card_body.pack(fill="both", expand=True)

    header = tk.Frame(card_body, bg=colors["panel_light"])
    header.pack(fill="x", padx=pad["widget"], pady=pad["widget"])
    tk.Label(
        header,
        text=lang,
        bg=colors["panel_light"],
        fg=colors["text_secondary"],
        font=fonts["subtitle"],
    ).pack(side="left", padx=pad["inner"])

    copy_button = RoundedButton(
        header,
        text="Copy",
        command=lambda c=code: self._copy_to_clipboard(c),
        bg=colors["accent"],
        fg=colors["accent_fg"],
        font=fonts["button"],
        padx=10,
        pady=2,
    )
    copy_button.pack(side="right")

    text_widget = tk.Text(
        card_body,
        wrap="none",
        bg=colors["panel_light"],
        fg=colors["text_primary"],
        insertbackground=colors["text_primary"],
        relief="flat",
        bd=0,
        height=10,
        font=fonts["code"],
    )
    text_widget.insert("1.0", code.rstrip() + "\n")
    self._make_readonly_text(text_widget)
    text_widget.pack(
        fill="both", expand=True, padx=pad["inner"], pady=(0, pad["inner"])
    )
    self._attach_context_menu(text_widget, read_only=True)

    card.pack(fill="x", padx=pad["inner"], pady=pad["inner"])
    self.canvas_canvas.update_idletasks()
    self.canvas_canvas.configure(scrollregion=self.canvas_canvas.bbox("all"))


def _on_copy_code(self, msg_id: int) -> None:
    record = self._messages.get(msg_id)
    if record:
        code_blocks = extract_code_blocks(record.get("text", ""))
        if code_blocks:
            self._copy_to_clipboard("\n\n".join(code_blocks))


# --- Scrolling ---
def _chat_yscroll(self, first: str, last: str):
    try:
        self._scrollbar_set(first, last)
    except Exception:
        pass
    self._update_scroll_button()


def _update_scroll_button(self) -> None:
    if not hasattr(self, "_jump_btn"):
        return
    try:
        _, last = self.chat_canvas.yview()
        if last < 0.995:
            self._jump_btn.place_configure(
                relx=1.0, rely=1.0, x=-12, y=-12, anchor="se"
            )
        else:
            self._jump_btn.place_forget()
    except Exception:
        pass


def _scroll_to_bottom(self) -> None:
    try:
        self.chat_canvas.yview_moveto(1.0)
    finally:
        self._update_scroll_button()
