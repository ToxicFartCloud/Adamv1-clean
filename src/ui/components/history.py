# src/ui/components/history.py
"""
Chat and project history management.
Handles creation, selection, persistence, and state synchronization.
"""

from __future__ import annotations
import json
from types import MethodType
from typing import Any, Dict
from tkinter import filedialog, messagebox
from pathlib import Path

from ..state import ui_state
from ..utils.paths import get_data_dir


# ────────────────────────────────
# Persistence
# ────────────────────────────────


def _get_state_file_path() -> Path:
    """Get path to the main application state file."""
    return get_data_dir() / "state.json"


def _load_state_from_disk() -> Dict[str, Any]:
    """Load full UI state from disk."""
    state_file = _get_state_file_path()
    if not state_file.exists():
        return {}
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _save_chats(self) -> None:
    """Save current UI state to disk."""
    _save_state_to_disk()


def _save_state_to_disk() -> None:
    """Persist current ui_state to disk."""
    state_file = _get_state_file_path()
    try:
        payload = {
            "projects": ui_state.get("projects", []),
            "chats": ui_state.get("chats", []),
            "active_project_id": ui_state.get("active_project_id"),
            "active_chat_id": ui_state.get("active_chat_id"),
            "chat_messages": ui_state.get("chat_messages", {}),
            "preferences": ui_state.get("preferences", {}),
            "next_chat_id": ui_state.get("next_chat_id"),
        }
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except OSError:
        pass  # Fail silently in UI


def _ensure_next_chat_id() -> None:
    chats = ui_state.get("chats", [])
    max_existing = max((c.get("id", 0) for c in chats), default=0)
    candidate = ui_state.get("next_chat_id")
    if not isinstance(candidate, int) or candidate <= max_existing:
        disk_next = ui_state.get("_disk_next_chat_id")
        if isinstance(disk_next, int) and disk_next > max_existing:
            candidate = disk_next
        else:
            candidate = max_existing + 1
    if candidate <= 0:
        candidate = max_existing + 1 if max_existing else 1
    ui_state["next_chat_id"] = candidate


def _allocate_chat_id() -> int:
    _ensure_next_chat_id()
    next_id = ui_state.get("next_chat_id", 1)
    chat_id = max(int(next_id), 1)
    ui_state["next_chat_id"] = chat_id + 1
    return chat_id


def _generate_chat_title(chat_id: int) -> str:
    base = f"Chat {chat_id}"
    existing = {c.get("title") for c in ui_state.get("chats", [])}
    if base not in existing:
        return base
    suffix = 2
    while f"{base} ({suffix})" in existing:
        suffix += 1
    return f"{base} ({suffix})"


# ────────────────────────────────
# Project Management
# ────────────────────────────────


def _new_project(self) -> None:
    """Create a new project and switch to it."""
    projects = ui_state.setdefault("projects", [])
    next_id = max((p.get("id", 0) for p in projects), default=0) + 1
    name = f"Project {next_id}"
    projects.append({"id": next_id, "name": name, "chats": []})
    ui_state["active_project_id"] = next_id
    _save_state_to_disk()
    self._populate_project_list()
    self._select_project_in_list(next_id)


def _delete_project(self, project_id: int) -> None:
    """Delete a project and all its chats."""
    projects = ui_state.get("projects", [])
    project = next((p for p in projects if p.get("id") == project_id), None)
    if not project:
        return

    name = project.get("name", f"Project {project_id}")
    confirmed = messagebox.askyesno(
        "Delete Project", f"Delete “{name}” and all its chats? This cannot be undone."
    )
    if not confirmed:
        return

    chat_ids_to_remove = set(project.get("chats", []))
    ui_state["chats"] = [
        chat
        for chat in ui_state.get("chats", [])
        if chat.get("id") not in chat_ids_to_remove
    ]
    ui_state.setdefault("chat_messages", {})
    for cid in chat_ids_to_remove:
        ui_state["chat_messages"].pop(str(cid), None)

    ui_state["projects"] = [p for p in projects if p.get("id") != project_id]

    remaining = ui_state.get("projects", [])
    if remaining:
        ui_state["active_project_id"] = remaining[0]["id"]
    else:
        _new_project(self)

    _save_state_to_disk()
    self._populate_project_list()
    self._populate_chat_list()


