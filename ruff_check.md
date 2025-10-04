📦[ToxicFartCloud@DevNew Adamv1]$ ruff check . --fix
E741 Ambiguous variable name: `l`
  --> eval/run.py:26:36
   |
25 |     with open(args.path, "r", encoding="utf-8") as f:
26 |         items = [json.loads(l) for l in f if l.strip()]
   |                                    ^
27 |
28 |     def run_mode(mode: str):
   |

invalid-syntax: Expected an indented block after `for` statement
   --> home/ToxicFartCloud/Projects/Adamv1/src/ui/app.py:321:9
    |
319 |     def _clear_canvas(self) -> None:
320 |         for child in self.canvas_cards.winfo_children():
321 |         self.canvas_canvas.configure(scrollregion=self.canvas_canvas.bbox("all"))
    |         ^^^^
322 |
323 |     def _handle_ctrl_return(self, _event) -> str:
    |

E701 Multiple statements on one line (colon)
   --> home/ToxicFartCloud/Projects/Adamv1/src/ui/app.py:447:26
    |
445 |     def _history_index_load(self):
446 |         p = self._index_path()
447 |         if not p.exists(): return []
    |                          ^
448 |         out = []
449 |         try:
    |

E701 Multiple statements on one line (colon)
   --> home/ToxicFartCloud/Projects/Adamv1/src/ui/app.py:454:52
    |
452 |                     try:
453 |                         parsed = json.loads(line)
454 |                         if isinstance(parsed, dict): out.append(parsed)
    |                                                    ^
455 |                     except Exception: continue
456 |         except Exception: return []
    |

E701 Multiple statements on one line (colon)
   --> home/ToxicFartCloud/Projects/Adamv1/src/ui/app.py:455:37
    |
453 |                         parsed = json.loads(line)
454 |                         if isinstance(parsed, dict): out.append(parsed)
455 |                     except Exception: continue
    |                                     ^
456 |         except Exception: return []
457 |         out.sort(key=lambda x: x.get("created", 0), reverse=True)
    |

E701 Multiple statements on one line (colon)
   --> home/ToxicFartCloud/Projects/Adamv1/src/ui/app.py:456:25
    |
454 |                         if isinstance(parsed, dict): out.append(parsed)
455 |                     except Exception: continue
456 |         except Exception: return []
    |                         ^
457 |         out.sort(key=lambda x: x.get("created", 0), reverse=True)
458 |         return out
    |

E701 Multiple statements on one line (colon)
   --> home/ToxicFartCloud/Projects/Adamv1/src/ui/app.py:466:25
    |
464 |             with p.open("a", encoding="utf-8") as handle:
465 |                 handle.write(json.dumps(rec) + "\n")
466 |         except Exception: pass
    |                         ^
467 |
468 |     def _history_refresh_list(self, select_name=None) -> None:
    |

E701 Multiple statements on one line (colon)
   --> home/ToxicFartCloud/Projects/Adamv1/src/ui/app.py:471:25
    |
469 |         try:
470 |             self.saved_list.delete(0, "end")
471 |         except Exception: return
    |                         ^
472 |         idx = self._history_index_load()
473 |         self._history_cache = idx
    |

E701 Multiple statements on one line (colon)
   --> home/ToxicFartCloud/Projects/Adamv1/src/ui/app.py:478:52
    |
476 |             label = item.get("name") or f"Chat {i + 1}"
477 |             self.saved_list.insert("end", "  " + label)
478 |             if select_name and label == select_name: selected_index = i
    |                                                    ^
479 |         if selected_index is not None:
480 |             try:
    |

E701 Multiple statements on one line (colon)
   --> home/ToxicFartCloud/Projects/Adamv1/src/ui/app.py:484:29
    |
482 |                 self.saved_list.selection_set(selected_index)
483 |                 self.saved_list.see(selected_index)
484 |             except Exception: pass
    |                             ^
485 |
486 |     def _history_open_selected(self) -> None:
    |

E701 Multiple statements on one line (colon)
   --> home/ToxicFartCloud/Projects/Adamv1/src/ui/app.py:489:25
    |
487 |         try:
488 |             selection = self.saved_list.curselection()
489 |         except Exception: return
    |                         ^
