# src/ui/app_ctk.py — Adam Desktop (CustomTkinter) — visual parity with server UI
# Layout: [Sidebar 240px] | [Header, Messages, Composer]
# Safe: standalone; does not modify existing app.py or components.

import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
import re
import tkinter.font as tkfont
from datetime import datetime

# ---------- Web CSS–style tokens ----------
CSS = {
    "bg": "#0f172a", "bg_elev": "#111c34", "bg_muted": "#15213d",
    "text": "#e2e8f0", "text_muted": "#94a3b8",
    "accent": "#38bdf8", "accent_fg": "#ffffff",
    "border": "#242d40",
    "bubble_user_bg": "#0b2a42", "bubble_user_fg": "#e2f3ff",
    "bubble_assist_bg": "#222230", "bubble_assist_fg": "#e6e6f0",
    "status_ok": "#10b981", "status_warn": "#f59e0b",
    "status_error": "#ef4444", "status_idle": "#94a3b8",
}

# Sidebar responsiveness (min/max + ratio of window width)
SIDEBAR_MIN_W = 200
SIDEBAR_MAX_W = 360
SIDEBAR_RATIO = 0.22  # ~22% of window width

# ---------- Theme apply ----------
def apply_theme(root):
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    try: root.configure(bg=CSS["bg"])
    except Exception: pass
    # tk option db so classic widgets match
    opt = root.option_add
    opt("*Font", "Inter 13")
    opt("*Label.background", CSS["bg"])
    opt("*Label.foreground", CSS["text"])
    opt("*Frame.background", CSS["bg"])
    opt("*Button.background", CSS["bg_elev"])
    opt("*Button.foreground", CSS["text"])
    opt("*Entry.background", CSS["bg_elev"])
    opt("*Entry.foreground", CSS["text"])
    opt("*Entry.insertBackground", CSS["text"])
    opt("*Listbox.background", CSS["bg_elev"])
    opt("*Listbox.foreground", CSS["text"])
    opt("*Listbox.selectBackground", CSS["bg_muted"])
    opt("*Listbox.selectForeground", CSS["text"])

# ---------- Small UI helpers ----------
def spacer(frame, h=8): tk.Frame(frame, height=h, bg=CSS["bg"]).pack(fill="x")

class StatusHeader(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0)
        self.grid_columnconfigure(1, weight=1)
        self.brand = ctk.CTkLabel(self, text="🤖  Adam",
                                  font=("", 16, "bold"))
        self.brand.grid(row=0, column=0, sticky="w", padx=12, pady=12)
        status = ctk.CTkFrame(self, corner_radius=999)
        status.grid(row=0, column=2, sticky="e", padx=12, pady=12)
        self.dot = ctk.CTkLabel(status, text="●", text_color=CSS["status_idle"])
        self.dot.grid(row=0, column=0, padx=6)
        self.label = ctk.CTkLabel(status, text="Checking…")
        self.label.grid(row=0, column=1, padx=6)
    def set_status(self, mode="idle", text=None):
        color = CSS.get(f"status_{mode}", CSS["status_idle"])
        self.dot.configure(text_color=color)
        if text is not None: self.label.configure(text=text)

