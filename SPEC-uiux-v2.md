# Pixel Token Pet v2 — UI/UX Refresh Specification

## 1. Background & Goals

The current 340×286 window packs all data with minimal visual hierarchy. This refresh improves legibility, surfaces hidden information, and adds two distinct completion popups — one for Codex and one for Claude — without changing the underlying data layer or plugin schema.

---

## 2. System Architecture (unchanged)

```
pixel_token_pet.py
├── load_config / save_config      ← JSON persistence (config.json)
├── UsageReader                    ← Data layer
│   ├── codex()                    → Reads logs_2.sqlite for token completions
│   ├── codex_goal_state()         → Reads goals_1.sqlite for completion state
│   ├── codex_turn_activity()      → Latest response/command IDs for popup gating
│   └── claude()                   → ccusage CLI → JSONL fallback → exe detection
├── PetTheme                       ← Plugin loader (plugins/<id>/pet_theme.json)
├── MemoryMonitor                  ← Windows psapi.dll memory tracker + JSONL logger
└── PixelPet                       ← Tkinter root + draw loop + event handling
    ├── animate()      280ms tick → draw()
    ├── refresh()      N-sec poll → reads all data → draw()
    ├── record_memory()  M-sec poll → writes JSONL
    ├── draw()           Full canvas redraw each frame
    ├── finish_popup()   Codex-style done popup (pink/green)
    └── claude_popup()   Claude-style done popup  ← NEW (indigo/purple)
```

---

## 3. Window & Layout

### 3.1 Dimensions

| | Before | After |
|---|---|---|
| Normal width | 340 | 360 |
| Normal height | 286 | 320 |
| Compact height | — | 92 |

### 3.2 Normal mode layout (360×320)

```
┌────────────────────────────────────────────────┐  y=0
│ [×]                              [gear ⚙]      │  y=14-36  close + gear buttons
│ [pet sprite]  PIXEL TOKEN PET                  │  y=16-80  pet + title
│               right click / dblclick done      │
├──────────────────────────────────────────────── │  y=82
│ ● CODEX                                        │  y=88     status dot + header
│   today in/out : X.XK / X.XK                  │  y=108
│   today total  : X.XK  calls N                │  y=126    ████ out
│   cached/reason: X.XK / X.XK                  │  y=144    ████ cache
│   all tokens   : X.XM                         │  y=162
│   latest HH:MM:SS model-name                  │  y=180
├─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│  y=196    section separator
│ ● CLAUDE                                       │  y=204    status dot + header
│   today total: X.XK  calls N   $X.XXX         │  y=224    cost shown if >0
│   in/out/cache: X.XK/X.XK/X.XK               │  y=242
│   month total: X.XM  $X.XXX                   │  y=258
├──────────────────────────────────────────────── │
│ MEM now/avg/max: X/X/X MB  samples N           │  y=302    font 8pt (was 7pt)
└────────────────────────────────────────────────┘  y=320
```

### 3.3 Compact mode layout (360×92)

```
┌────────────────────────────────────────────────┐  y=0
│ [×]                              [gear ⚙]      │  y=14-36
│ [pet sprite]  PIXEL TOKEN PET                  │  y=16-80
│               right click / dblclick done      │
│ cx X.XK | cl X.XK  today                       │  y=68     single summary line
└────────────────────────────────────────────────┘  y=92
```

---

## 4. New UI Components

### 4.1 Close Button [×]

- Position: `close_box = (10, 14, 32, 36)` (top-left, inside panel)
- Visual: dark background square with red X lines
- Behaviour: single left-click destroys root window
- Rationale: `overrideredirect(True)` removes system title bar — no other visible close path

### 4.2 Status Indicator Dots

- 8×8 filled circle rendered at `(14, section_header_y + 4)` before each section header
- Green (`#8cffc1`) when `ok=True`, Red (`#ff7c8a`) when `ok=False`
- Section header text shifts right to x=27 (was 24) to clear the dot

### 4.3 Section Separator

- Single-pixel horizontal line in MUTED color at y=196, from x=24 to x=336

### 4.4 Compact Mode Toggle

- Right-click menu item "Compact view" / "Full view" (top of menu)
- On toggle: window resizes, canvas height adjusts, menu label flips
- Pet animation continues in compact mode

---

## 5. Data Display Improvements

### 5.1 Cost (Claude section)

- If `today["cost"] > 0.0001`: append `$X.XXX` on the today-total line
- If `month["cost"] > 0.0001`: append `$X.XXX` on the month-total line

### 5.2 Memory Footer

- Font size: 7 → 8

### 5.3 Progress Bars

- Bar width: 70 → 80 px (takes advantage of wider window)

---

## 6. Completion Popups

### 6.1 Codex Popup (updated `finish_popup()`)

Visual style: existing pink/green palette on `#1a1022` background.

Changes:
- Width: 292 → 320
- Height: 100 (no objective) or 120 (with objective)
- Click anywhere to dismiss immediately
- If `goal_state["latest_objective"]` is non-empty, show truncated (≤44 chars) on third line
- Particles: 32 (was 28), same square style with falling gravity

### 6.2 Claude Popup (new `claude_popup()`)

Visual style: indigo/purple palette, floating circular particles.

| Property | Value |
|---|---|
| Background | `#0d1117` (dark navy) |
| Inner fill | `#13101e` (dark indigo) |
| Border | `#7c6ff7` (indigo) |
| Title color | `#a78bfa` (light purple) |
| Body color | `#e2e8f0` (light gray-white) |
| Particles | `["#7c6ff7", "#a78bfa", "#c4b5fd", "#818cf8", "#6366f1"]` |
| Particle shape | Circular (create_oval), float **upward** with deceleration |
| Title text | `"✦  CLAUDE DONE"` |

Trigger: `trigger_claude_popup_on_new_completion` config key (default `false`).  
Detection: compare `claude_data["today"]["calls"]` vs `last_claude_calls` in `refresh()`.

---

## 7. Settings Panel

New trigger section added between "Display" and hint label.

**Added variables:**
- `trigger_finish_popup_on_new_codex_completion` → checkbox
- `trigger_finish_popup_on_goal_complete` → checkbox
- `trigger_finish_popup_on_final_response` → checkbox
- `finish_popup_delay_seconds` → text entry
- `trigger_claude_popup_on_new_completion` → checkbox

Window size: `360×292` → `380×450`

Layout addition:
```
━━ horizontal separator ━━━━━━━━━━━━━━━━
Triggers
[ ] Pop on new Codex completion
[x] Pop on goal complete
[x] Pop on final response
    Popup delay (seconds): [3]
[ ] Pop on new Claude completion
━━ horizontal separator ━━━━━━━━━━━━━━━━
Changes are saved to local config.json.
[Test Codex popup] [Test Claude popup]  [Save]
```

---

## 8. Configuration Changes

New keys added to `load_config()` defaults:

| Key | Default | Description |
|---|---|---|
| `trigger_claude_popup_on_new_completion` | `false` | Show Claude popup when new Claude calls detected |

---

## 9. Implementation Notes

- All changes are confined to `pixel_token_pet.py`; no plugin schema changes
- `self.compact`, `self.done_label`, `self.last_claude_calls` added to `PixelPet`
- `draw()` branches on `self.compact` to call `_draw_compact()` or normal path
- `NORMAL_W=360`, `NORMAL_H=320`, `COMPACT_W=360`, `COMPACT_H=92` added as module constants
- New methods: `draw_close()`, `draw_status_dot()`, `_draw_compact()`, `toggle_compact()`, `is_close_hit()`, `claude_popup()`