490 |         if not selection: return
491 |         index = selection[0]
    |

E701 Multiple statements on one line (colon)
   --> home/ToxicFartCloud/Projects/Adamv1/src/ui/app.py:490:25
    |
488 |             selection = self.saved_list.curselection()
489 |         except Exception: return
490 |         if not selection: return
    |                         ^
491 |         index = selection[0]
492 |         cache = getattr(self, "_history_cache", [])
    |

E701 Multiple statements on one line (colon)
   --> home/ToxicFartCloud/Projects/Adamv1/src/ui/app.py:493:31
    |
491 |         index = selection[0]
492 |         cache = getattr(self, "_history_cache", [])
493 |         if index >= len(cache): return
    |                               ^
494 |         item = cache[index]
495 |         path_value = item.get("path")
    |

E701 Multiple statements on one line (colon)
   --> home/ToxicFartCloud/Projects/Adamv1/src/ui/app.py:524:33
    |
522 |             if start > cursor:
523 |                 chunk = text[cursor:start]
524 |                 if chunk.strip(): segments.append(("text", chunk))
    |                                 ^
525 |             lang = (match.group(1) or "code").strip() or "code"
526 |             code = match.group(2) or ""
    |

E701 Multiple statements on one line (colon)
   --> home/ToxicFartCloud/Projects/Adamv1/src/ui/app.py:531:28
    |
529 |         if cursor < len(text):
530 |             tail = text[cursor:]
531 |             if tail.strip(): segments.append(("text", tail))
    |                            ^
532 |         if not segments and text.strip(): segments.append(("text", text))
533 |         return segments
    |

E701 Multiple statements on one line (colon)
   --> home/ToxicFartCloud/Projects/Adamv1/src/ui/app.py:532:41
    |
530 |             tail = text[cursor:]
531 |             if tail.strip(): segments.append(("text", tail))
532 |         if not segments and text.strip(): segments.append(("text", text))
    |                                         ^
533 |         return segments
    |

F841 Local variable `language` is assigned to but never used
  --> plugins/agent_coder.py:33:9
   |
31 |     try:
32 |         prompt = kwargs.get("prompt", "").strip()
33 |         language = kwargs.get("language", "python")
   |         ^^^^^^^^
34 |
35 |         if not prompt:
   |
help: Remove assignment to unused variable `language`

F841 Local variable `change_result` is assigned to but never used
   --> plugins/agent_interpreter.py:334:13
    |
332 |         # Apply the changes
333 |         try:
334 |             change_result = _apply_code_changes(proposal)
    |             ^^^^^^^^^^^^^
335 |             
336 |             # Test the changes if agent_tester is available
    |
help: Remove assignment to unused variable `change_result`

E402 Module level import not at top of file
  --> plugins/agent_router.py:18:1
   |
17 | # Import shared state
18 | from .group_chat import get_chat_history, append_message, clear_chat_history
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   |

F841 Local variable `model_path` is assigned to but never used
   --> plugins/creative_cortex.py:195:9
    |
194 |         mode_hint = kwargs.get("mode")
195 |         model_path = kwargs.get("model_path", "models/adam_offline.gguf")
    |         ^^^^^^^^^^
196 |
197 |         cortex = CreativeCortex()
    |
help: Remove assignment to unused variable `model_path`

E722 Do not use bare `except`
   --> plugins/hardware_audit.py:196:25
    |
194 |                         try:
195 |                             vram_gb = int(vram_str.replace("MB", "").strip()) // 1024
196 |                         except:
    |                         ^^^^^^
197 |                             vram_gb = 0
198 |                         gpus.append({"name": model, "vendor": vendor, "vram_gb": vram_gb})
    |

E402 Module level import not at top of file
  --> run_adam.py:14:1
   |
13 | # Import and run main from src/adam/core.py
14 | from adam.core import main
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^
15 |
16 | if __name__ == "__main__":
   |

F401 `collections.abc` imported but unused
 --> src/adam/adapters/__init__.py:3:8
  |
1 | # src/adam/adapters.py
2 |
3 | import collections.abc
  |        ^^^^^^^^^^^^^^^
4 | import logging
5 | import os
  |
