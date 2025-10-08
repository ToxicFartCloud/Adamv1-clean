# UI Refresh Context (October 2025)

## Theme System
- Replaced the default dark palette with web-aligned colors, including hover, sidebar, composer, and status tokens.
- Added a complete light theme preset and a `set_theme_mode` helper to swap between light/dark palettes.
- Extended theme application to push colors, fonts, layout tokens, selection highlights, and ttk style padding/focus rings globally.
- Introduced chat bubble role colors (default + hover) and ensured layout tokens (sidebar width, sash) are enforced.

## Chat Experience
- Added a fallback `_bubble_fallback` renderer that consumes the new bubble tokens and implements hover tinting.
- Updated the composer surface/placeholder styling, Enter and Ctrl/Cmd+Enter bindings, and implemented a muted placeholder flow.
- Added a floating “Scroll to latest” button driven by `_update_scroll_button` and ensured scroll bindings keep it in sync.
- Exposed `set_status` with themed status dot colors for the header health indicator.

## Sidebar Improvements
- Added a hover-focused shim for listbox rows, using new sidebar hover tokens.
- Introduced a styled search field with placeholder behavior that reuses composer placeholder colors.

## Classic Tk/ttk Polish
- Applied option database defaults for buttons, inputs, scrollbars, listboxes, canvases, and selection colors to match the web spec.
- Configured ttk widgets (buttons, entries, combo boxes, labels, frames) with consistent padding, accent focus rings, and an accent button variant.

## Miscellaneous
- Set typography via Tk named fonts to mirror CSS sizes.
- Ensured layout tokens and spacing scale propagate to layout rebalancing logic.

## November 2025 Updates
- Theme menu now includes a `Mode` submenu with light/dark radio items wired to `app.set_theme_mode`, plus an auto-initialized `StringVar` so the toggle persists.
- Model picker OptionMenu gains modern hover/active styling, flat relief, fixed width, and a rounded CTk replacement in the CustomTkinter desktop shell.
- Chat params panel is constructed during layout build, hidden by default, and the `_toggle_params_panel` helper safely restores it; Tk exception handler signature updated to prevent fallback crashes.
- CustomTkinter desktop UI received rounded surfaces (sidebar, composer, bubbles, typing indicator), simplified Adam branding, a pop-out Canvas button, responsive sidebar width, and soft-wrapped message bubbles with markdown-style code block rendering.
- Sidebar list now renders as rounded CTk buttons within a scrollable frame, supporting prepend updates and consistent theme tokens.