class MessageStream(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=48)
        self._wrap = 860  # default; updated by app._on_resize
        # Monospace for code blocks (falls back safely if font missing)
        self._mono = tkfont.Font(family="Courier New", size=12)
        # Regex to capture ```lang\n...``` fenced blocks
        self._code_re = re.compile(r"```([a-zA-Z0-9_+-]*)\n(.*?)\n```", re.DOTALL)

    def _softwrap(self, s: str, limit: int = 30) -> str:
        """Insert zero-width spaces into long unbroken chunks to allow wrapping."""
        out, cur = [], []
        for ch in s:
            cur.append(ch)
            if len(cur) >= limit and ch not in (" ", "\n", "\t"):
                cur.append("\u200b")
                out.append("".join(cur))
                cur = []
        out.append("".join(cur))
        return "".join(out)

    def add(self, role, content):
        content = self._softwrap(content or "")
        wrap = ctk.CTkFrame(self, corner_radius=20)
        wrap.pack(fill="x", padx=8, pady=6, anchor="w")
        row = ctk.CTkFrame(wrap, fg_color="transparent")
        row.pack(fill="x")
        is_user = role == "user"
        bg = CSS["bubble_user_bg"] if is_user else CSS["bubble_assist_bg"]
        fg = CSS["bubble_user_fg"] if is_user else CSS["bubble_assist_fg"]
        side = "right" if is_user else "left"
        bubble = ctk.CTkFrame(row, corner_radius=44, fg_color=bg)
        bubble.pack(side=side, padx=8, pady=2)
        for kind, lang, body in self._parse_segments(content):
            if kind == "code":
                self._render_code(bubble, body, lang=lang)
            else:
                self._render_text(bubble, fg, body)

    def set_wrap(self, wrap_len: int):
        """Update wraplength on existing and future messages."""
        self._wrap = max(260, int(wrap_len))
        try:
            for child in self.winfo_children():
                for row in child.winfo_children():
                    for bubble in row.winfo_children():
                        for lbl in bubble.winfo_children():
                            try:
                                lbl.configure(wraplength=self._wrap)
                            except Exception:
                                pass
        except Exception:
            pass

    def _parse_segments(self, text: str):
        """
        Yields tuples: ("code", lang, body) or ("text", "", body)
        Recognizes fenced blocks: ```lang\n...\n```
        """
        if not text:
            return [("text", "", "")]
        segs = []
        pos = 0
        for m in self._code_re.finditer(text):
            start, end = m.span()
            if start > pos:
                segs.append(("text", "", text[pos:start]))
            segs.append(("code", (m.group(1) or "").strip(), m.group(2)))
            pos = end
        if pos < len(text):
            segs.append(("text", "", text[pos:]))
        return segs

    def _render_text(self, parent, fg, content):
        # Normal paragraph bubble
        lbl = ctk.CTkLabel(parent, text=content, justify="left",
                           text_color=fg, anchor="w", wraplength=self._wrap)
        lbl.pack(padx=10, pady=10)

    def _render_code(self, parent, content, lang=""):
        # Rounded code container with horizontal scroll
        block = ctk.CTkFrame(parent, corner_radius=16, fg_color=CSS["bg_muted"])
        block.pack(fill="x", padx=10, pady=8)
        if lang:
            ctk.CTkLabel(block, text=lang, text_color=CSS["text_muted"]).pack(anchor="ne", padx=8, pady=(8,0))
        wrap = tk.Frame(block, bg=CSS["bg_muted"])
        wrap.pack(fill="x", expand=True, padx=8, pady=8)
        xscroll = tk.Scrollbar(wrap, orient="horizontal")
        xscroll.pack(side="bottom", fill="x")
        t = tk.Text(
            wrap,
            height=8,
            wrap="none",
            font=self._mono,
            bg=CSS["bg_muted"],
            fg=CSS["text"],
            relief="flat",
            highlightthickness=0,
            insertbackground=CSS["text"],
        )
        t.pack(fill="both", expand=True)
        try:
            self.winfo_toplevel()._attach_context_menu(t)
        except Exception:
            pass
        t.insert("1.0", content.rstrip("\n"))
        t.configure(state="disabled")
        t.configure(xscrollcommand=xscroll.set)
        xscroll.configure(command=t.xview)

class TypingIndicator(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=40)
        self._shown = False
        self._lbl = ctk.CTkLabel(self, text="Assistant is thinking…  ● ● ●")
        self._lbl.pack(padx=8, pady=8)
    def show(self, on=True):
        if on and not self._shown:
            self.grid()
            self._shown = True
        elif not on and self._shown:
            self.grid_remove()
            self._shown = False