def _rename_project(self, project_id: int, new_name: str) -> None:
    """Rename a project."""
    if not new_name.strip():
        return
    for project in ui_state.get("projects", []):
        if project.get("id") == project_id:
            project["name"] = new_name.strip()
            break
    _save_state_to_disk()
    self._populate_project_list()


# ────────────────────────────────
# Chat Management (within active project)
# ────────────────────────────────


def _new_chat(self) -> None:
    """Create a new chat in the active project."""
    chats = ui_state.setdefault("chats", [])
    chat_id = _allocate_chat_id()
    title = _generate_chat_title(chat_id)

    active_pid = ui_state.get("active_project_id")
    if active_pid is not None:
        for project in ui_state.get("projects", []):
            if project.get("id") == active_pid:
                project.setdefault("chats", []).append(chat_id)
                break

    chats.append({"id": chat_id, "title": title})
    ui_state["active_chat_id"] = chat_id
    ui_state.setdefault("chat_messages", {})[str(chat_id)] = []
    _save_state_to_disk()
    self._populate_chat_list()
    self._select_chat_in_list(chat_id)


def _delete_active_chat(self) -> None:
    """Delete the currently active chat."""
    chats = ui_state.get("chats", [])
    if not chats:
        return

    cid = ui_state.get("active_chat_id")
    if cid is None:
        cid = chats[0].get("id")

    chat_title = next(
        (c.get("title") for c in chats if c.get("id") == cid), f"Chat {cid}"
    )
    confirmed = messagebox.askyesno(
        "Delete Chat", f"Delete “{chat_title}”? This cannot be undone."
    )
    if not confirmed:
        return

    for project in ui_state.get("projects", []):
        if cid in project.get("chats", []):
            project["chats"] = [c for c in project["chats"] if c != cid]
            break

    ui_state["chats"] = [c for c in chats if c.get("id") != cid]
    ui_state.setdefault("chat_messages", {}).pop(str(cid), None)

    active_pid = ui_state.get("active_project_id")
    remaining_chats = []
    if active_pid is not None:
        project_chats = next(
            (
                p.get("chats", [])
                for p in ui_state.get("projects", [])
                if p.get("id") == active_pid
            ),
            [],
        )
        remaining_chats = [
            c for c in ui_state.get("chats", []) if c.get("id") in project_chats
        ]

    if remaining_chats:
        ui_state["active_chat_id"] = remaining_chats[0]["id"]
    elif ui_state.get("chats"):
        ui_state["active_chat_id"] = ui_state["chats"][0]["id"]
    else:
        _new_chat(self)

    _save_state_to_disk()
    self._populate_chat_list()

    # Clear UI and reload active chat
    chat_log = getattr(self, "chat_log", None)
    if chat_log:
        for widget in list(chat_log.winfo_children()):
            widget.destroy()
    self._messages = {}

    active_cid = str(ui_state.get("active_chat_id"))
    for msg in ui_state.get("chat_messages", {}).get(active_cid, []):
        self._bubble(msg.get("role", "assistant"), msg.get("text", ""), persist=False)


def _clear_active_chat(self) -> None:
    """Remove all messages in the active chat (keeps the chat thread)."""
    active_chat_id = ui_state.get("active_chat_id")
    if active_chat_id is None:
        return

    title = next(
        (c["title"] for c in ui_state.get("chats", []) if c["id"] == active_chat_id),
        f"Chat {active_chat_id}",
    )

    try:
        confirmed = messagebox.askyesno(
            "Clear Chat", f"Clear all messages in “{title}”?"
        )
    except Exception:
        return
    if not confirmed:
        return

    cid = str(active_chat_id)
    ui_state.setdefault("chat_messages", {})[cid] = []
    _save_state_to_disk()

    # Clear UI display
    chat_log = getattr(self, "chat_log", None)
    if chat_log:
        for widget in list(chat_log.winfo_children()):
            widget.destroy()
    self._messages = {}


