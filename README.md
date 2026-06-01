# Pixel Token Pet

A small pixel-style desktop pet for Windows that shows local Codex and Claude usage.

## Features

- Floating pixel pet window.
- Codex token usage from `%USERPROFILE%\.codex\logs_2.sqlite`.
- Codex goal-complete detection from `%USERPROFILE%\.codex\goals_1.sqlite`.
- Claude Code usage from `ccusage daily --json` or `%USERPROFILE%\.claude\projects\**\*.jsonl`.
- Claude Code fallback search in `%APPDATA%\Claude` and Windows packaged Claude folders.
- Cute completion popup when a Codex goal becomes `complete`.
- Manual completion popup by double-clicking the pet.
- External completion popup by touching `finish.signal`.
- Theme plugin system for replacing the pixel art and popup text.
- Ten bundled animal themes: fox, dog, cat, whale, rabbit, panda, penguin, frog, hamster, and owl.
- Gear button in the top-right corner for changing settings without editing JSON.
- Daily memory usage logging for the pet process.

## Run

Double-click:

```text
run_pet_silent.vbs
```

Use this when you want a normal no-console startup.

For debugging, run:

```powershell
python pixel_token_pet.py
```

or double-click:

```text
run_pet.bat
```

## Controls

- Drag: left mouse button.
- Settings: click the gear in the top-right corner.
- Menu: right click.
- Completion popup: double click.
- Close: right-click menu, then `Close pet`.

## Settings

Click the gear in the top-right corner to change common settings:

- Active theme.
- Always-on-top window behavior.
- Memory logging on/off.
- Refresh interval.
- Memory sample interval.

Settings are saved to `config.json`, which stays local and is ignored by git.

## Completion Popup Rules

The popup does not fire when each shell command or tool call finishes.

By default it fires only when:

- A Codex goal changes to `complete`.
- `finish.signal` is updated.
- The user manually triggers it from the pet.

Relevant config:

```json
{
  "trigger_finish_popup_on_new_codex_completion": false,
  "trigger_finish_popup_on_goal_complete": true,
  "finish_signal_file": "finish.signal"
}
```

## Memory Usage Logging

The pet records its own memory usage so you can leave it running for a day and see how much RAM it uses. The current-day memory usage is also shown directly in the pet window.

Default behavior:

- Logs one sample every 5 minutes.
- Writes JSON Lines files into `logs/`.
- Uses one file per day: `logs/memory-YYYY-MM-DD.jsonl`.
- `logs/` is ignored by git.
- The UI shows current / average / max memory for the current day.

Each record contains:

```json
{
  "timestamp": "2026-06-02T12:00:00",
  "rss_bytes": 12345678,
  "private_bytes": 12345678,
  "peak_rss_bytes": 12345678
}
```

To inspect one day:

```powershell
Get-Content .\logs\memory-2026-06-02.jsonl
```

Relevant config:

```json
{
  "memory_log_enabled": true,
  "memory_sample_seconds": 300,
  "memory_log_dir": "logs"
}
```

## Theme Plugins

Pet art and popup text are loaded from:

```text
plugins/<theme_id>/pet_theme.json
```

Bundled themes:

- `default_blob`
- `fox`
- `dog`
- `cat`
- `whale`
- `rabbit`
- `panda`
- `penguin`
- `frog`
- `hamster`
- `owl`

Set the active theme from the gear settings panel or in `config.json`:

```json
{
  "theme": "fox"
}
```

See `plugins/README.md` for the plugin schema.

## Sharing With Other People

This app is portable:

- Clone or download the repository.
- Install Python 3 on Windows.
- Run `run_pet_silent.vbs` for normal use or `python pixel_token_pet.py` for debugging.
- Optional local data paths are read from `config.json`.

If Codex or Claude data is not present on a machine, the app still opens and shows zero/unavailable usage instead of crashing.

## Config

The app creates `config.json` on first run. This file is local-only and ignored by git.

Use `config.example.json` as the portable template:

```json
{
  "codex_logs_db": "%USERPROFILE%\\.codex\\logs_2.sqlite",
  "codex_goals_db": "%USERPROFILE%\\.codex\\goals_1.sqlite",
  "claude_dir": "%USERPROFILE%\\.claude",
  "claude_exe": "%USERPROFILE%\\.local\\bin\\claude.exe",
  "claude_extra_dirs": [],
  "refresh_seconds": 5,
  "always_on_top": true,
  "trigger_finish_popup_on_new_codex_completion": false,
  "trigger_finish_popup_on_goal_complete": true,
  "finish_signal_file": "finish.signal",
  "theme": "default_blob",
  "memory_log_enabled": true,
  "memory_sample_seconds": 300,
  "memory_log_dir": "logs"
}
```

## Privacy Notes

This project should not commit local config, token databases, usage logs, or generated memory logs.

Ignored local files include:

- `config.json`
- `finish.signal`
- `logs/`
- `__pycache__/`