class Composer(ctk.CTkFrame):
    def __init__(self, master, on_send, on_canvas):
        super().__init__(master, corner_radius=48)
        self.on_send = on_send; self.on_canvas = on_canvas
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self._target_width = 1200
        bar = ctk.CTkFrame(self, corner_radius=56, fg_color=CSS["bg_elev"])
        bar.grid(row=0, column=1, sticky="ew", padx=8, pady=8)
        self._bar = bar
        bar.grid_columnconfigure(0, weight=1)
        self.base_lines = 4
        self.max_lines = 8
        bar.grid_columnconfigure(0, weight=1)
        bar.grid_columnconfigure(1, weight=0)
        self.input = tk.Text(
            bar,
            height=self.base_lines,
            wrap="char",
            bg=CSS["bg_elev"],
            fg=CSS["text"],
            insertbackground=CSS["text"],
            relief="flat",
            highlightthickness=0,
            padx=8,
            pady=8,
        )
        self.input.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 6))
        self.input_scroll = ctk.CTkScrollbar(bar, orientation="vertical", command=self.input.yview)
        self.input_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=(10, 6))
        self.input_scroll.grid_remove()
        self.input.configure(yscrollcommand=self.input_scroll.set)
        self._enforce_word_wrap()
        try:
            self.winfo_toplevel()._attach_context_menu(self.input)
        except Exception:
            pass
        self.input.bind("<Return>", self._handle_return)
        self.input.bind("<Shift-Return>", lambda e: None)
        self.input.bind("<Control-Return>", self._handle_return)
        self.input.bind("<Command-Return>", self._handle_return)
        self.input.bind("<KeyRelease>", self._resize_text_height, add="+")
        init_height = int(self.input.cget("height"))
        self._line_height = max(1, init_height // self.base_lines)
        tools = ctk.CTkFrame(bar, corner_radius=28, fg_color="transparent")
        tools.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 10))
        tools.grid_columnconfigure(0, weight=1)
        self.actions = ctk.CTkFrame(tools, fg_color="transparent")
        self.actions.grid(row=0, column=0, sticky="w")
        self._act_btns = []
        for txt in ("📎","🖼️","🎤"):
            b = ctk.CTkButton(self.actions, text=txt, width=34, height=34, corner_radius=24)
            b.pack(side="left", padx=4, pady=4)
            self._act_btns.append(b)
        self.more = ctk.CTkButton(
            self.actions,
            text="⋯",
            width=40,
            height=34,
            corner_radius=24,
            command=self._show_overflow,
        )
        self.more.pack(side="left", padx=4, pady=4)
        self.more.pack_forget()
        right = ctk.CTkFrame(tools, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e")
        self.canvas_btn = ctk.CTkButton(
            right,
            text="🗖",
            width=44,
            height=38,
            corner_radius=28,
            command=lambda: self.on_canvas(),
        )
        self.canvas_btn.pack(side="left", padx=4)
        self.btn = ctk.CTkButton(
            right,
            text="✈️",
            width=52,
            height=40,
            corner_radius=28,
            fg_color=CSS["accent"],
            text_color=CSS["accent_fg"],
            command=self._send,
        )
        self.btn.pack(side="left", padx=4)

    def set_compact(self, compact: bool):
        """Show ⋯ instead of the three left action buttons when compact."""
        if compact:
            for b in self._act_btns:
                try:
                    b.pack_forget()
                except Exception:
                    pass
            try:
                self.more.pack(side="left", padx=4, pady=4)
            except Exception:
                pass
        else:
            try:
                self.more.pack_forget()
            except Exception:
                pass
            for b in self._act_btns:
                try:
                    b.pack(side="left", padx=4, pady=4)
                except Exception:
                    pass

    def _show_overflow(self):
        # simple popup with the three actions (placeholder commands)
        m = tk.Menu(self, tearoff=0)
        for label in ("Attach file…", "Insert image…", "Voice input…"):
            m.add_command(label=label, command=lambda L=label: None)
        x = self.more.winfo_rootx()
        y = self.more.winfo_rooty() + self.more.winfo_height()
        try:
            m.tk_popup(x, y)
        finally:
            m.grab_release()

    def set_width(self, w: int):
        """Limit the visual width and keep the box centered."""
        try:
            avail = max(480, int(w) - 16)
            self._target_width = avail
            self.grid_columnconfigure(1, minsize=self._target_width)
            if hasattr(self, "_bar"):
                try:
                    self._bar.grid_propagate(False)
                    self._bar.configure(width=self._target_width)
                except Exception:
                    pass
        except Exception:
            pass
        self._enforce_word_wrap()

    def _enforce_word_wrap(self):
        """Ensure the input keeps character wrapping and no horizontal scroll."""
        try:
            self.input.configure(wrap="char", xscrollcommand="")
        except Exception:
            pass

    def _resize_text_height(self, _event=None):
        try:
            total_lines = int(self.input.index("end-1c").split(".")[0])
        except Exception:
            total_lines = self.base_lines
        lines = max(self.base_lines, min(self.max_lines, total_lines))
        try:
            current = int(self.input.cget("height"))
        except Exception:
            current = lines
        if lines and lines != current:
            self.input.configure(height=lines)
        if total_lines > self.max_lines:
            try:
                self.input_scroll.grid()
            except Exception:
                pass
            try:
                self.input.see("insert")
            except Exception:
                pass
        else:
            try:
                self.input_scroll.grid_remove()
            except Exception:
                pass
    def _handle_return(self, e):
        if (e.state & 0x0001):  # Shift
            return
        self._send(); return "break"

    def _send(self):
        text = self.input.get("1.0","end").strip()
        if not text: return
        self.on_send(text)
        self.input.delete("1.0","end")

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_new_chat, on_open_settings, on_select_chat):
        super().__init__(master, corner_radius=48, fg_color=CSS["bg_elev"])
        # header
        head = ctk.CTkFrame(self, corner_radius=40)
        head.pack(fill="x", padx=6, pady=6)
        ctk.CTkLabel(head, text="🧠 Mako-AI", font=("",16,"bold")).pack(side="left", padx=6, pady=6)
        self.collapse_btn = ctk.CTkButton(
            head,
            text="−",
            width=36,
            height=36,
            corner_radius=24,
            command=lambda: self.winfo_toplevel()._toggle_sidebar(),
        )
        self.collapse_btn.pack(side="right", padx=6, pady=6)
        # new chat
        ctk.CTkButton(self, text="➕ New Chat", command=on_new_chat, corner_radius=36)\
            .pack(fill="x", padx=6, pady=6)
        # search
        sr = ctk.CTkFrame(self, corner_radius=40)
        sr.pack(fill="x", padx=6, pady=6)
        self.search = ctk.CTkEntry(sr, placeholder_text="Search chats")
        self.search.pack(fill="x", padx=8, pady=8)
        try:
            self.winfo_toplevel()._attach_context_menu(self.search)
        except Exception:
            pass
        # chats list (rounded via CTk buttons in a scroll frame)
        self.list_frame = ctk.CTkScrollableFrame(
            self, corner_radius=20, fg_color=CSS["bg_elev"]
        )
        self.list_frame.pack(fill="both", expand=True, padx=6, pady=6)
        self._items = []
        self._item_buttons = []
        self._on_select_chat = on_select_chat
        self._titles = []
        # footer
        ft = ctk.CTkFrame(self, corner_radius=40)
        ft.pack(fill="x", padx=6, pady=6)
        ctk.CTkButton(ft, text="👤 Settings", command=on_open_settings, corner_radius=12)\
            .pack(fill="x", padx=6, pady=6)
    def selected_id(self):
        return None
    def set_items(self, titles):
        for b in self._items:
            try:
                b.destroy()
            except Exception:
                pass
        self._items.clear()
        self._titles = list(titles or [])
        self._item_buttons = []
        for idx, t in enumerate(self._titles):
            row = ctk.CTkFrame(self.list_frame, corner_radius=36, fg_color="transparent")
            row.pack(fill="x", padx=6, pady=4)
            btn = ctk.CTkButton(
                row,
                text=t,
                corner_radius=48,
                fg_color=CSS["bg_muted"],
                hover_color=CSS["bg_elev"],
                text_color=CSS["text"],
                anchor="w",
                command=lambda i=idx: self._on_select_chat(i),
            )
            btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
            kabob = ctk.CTkButton(
                row,
                text="⋮",
                width=34,
                height=34,
                corner_radius=24,
                command=lambda i=idx: self._open_chat_menu(i),
            )
            kabob.pack(side="right")
            self._items.append(row)
            self._item_buttons.append(btn)

    def prepend_item(self, title):
        self.set_items([title, *self._titles])

    def set_compact(self, compact: bool):
        """When compact, show generic 'Chat…' text to save width."""
        self._compact = bool(compact)
        if not hasattr(self, "_item_buttons"):
            return
        for i, btn in enumerate(self._item_buttons):
            full = self._titles[i] if i < len(self._titles) else ""
            btn.configure(text=("Chat…" if self._compact else full))

    def _open_chat_menu(self, idx: int):
        m = tk.Menu(self, tearoff=0)
        m.add_command(label="Rename", command=lambda i=idx: self._rename_chat(i))
        m.add_command(label="Delete", command=lambda i=idx: self._delete_chat(i))
        sub = tk.Menu(m, tearoff=0)
        sub.add_command(label="(Set up projects…)", command=lambda: None)
        m.add_cascade(label="Move to", menu=sub)
        try:
            m.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            m.grab_release()

    def _rename_chat(self, idx: int):
        new = None
        try:
            dlg = ctk.CTkInputDialog(text="New chat name:", title="Rename chat")
            new = dlg.get_input()
        except Exception:
            pass
        if new:
            self._titles[idx] = new
            self.set_items(self._titles)

    def _delete_chat(self, idx: int):
        if 0 <= idx < len(self._titles):
            del self._titles[idx]
            self.set_items(self._titles)