# ────────────────────────────────
# UI Population & Selection
# ────────────────────────────────


def _populate_project_list(self) -> None:
    """Refresh the project list in the sidebar."""
    try:
        self.project_list.delete(0, "end")
        for project in ui_state.get("projects", []):
            self.project_list.insert("end", project.get("name", "Project"))
    except Exception:
        pass


def _populate_chat_list(self) -> None:
    """Refresh the chat list for the active project."""
    try:
        self.chat_list.delete(0, "end")
        active_pid = ui_state.get("active_project_id")
        if active_pid is None:
            return

        project_chats = next(
            (
                p.get("chats", [])
                for p in ui_state.get("projects", [])
                if p.get("id") == active_pid
            ),
            [],
        )
        chat_map = {c["id"]: c for c in ui_state.get("chats", [])}
        for cid in project_chats:
            chat = chat_map.get(cid, {})
            self.chat_list.insert("end", chat.get("title", f"Chat {cid}"))
    except Exception:
        pass


def _select_project_in_list(self, project_id: int | None) -> None:
    """Highlight a project in the project list."""
    if project_id is None:
        return
    try:
        projects = ui_state.get("projects", [])
        idx = next(i for i, p in enumerate(projects) if p.get("id") == project_id)
        self.project_list.selection_clear(0, "end")
        self.project_list.selection_set(idx)
        self.project_list.see(idx)
    except Exception:
        pass


def _select_chat_in_list(self, chat_id: int | None) -> None:
    """Highlight a chat in the chat list."""
    if chat_id is None:
        return
    try:
        active_pid = ui_state.get("active_project_id")
        if active_pid is None:
            return
        project_chats = next(
            (
                p.get("chats", [])
                for p in ui_state.get("projects", [])
                if p.get("id") == active_pid
            ),
            [],
        )
        idx = project_chats.index(chat_id)
        self.chat_list.selection_clear(0, "end")
        self.chat_list.selection_set(idx)
        self.chat_list.see(idx)
    except Exception:
        pass


def _on_project_selected(self, _event) -> None:
    """Handle project selection in UI."""
    if getattr(self, "_suppress_project_event", False):
        return

    selection = self.project_list.curselection()
    if not selection:
        return

    idx = selection[0]
    projects = ui_state.get("projects", [])
    try:
        project_id = projects[idx]["id"]
    except Exception:
        return

    if ui_state.get("active_project_id") == project_id:
        return

    ui_state["active_project_id"] = project_id
    _save_state_to_disk()

    self._populate_chat_list()
    try:
        if self.chat_list.size() > 0:
            self.chat_list.selection_clear(0, "end")
            self.chat_list.selection_set(0)
            self.chat_list.activate(0)
            self.chat_list.see(0)
            self._on_chat_selected(None)
    except Exception:
        pass


def _on_chat_selected(self, _event) -> None:
    """Handle chat selection in UI."""
    if getattr(self, "_suppress_select_event", False):
        return
    selection = self.chat_list.curselection()
    if not selection:
        return
    idx = selection[0]
    active_pid = ui_state.get("active_project_id")
    if active_pid is None:
        return
    project_chats = next(
        (
            p.get("chats", [])
            for p in ui_state.get("projects", [])
            if p.get("id") == active_pid
        ),
        [],
    )
    try:
        chat_id = project_chats[idx]
    except Exception:
        return
    if ui_state.get("active_chat_id") == chat_id:
        return
    ui_state["active_chat_id"] = chat_id
    _save_state_to_disk()

    # Clear chat display
    chat_log = getattr(self, "chat_log", None)
    if chat_log:
        for widget in list(chat_log.winfo_children()):
            widget.destroy()
    self._messages = {}

    # Load messages
    cid = str(chat_id)
    for msg in ui_state.get("chat_messages", {}).get(cid, []):
        self._bubble(msg.get("role", "assistant"), msg.get("text", ""), persist=False)


# ────────────────────────────────
# Import / Export
# ────────────────────────────────