help: Remove unused import: `collections.abc`

F401 `.base.register_backend` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
  --> src/adam/backends/__init__.py:12:19
   |
12 | from .base import register_backend
   |                   ^^^^^^^^^^^^^^^^
13 | from pathlib import Path
14 | import importlib
   |
help: Use an explicit re-export: `register_backend as register_backend`

E402 Module level import not at top of file
   --> src/adam/core.py:121:1
    |
119 |             return str(candidate)
120 |     return str(base.with_suffix(".gguf"))
121 | from collections.abc import Generator
    | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
122 | from src.adam.plugin_manager import manager
123 | from src.adam.adapters import ChromaVectorStore, SentenceTransformerEmbedder
    |

E402 Module level import not at top of file
   --> src/adam/core.py:122:1
    |
120 |     return str(base.with_suffix(".gguf"))
121 | from collections.abc import Generator
122 | from src.adam.plugin_manager import manager
    | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
123 | from src.adam.adapters import ChromaVectorStore, SentenceTransformerEmbedder
    |

E402 Module level import not at top of file
   --> src/adam/core.py:123:1
    |
121 | from collections.abc import Generator
122 | from src.adam.plugin_manager import manager
123 | from src.adam.adapters import ChromaVectorStore, SentenceTransformerEmbedder
    | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
124 |
125 | # ------------------------------------------------------------------------------
    |

E402 Module level import not at top of file
  --> src/adam/utils/plugin_utils.py:8:1
   |
 6 | }
 7 |
 8 | import json
   | ^^^^^^^^^^^
 9 | import os
10 | from datetime import datetime, timezone
   |

E402 Module level import not at top of file
  --> src/adam/utils/plugin_utils.py:9:1
   |
 8 | import json
 9 | import os
   | ^^^^^^^^^
10 | from datetime import datetime, timezone
11 | from pathlib import Path
   |

E402 Module level import not at top of file
  --> src/adam/utils/plugin_utils.py:10:1
   |
 8 | import json
 9 | import os
10 | from datetime import datetime, timezone
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
11 | from pathlib import Path
12 | from typing import Any, Dict, List, Tuple
   |

E402 Module level import not at top of file
  --> src/adam/utils/plugin_utils.py:11:1
   |
 9 | import os
10 | from datetime import datetime, timezone
11 | from pathlib import Path
   | ^^^^^^^^^^^^^^^^^^^^^^^^
12 | from typing import Any, Dict, List, Tuple
   |

E402 Module level import not at top of file
  --> src/adam/utils/plugin_utils.py:12:1
   |
10 | from datetime import datetime, timezone
11 | from pathlib import Path
12 | from typing import Any, Dict, List, Tuple
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
13 |
14 | LOG_PATH = Path("logs") / "audit.jsonl"
   |

invalid-syntax: Unexpected indentation
 --> src/adam/utils/tool_base.py:1:1
  |
1 |     """
  | ^^^^
2 |     tool_base.py — Optional abstract base class for Adam Tools.
  |

invalid-syntax: Expected a statement
  --> src/adam/utils/tool_base.py:11:1
   |
 9 |     """