class ModelPicker(ctk.CTkFrame):
    def __init__(self, master, on_change):
        super().__init__(master, corner_radius=12, fg_color="transparent")
        ctk.CTkLabel(self, text="Model:", text_color=CSS["text_muted"]).pack(side="left", padx=6)
        self.var = tk.StringVar(self)
        self.menu = ctk.CTkOptionMenu(
            self,
            variable=self.var,
            values=[],
            corner_radius=48,
            fg_color=CSS["bg_elev"],
            button_color=CSS["bg_muted"],
            text_color=CSS["text"],
        )
        self.menu.pack(side="left", padx=6)
        self.on_change = on_change
    def set_options(self, options, current=None):
        values = options or ["No models"]
        self.menu.configure(values=values)
        if options:
            val = current if current in options else options[0]
        else:
            val = "No models"
        self.var.set(val)
        self.menu.set(val)
        self.on_change(val)
    def _set(self, v):
        self.var.set(v)
        self.menu.set(v)
        self.on_change(v)

class AdamCTK(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Desktop UI (CTk)")
        self.geometry("2400x1600")
        self.minsize(980, 620)
        apply_theme(self)
        # log full Tk callback errors to a file (so we see real tracebacks)
        def _tk_err_logger(exc, val, tb):
            try:
                import traceback, datetime as _dt
                with open("tk_errors.log", "a", buffering=1) as fp:
                    print(f"\n=== Tk callback @ {_dt.datetime.now().isoformat()} ===", file=fp)
                    traceback.print_exception(exc, val, tb, file=fp)
            except Exception:
                pass
        self.report_callback_exception = _tk_err_logger
        # resize debounce state
        self._resize_job = None
        self._last_scale = 1.0
        self._sidebar_w = None
        self._compact_mode = None
        self._pending_w = 1200
        # split view with draggable sash
        self.panes = tk.PanedWindow(
            self,
            orient="horizontal",
            sashwidth=8,
            bg=CSS["bg"],
            borderwidth=0,
        )
        self.panes.pack(fill="both", expand=True)
        # sidebar (left)
        self.sidebar = Sidebar(self.panes, self._new_chat, self._open_settings, self._select_chat)
        # main content (right)
        self.main = ctk.CTkFrame(self.panes, corner_radius=0)
        main = self.main
        # add panes with a minimum sidebar width to keep controls visible
        self.panes.add(self.sidebar, minsize=SIDEBAR_MIN_W)
        self.panes.add(main)
        self.sidebar_stub = ctk.CTkFrame(self.panes, corner_radius=0)
        self.stub_btn = ctk.CTkButton(
            self.sidebar_stub,
            text="+",
            width=36,
            height=36,
            corner_radius=24,
            command=self._toggle_sidebar,
        )
        self.stub_btn.pack(padx=6, pady=6)
        self._sidebar_hidden = False
        # --- settle initial layout before listening to <Configure> ---
        self._ready = False
        self.update_idletasks()
        try:
            _w = max(self.winfo_width(), 1)
        except Exception:
            _w = 1200
        self._last_scale = round(min(1.30, max(0.90, _w / 1200)), 2)
        desired_sidebar = int(max(SIDEBAR_MIN_W, min(SIDEBAR_MAX_W, _w * SIDEBAR_RATIO)))
        try:
            self.panes.sash_place(0, desired_sidebar, 0)
        except Exception:
            pass
        try:
            self.update_idletasks()
            self._sidebar_w = max(self.sidebar.winfo_width(), SIDEBAR_MIN_W)
        except Exception:
            self._sidebar_w = desired_sidebar
        try:
            avail = max(_w - self._sidebar_w - 48, 320)
            self.stream.set_wrap(int(avail * 0.9))
            try:
                self.composer.set_width(int(avail))
            except Exception:
                pass
            self.composer.set_compact(_w < 960)
        except Exception:
            pass
        self.after(
            200,
            lambda: (
                setattr(self, "_ready", True),
                self.bind("<Configure>", self._on_resize, add="+"),
            ),
        )
        main.grid_rowconfigure(2, weight=1)
        main.grid_columnconfigure(0, weight=1)
        # header
        topbar = ctk.CTkFrame(main, corner_radius=0)
        topbar.grid(row=0, column=0, sticky="ew")
        self.header = StatusHeader(topbar)
        self.header.pack(fill="x")
        # model picker row
        tools = ctk.CTkFrame(main, corner_radius=12, fg_color="transparent")
        tools.grid(row=1, column=0, sticky="ew", padx=12, pady=(6,0))
        self.model = ModelPicker(tools, on_change=self._set_model)
        self.model.pack(side="left")
        # messages
        self.stream = MessageStream(main)
        self.stream.grid(row=2, column=0, sticky="nsew", padx=12, pady=12)
        # typing indicator (hidden by default)
        self.typing = TypingIndicator(main)
        self.typing.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 6))
        self.typing.grid_remove()
        # composer
        self.composer = Composer(main, on_send=self._send, on_canvas=self._toggle_canvas)
        self.composer.grid(row=4, column=0, sticky="ew", padx=12, pady=12)
        # seed demo
        self._seed()
        # ----- callbacks -----
    def _seed(self):
        self.sidebar.set_items(["Welcome", "Design Review", "Bug triage"])
        self.model.set_options(["gpt-neon-small", "mistral:7b", "llama3.1:8b"], current="mistral:7b")
        self.stream.add("assistant", "Welcome.")
        self.stream.add("user", "Mirror the server UI.")
        self.header.set_status("ok", "Online")
    def _new_chat(self):
        self.sidebar.prepend_item(
            f"New chat — {datetime.now().strftime('%H:%M:%S')}"
        )
    def _open_settings(self):
        top = ctk.CTkToplevel(self); top.title("Settings"); spacer(top,6)
        ctk.CTkLabel(top, text="Appearance only dialog (placeholder)").pack(padx=12, pady=12)

    def _toggle_sidebar(self):
        """Hide/show the sidebar pane; remembers last width."""
        try:
            if getattr(self, "_sidebar_hidden", False):
                try:
                    self.panes.forget(self.sidebar_stub)
                except Exception:
                    pass
                self.panes.add(self.sidebar, before=self.main, minsize=SIDEBAR_MIN_W)
                if hasattr(self, "_saved_sidebar_w"):
                    try:
                        self.panes.sashpos(0, max(SIDEBAR_MIN_W, int(self._saved_sidebar_w)))
                    except Exception:
                        pass
                self._sidebar_hidden = False
            else:
                self._saved_sidebar_w = self.sidebar.winfo_width()
                try:
                    self.panes.forget(self.sidebar)
                except Exception:
                    pass
                self.panes.add(self.sidebar_stub, before=self.main, minsize=36)
                self._sidebar_hidden = True
            try:
                if hasattr(self, "sidebar") and hasattr(self.sidebar, "collapse_btn"):
                    self.sidebar.collapse_btn.configure(text=("+" if self._sidebar_hidden else "−"))
                if hasattr(self, "stub_btn"):
                    self.stub_btn.configure(text="+")
            except Exception:
                pass
            self._on_resize()
        except Exception:
            pass

    def _attach_context_menu(self, widget):
        """Adds Cut/Copy/Paste/Select All to Text/Entry/CTkTextbox (and inner tk.Text)."""
        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label="Cut",        command=lambda: widget.event_generate("<<Cut>>"))
        menu.add_command(label="Copy",       command=lambda: widget.event_generate("<<Copy>>"))
        menu.add_command(label="Paste",      command=lambda: widget.event_generate("<<Paste>>"))
        menu.add_separator()
        def _select_all():
            try:
                widget.event_generate("<<SelectAll>>")
            except Exception:
                try:
                    if isinstance(widget, tk.Text) or getattr(widget, "tag_ranges", None):
                        widget.tag_add("sel", "1.0", "end-1c")
                    else:
                        widget.selection_range(0, "end")
                except Exception:
                    pass
        menu.add_command(label="Select All", command=_select_all)
        def _popup(e):
            try:
                menu.tk_popup(e.x_root, e.y_root)
            finally:
                menu.grab_release()
        widget.bind("<Button-3>", _popup, add="+")
        widget.bind("<Button-2>", _popup, add="+")
        try:
            inner = getattr(widget, "_textbox", None)
            if inner is not None:
                self._attach_context_menu(inner)
        except Exception:
            pass

    def _toggle_canvas(self):
        # Create once; reuse on subsequent clicks
        if (
            not hasattr(self, "canvas_win")
            or self.canvas_win is None
            or not self.canvas_win.winfo_exists()
        ):
            win = ctk.CTkToplevel(self)
            win.title("Canvas")
            win.geometry("720x520")
            spacer(win, 6)
            hold = ctk.CTkFrame(win, corner_radius=24, fg_color=CSS["bg_elev"])
            hold.pack(fill="both", expand=True, padx=12, pady=12)
            # placeholder canvas area for future enhancements
            self.canvas_area = tk.Canvas(
                hold, bg=CSS["bg_muted"], highlightthickness=0
            )
            self.canvas_area.pack(fill="both", expand=True, padx=12, pady=12)
            self.canvas_win = win
        else:
            self.canvas_win.deiconify()
        self.canvas_win.lift()
        self.canvas_win.focus_force()
    def _select_chat(self, idx):
        if idx is None: return
        self.stream.add("assistant", f"Opened chat #{idx}")
    def _set_model(self, name):
        self.stream.add("assistant", f"Model set: {name}")
    def _on_resize(self, _e=None):
        if not getattr(self, "_ready", False):
            return
        try:
            if self._resize_job:
                self.after_cancel(self._resize_job)
        except Exception:
            pass
        try:
            self._pending_w = max(self.winfo_width(), 1)
        except Exception:
            self._pending_w = 1200
        self._resize_job = self.after(60, self._do_resize)

    def _do_resize(self):
        self._resize_job = None
        w = int(getattr(self, "_pending_w", 1200))
        sidebar_width = self._sidebar_w or SIDEBAR_MIN_W
        try:
            if hasattr(self, "sidebar") and self.sidebar.winfo_exists():
                sidebar_width = max(self.sidebar.winfo_width(), SIDEBAR_MIN_W)
        except Exception:
            pass
        self._sidebar_w = sidebar_width
        try:
            target = min(1.30, max(0.90, w / 1280))
            last = getattr(self, "_last_scale", 1.0)
            new = last + (target - last) * 0.35
            new = round(new, 2)
            if abs(new - last) >= 0.01:
                ctk.set_widget_scaling(new)
                self._last_scale = new
        except Exception:
            pass
        try:
            avail = max(w - sidebar_width - 48, 320)
            new_wrap = int(avail * 0.9)
            if hasattr(self, "stream"):
                self.stream.set_wrap(new_wrap)
            if hasattr(self, "composer") and hasattr(self.composer, "set_width"):
                try:
                    self.composer.set_width(int(avail))
                except Exception:
                    pass
            if hasattr(self, "sidebar") and hasattr(self.sidebar, "set_compact"):
                self.sidebar.set_compact(w < 1100)
        except Exception:
            pass
        try:
            if hasattr(self, "composer"):
                prev = self._compact_mode
                now = prev
                if prev is None:
                    now = (w < 960)
                else:
                    if prev and w > 1040:
                        now = False
                    if (prev is False) and w < 960:
                        now = True
                if now is not None and now != prev:
                    self.composer.set_compact(now)
                    self._compact_mode = now
        except Exception:
            pass
    def _send(self, text):
        self.stream.add("user", text); self.typing.show(True)
        self.after(500, lambda: (self.typing.show(False), self.stream.add("assistant","(Thinking)")))


if __name__ == "__main__":
    app = AdamCTK()
    app.mainloop()