def _export_active_chat(self) -> None:
    """Export active chat to a text file."""
    cid = str(ui_state.get("active_chat_id", 1))
    msgs = ui_state.get("chat_messages", {}).get(cid, [])
    if not msgs:
        return
    try:
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"chat_{cid}.txt",
            title="Export Chat",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as fh:
            for msg in msgs:
                role = (msg.get("role") or "user").upper()
                text = msg.get("text") or ""
                fh.write(f"[{role}] {text}\n\n")
    except Exception:
        pass


def _import_chat_from_file(self) -> None:
    """Import a chat from a text file into the active project."""
    try:
        path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Import Chat",
        )
        if not path:
            return
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read().strip()
    except Exception:
        return

    chat_id = _allocate_chat_id()
    title = f"Imported {chat_id}"

    active_pid = ui_state.get("active_project_id")
    if active_pid is not None:
        for project in ui_state.get("projects", []):
            if project.get("id") == active_pid:
                project.setdefault("chats", []).append(chat_id)
                break

    ui_state.setdefault("chats", []).append({"id": chat_id, "title": title})
    ui_state["active_chat_id"] = chat_id
    ui_state.setdefault("chat_messages", {})[str(chat_id)] = [
        {"role": "user", "text": content}
    ]
    _save_state_to_disk()
    self._populate_chat_list()
    self._select_chat_in_list(chat_id)
    self._bubble("user", content, persist=False)


# ────────────────────────────────
# Attachment
# ────────────────────────────────


def attach_history(app) -> None:
    """Attach all history-related methods to the app namespace."""
    methods = {
        # Projects
        "_new_project": _new_project,
        "_delete_project": _delete_project,
        "_rename_project": _rename_project,
        "_populate_project_list": _populate_project_list,
        "_select_project_in_list": _select_project_in_list,
        "_on_project_selected": _on_project_selected,
        # Chats
        "_new_chat": _new_chat,
        "_delete_active_chat": _delete_active_chat,
        "_clear_active_chat": _clear_active_chat,
        "_populate_chat_list": _populate_chat_list,
        "_select_chat_in_list": _select_chat_in_list,
        "_on_chat_selected": _on_chat_selected,
        # I/O
        "_export_active_chat": _export_active_chat,
        "_import_chat_from_file": _import_chat_from_file,
        # Persistence
        "_load_chats": lambda self: None,  # Deprecated
        "_save_chats": _save_chats,
    }

    for name, func in methods.items():
        setattr(app, name, MethodType(func, app))


# ────────────────────────────────
# Initialization Helper
# ────────────────────────────────


def initialize_history_state() -> None:
    """Ensure projects/chats structure exists in ui_state."""
    disk_state = _load_state_from_disk()
    disk_next = disk_state.get("next_chat_id")
    if isinstance(disk_next, int):
        ui_state["_disk_next_chat_id"] = disk_next

    if not ui_state.get("projects"):
        ui_state["projects"] = disk_state.get("projects") or [
            {"id": 1, "name": "Default", "chats": []}
        ]

    if not ui_state.get("chats"):
        ui_state["chats"] = disk_state.get("chats") or []

    ui_state.setdefault("active_project_id", ui_state["projects"][0]["id"])
    active_pid = ui_state["active_project_id"]
    project_chats = next(
        (p.get("chats", []) for p in ui_state["projects"] if p.get("id") == active_pid),
        [],
    )
    if project_chats:
        ui_state.setdefault("active_chat_id", project_chats[0])
    elif ui_state["chats"]:
        ui_state.setdefault("active_chat_id", ui_state["chats"][0]["id"])
    else:
        first_chat_id = 1
        ui_state["chats"] = [{"id": first_chat_id, "title": "Welcome"}]
        ui_state["active_chat_id"] = first_chat_id
        ui_state["projects"][0].setdefault("chats", []).append(first_chat_id)

    ui_state.setdefault("chat_messages", disk_state.get("chat_messages", {}))
    ui_state.setdefault("preferences", disk_state.get("preferences", {}))

    active_cid = str(ui_state["active_chat_id"])
    ui_state["chat_messages"].setdefault(active_cid, [])
    _ensure_next_chat_id()
    ui_state.pop("_disk_next_chat_id", None)


__all__ = ["attach_history", "initialize_history_state"]