10 |
11 | METADATA = {
   | ^
12 |     "executable": False,
13 |     "description": "Abstract base class for Tools.  Optional - Adam only required run(**kwargs)",
   |

E702 Multiple statements on one line (semicolon)
 --> src/server/main.py:1:28
  |
1 | from fastapi import FastAPI; app = FastAPI()
  |                            ^
  |

F401 `.utils.validation.extract_code_blocks` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
 --> src/ui/__init__.py:1:31
  |
1 | from .utils.validation import extract_code_blocks
  |                               ^^^^^^^^^^^^^^^^^^^
2 | from .components.model_selector import render_model_selector
3 | from .components.sidebar import render_sidebar
  |
help: Use an explicit re-export: `extract_code_blocks as extract_code_blocks`

F401 `.components.model_selector.render_model_selector` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
 --> src/ui/__init__.py:2:40
  |
1 | from .utils.validation import extract_code_blocks
2 | from .components.model_selector import render_model_selector
  |                                        ^^^^^^^^^^^^^^^^^^^^^
3 | from .components.sidebar import render_sidebar
4 | from .components.chat import render_chat
  |
help: Use an explicit re-export: `render_model_selector as render_model_selector`

F401 `.components.sidebar.render_sidebar` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
 --> src/ui/__init__.py:3:33
  |
1 | from .utils.validation import extract_code_blocks
2 | from .components.model_selector import render_model_selector
3 | from .components.sidebar import render_sidebar
  |                                 ^^^^^^^^^^^^^^
4 | from .components.chat import render_chat
5 | from .state import ui_state
  |
help: Use an explicit re-export: `render_sidebar as render_sidebar`

F401 `.components.chat.render_chat` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
 --> src/ui/__init__.py:4:30
  |
2 | from .components.model_selector import render_model_selector
3 | from .components.sidebar import render_sidebar
4 | from .components.chat import render_chat
  |                              ^^^^^^^^^^^
5 | from .state import ui_state
6 | from .components.history import attach_history
  |
help: Use an explicit re-export: `render_chat as render_chat`

F401 `.state.ui_state` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
 --> src/ui/__init__.py:5:20
  |
3 | from .components.sidebar import render_sidebar
4 | from .components.chat import render_chat
5 | from .state import ui_state
  |                    ^^^^^^^^
6 | from .components.history import attach_history
  |
help: Use an explicit re-export: `ui_state as ui_state`

F401 `.components.history.attach_history` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
 --> src/ui/__init__.py:6:33
  |
4 | from .components.chat import render_chat
5 | from .state import ui_state
6 | from .components.history import attach_history
  |                                 ^^^^^^^^^^^^^^
  |
help: Use an explicit re-export: `attach_history as attach_history`

E402 Module level import not at top of file
  --> src/ui/app.py:26:1
   |
26 | from .state import ensure_defaults
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
27 | from .components.layout import attach_layout
28 | from .components.sidebar import render_sidebar
   |

E402 Module level import not at top of file
  --> src/ui/app.py:27:1
   |
26 | from .state import ensure_defaults
27 | from .components.layout import attach_layout
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
28 | from .components.sidebar import render_sidebar
29 | from .components.chat import render_chat
   |

E402 Module level import not at top of file
  --> src/ui/app.py:28:1
   |
26 | from .state import ensure_defaults
27 | from .components.layout import attach_layout
28 | from .components.sidebar import render_sidebar
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
29 | from .components.chat import render_chat
30 | from .components.settings import render_settings
   |

E402 Module level import not at top of file
  --> src/ui/app.py:29:1
   |
27 | from .components.layout import attach_layout
28 | from .components.sidebar import render_sidebar
29 | from .components.chat import render_chat
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
30 | from .components.settings import render_settings
31 | from .components.history import attach_history
   |

E402 Module level import not at top of file
  --> src/ui/app.py:30:1
   |
28 | from .components.sidebar import render_sidebar
29 | from .components.chat import render_chat
30 | from .components.settings import render_settings
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
31 | from .components.history import attach_history
32 | from .components.renderer import attach_renderer
   |

E402 Module level import not at top of file
  --> src/ui/app.py:31:1
   |
29 | from .components.chat import render_chat
30 | from .components.settings import render_settings
31 | from .components.history import attach_history
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
32 | from .components.renderer import attach_renderer
33 | from .components.search import attach_search
   |

E402 Module level import not at top of file
  --> src/ui/app.py:32:1
   |
30 | from .components.settings import render_settings
31 | from .components.history import attach_history
32 | from .components.renderer import attach_renderer
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
33 | from .components.search import attach_search
34 | from .components.theme import attach_theme
   |

E402 Module level import not at top of file
  --> src/ui/app.py:33:1
   |
31 | from .components.history import attach_history
32 | from .components.renderer import attach_renderer
33 | from .components.search import attach_search
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
34 | from .components.theme import attach_theme
35 | from .components.model_sync import attach_model_sync
   |

E402 Module level import not at top of file
  --> src/ui/app.py:34:1
   |
32 | from .components.renderer import attach_renderer
33 | from .components.search import attach_search
34 | from .components.theme import attach_theme
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
35 | from .components.model_sync import attach_model_sync
36 | from .components.shortcuts import attach_shortcuts
   |

E402 Module level import not at top of file
  --> src/ui/app.py:35:1
   |
33 | from .components.search import attach_search
34 | from .components.theme import attach_theme
35 | from .components.model_sync import attach_model_sync
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
36 | from .components.shortcuts import attach_shortcuts
37 | from .components.style import set_spacing_scale
   |

E402 Module level import not at top of file
  --> src/ui/app.py:36:1
   |
34 | from .components.theme import attach_theme
35 | from .components.model_sync import attach_model_sync
36 | from .components.shortcuts import attach_shortcuts
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
37 | from .components.style import set_spacing_scale
38 | from .fallback_ui import launch_fallback_ui
   |

E402 Module level import not at top of file
  --> src/ui/app.py:37:1
   |
35 | from .components.model_sync import attach_model_sync
36 | from .components.shortcuts import attach_shortcuts
37 | from .components.style import set_spacing_scale
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
38 | from .fallback_ui import launch_fallback_ui
   |

E402 Module level import not at top of file
  --> src/ui/app.py:38:1
   |
36 | from .components.shortcuts import attach_shortcuts
37 | from .components.style import set_spacing_scale
38 | from .fallback_ui import launch_fallback_ui
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
39 |
40 | logger = logging.getLogger(__name__)
   |

F841 Local variable `chat_container` is assigned to but never used
  --> src/ui/components/layout.py:65:13
   |
63 |             if canvas_container and str(p) == str(canvas_container):
64 |                 continue
65 |             chat_container = p
   |             ^^^^^^^^^^^^^^
66 |             break
   |
help: Remove assignment to unused variable `chat_container`

E702 Multiple statements on one line (semicolon)
 --> tools/deep_diag.py:7:15
  |
5 | import re
6 | REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
7 | os.chdir(REPO); sys.path.insert(0, REPO)
  |               ^
8 |
9 | def read(p):
  |

E701 Multiple statements on one line (colon)
  --> tools/deep_diag.py:11:47
   |
 9 | def read(p):
10 |     try: 
11 |         with open(p,"r",encoding="utf-8") as f: return f.read()
   |                                               ^
12 |     except Exception: return None
   |

E701 Multiple statements on one line (colon)
  --> tools/deep_diag.py:12:21
   |
10 |     try: 
11 |         with open(p,"r",encoding="utf-8") as f: return f.read()
12 |     except Exception: return None
   |                     ^
13 |
14 | def exists(p): return os.path.exists(p)
   |

E701 Multiple statements on one line (colon)
  --> tools/deep_diag.py:21:29
   |
19 |            "sled":"sidecars/sled/app.py","plugins_list":"config/plugins.txt","config_yaml":"config/adam.yaml",
20 |            "models_dir":"models"}
21 |     for k,p in paths.items(): report["exists"][k]=exists(p)
   |                             ^
