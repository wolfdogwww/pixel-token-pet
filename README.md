# Pixel Token Pet

A Windows desktop widget that monitors **Codex** and **Claude Code** token usage in real time. Floats on screen as a pixel-art pet; shows today's and all-time token counts, cached tokens, cost, API calls, and its own memory footprint.

---

## Quick Start

Double-click `run_pet_silent.vbs` (no console window), or:

```powershell
python pixel_token_pet.py
```

Settings are stored in `config.json` (created on first run from defaults).

---

## Features

- **Live token counters** — Codex (SQLite) and Claude Code (ccusage or JSONL)
- **Two completion popups** — Codex style (pink/green, falling particles) and Claude style (indigo/purple, rising particles)
- **Compact mode** — right-click → *精簡模式 / Compact view* (360 × 92 px)
- **Minimize to system tray** — right-click → *縮到系統匣 / Minimize to tray*; single-click or double-click the tray icon to restore
- **Snap to tray corner** — positions window flush with the bottom-right of the work area
- **Language toggle** — English ↔ 中文 (gear → Settings → Language)
- **Engineer mode** — click the gear icon 5× rapidly to unlock test buttons and debug menu items
- **10 built-in themes** — cat, dog, fox, owl, panda, penguin, frog, hamster, rabbit, whale, blob

---

## Memory Usage (measured on Windows 11)

Sampled every 5 minutes via `psapi.dll · GetProcessMemoryInfo`.

| Metric | Value |
|---|---|
| **Steady-state RSS** | ~45.5 – 50.5 MB |
| **Average RSS (2026-06-03 so far)** | ~48.7 MB |
| **Peak RSS** | ~50.5 MB |
| **Private bytes (committed)** | ~28 MB |
| **Startup RSS** | ~25 MB |
| **Sample interval** | 300 s (configurable, min 30 s) |

> Data from 272 samples over 2026-06-02 (full day) and 150 samples on 2026-06-03 through 12:28.
> Memory is logged to `logs/memory-YYYY-MM-DD.jsonl` for offline analysis.

The footprint is dominated by Python 3.11 + Tkinter startup cost (~25 MB at launch) and grows slightly (~50 MB) after the SQLite and JSONL parsers warm up their internal caches.

---

## Configuration (`config.json`)

| Key | Default | Description |
|---|---|---|
| `refresh_seconds` | `5` | Poll interval for token data |
| `always_on_top` | `true` | Window stays above all others |
| `language` | `"en"` | UI language (`"en"` or `"zh"`) |
| `snap_to_tray` | `false` | Start in bottom-right corner |
| `theme` | `"default_blob"` | Active pet theme ID |
| `trigger_finish_popup_on_goal_complete` | `true` | Codex popup on goal completion |
| `trigger_finish_popup_on_final_response` | `true` | Codex popup after last response |
| `finish_popup_delay_seconds` | `3` | Grace period before popup fires |
| `trigger_claude_popup_on_new_completion` | `false` | Claude popup when session goes idle |
| `claude_idle_seconds` | `30` | Idle window to detect Claude session end |
| `memory_log_enabled` | `true` | Write RSS samples to `logs/` |
| `memory_sample_seconds` | `300` | RSS sample interval (min 30) |

---

## Adding a Theme

1. Create `plugins/my_theme/pet_theme.json` (copy an existing theme as template)
2. Define pixel art in `animations.idle.frames` (rows of symbol strings; `1`=outline `2`=body `3`=eye `4`=cheek)
3. Set colors in `palette` and display text in `speech`
4. Select it in Settings → Theme, or set `"theme": "my_theme"` in `config.json`

---

## Dependencies

No external packages. Requires **Python 3.6+** and **Windows** (uses `psapi.dll`, `shell32.dll`).