22 |     s = read("Adam.py") or ""
23 |     report["checks"].append({"name":"launcher_is_thin",
   |

E702 Multiple statements on one line (semicolon)
  --> tools/deep_diag.py:50:42
   |
48 |         txt = read("config/plugins.txt") or ""
49 |         plugins=[ln.strip() for ln in txt.splitlines() if ln.strip() and not ln.strip().startswith("#")]
50 |     report["plugins"]["declared"]=plugins; report["plugins"]["count"]=len(plugins)
   |                                          ^
51 |     ok_all = all(c["ok"] for c in report["checks"])
52 |     print(json.dumps({"ok":ok_all, **report}, indent=2))
   |

E701 Multiple statements on one line (colon)
  --> tools/deep_diag.py:54:24
   |
52 |     print(json.dumps({"ok":ok_all, **report}, indent=2))
53 |     return 0 if ok_all else 1
54 | if __name__=="__main__": raise SystemExit(main())
   |                        ^
   |

E701 Multiple statements on one line (colon)
  --> tools/diag_adam.py:14:12
   |
12 |     with socket.socket() as s:
13 |         s.settimeout(t)
14 |         try: s.connect((h,p)); return True
   |            ^
15 |         except Exception: return False
   |

E702 Multiple statements on one line (semicolon)
  --> tools/diag_adam.py:14:30
   |
12 |     with socket.socket() as s:
13 |         s.settimeout(t)
14 |         try: s.connect((h,p)); return True
   |                              ^
15 |         except Exception: return False
   |

E701 Multiple statements on one line (colon)
  --> tools/diag_adam.py:15:25
   |
13 |         s.settimeout(t)
14 |         try: s.connect((h,p)); return True
15 |         except Exception: return False
   |                         ^
16 |
17 | def main():
   |

E702 Multiple statements on one line (semicolon)
  --> tools/diag_adam.py:18:19
   |
17 | def main():
18 |     os.chdir(REPO); sys.path.insert(0, REPO)
   |                   ^
19 |     result = {"repo": REPO, "python": sys.executable, "steps": []}
20 |     # adam_base import
   |

E701 Multiple statements on one line (colon)
  --> tools/diag_adam.py:22:8
   |
20 |     # adam_base import
21 |     step = {"name":"launcher_import","ok":False,"details":""}
22 |     try: step["ok"]=True
   |        ^
23 |     except Exception as e: step["details"]=f"adam_base import failed: {e}"
24 |     result["steps"].append(step)
   |

E701 Multiple statements on one line (colon)
  --> tools/diag_adam.py:23:26
   |
21 |     step = {"name":"launcher_import","ok":False,"details":""}
22 |     try: step["ok"]=True
23 |     except Exception as e: step["details"]=f"adam_base import failed: {e}"
   |                          ^
24 |     result["steps"].append(step)
25 |     # run_ui present?
   |

E701 Multiple statements on one line (colon)
  --> tools/diag_adam.py:27:8
   |
25 |     # run_ui present?
26 |     step = {"name":"run_ui_present","ok":False,"details":""}
27 |     try: step["ok"]=True
   |        ^
28 |     except Exception as e: step["details"]=f"run_ui missing: {e}"
29 |     result["steps"].append(step)
   |

E701 Multiple statements on one line (colon)
  --> tools/diag_adam.py:28:26
   |
26 |     step = {"name":"run_ui_present","ok":False,"details":""}
27 |     try: step["ok"]=True
28 |     except Exception as e: step["details"]=f"run_ui missing: {e}"
   |                          ^
29 |     result["steps"].append(step)
30 |     # backend health (auto-start if down)
   |

E701 Multiple statements on one line (colon)
  --> tools/diag_adam.py:38:36
   |
36 |             t0=time.time()
37 |             while time.time()-t0<6:
38 |                 if is_up(HOST,PORT): break
   |                                    ^
39 |                 time.sleep(0.25)
40 |         except Exception as e: step["details"]=f"autostart failed: {e}"
   |

E701 Multiple statements on one line (colon)
  --> tools/diag_adam.py:40:30
   |
38 |                 if is_up(HOST,PORT): break
39 |                 time.sleep(0.25)
40 |         except Exception as e: step["details"]=f"autostart failed: {e}"
   |                              ^
41 |     step["ok"]=is_up(HOST,PORT)
42 |     if not step["ok"] and not step["details"]: step["details"]="backend not reachable"
   |

E701 Multiple statements on one line (colon)
  --> tools/diag_adam.py:42:46
   |
40 |         except Exception as e: step["details"]=f"autostart failed: {e}"
41 |     step["ok"]=is_up(HOST,PORT)
42 |     if not step["ok"] and not step["details"]: step["details"]="backend not reachable"
   |                                              ^
43 |     result["steps"].append(step)
44 |     print(json.dumps(result, indent=2))
   |

E701 Multiple statements on one line (colon)
  --> tools/diag_adam.py:46:24
   |
44 |     print(json.dumps(result, indent=2))
45 |     return 0 if all(s["ok"] for s in result["steps"]) else 1
46 | if __name__=="__main__": raise SystemExit(main())
   |                        ^
   |

invalid-syntax: Expected `except` or `finally` after `try` block
  --> tools/model_update.py:66:1
   |
64 |             error_msg = f"Missing script: {script}"
65 |             logger.error(error_msg)
   |                                    ^
   |

Found 74 errors.
No fixes available (4 hidden fixes can be enabled with the `--unsafe-fixes` option).

