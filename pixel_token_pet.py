import json
import re
import sqlite3
import subprocess
import sys
import time
import tkinter as tk
import ctypes
from ctypes import wintypes
from datetime import datetime
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config.json"
DEFAULT_CODEX_DB = Path.home() / ".codex" / "logs_2.sqlite"
DEFAULT_CODEX_GOALS_DB = Path.home() / ".codex" / "goals_1.sqlite"
DEFAULT_CLAUDE_DIR = Path.home() / ".claude"
DEFAULT_CLAUDE_EXE = Path.home() / ".local" / "bin" / "claude.exe"
DEFAULT_THEME = "default_blob"

NORMAL_W, NORMAL_H = 360, 320
COMPACT_W, COMPACT_H = 360, 92

PIXEL = 6
BG = "#17151f"
PANEL = "#242130"
INK = "#f7ecff"
MUTED = "#a99bb8"
GREEN = "#8cffc1"
PINK = "#ff8bd4"
YELLOW = "#ffe78a"
BLUE = "#7bd7ff"
RED = "#ff7c8a"

# Claude popup palette
CLAUDE_BG = "#0d1117"
CLAUDE_INNER = "#13101e"
CLAUDE_BORDER = "#7c6ff7"
CLAUDE_TITLE = "#a78bfa"
CLAUDE_BODY = "#e2e8f0"
CLAUDE_MUTED = "#6e7c8c"
CLAUDE_PARTICLES = ["#7c6ff7", "#a78bfa", "#c4b5fd", "#818cf8", "#6366f1"]

_LANG = {
    "en": {
        # right-click menu
        "compact_view":   "Compact view",
        "full_view":      "Full view",
        "min_to_tray":    "Minimize to tray",
        "snap_tray":      "Snap to tray corner",
        "refresh":        "Refresh",
        "close_pet":      "Close pet",
        "eng_done_anim":  "⚙ Done animation",
        "eng_claude_pop": "⚙ Claude popup",
        # settings window
        "settings_title": "Pixel Token Pet Settings",
        "lbl_theme":      "Theme",
        "lbl_display":    "Display",
        "ck_always_top":  "Always on top",
        "ck_memory_log":  "Memory logging",
        "ck_snap_tray":   "Start at system tray corner",
        "entry_refresh":  "Refresh seconds",
        "entry_mem_smp":  "Memory sample seconds",
        "lbl_triggers":   "Triggers",
        "ck_pop_codex":   "Pop on new Codex completion",
        "ck_pop_goal":    "Pop on goal complete",
        "ck_pop_final":   "Pop on final response",
        "entry_delay":    "Popup delay (seconds)",
        "ck_pop_claude":  "Pop on new Claude completion",
        "entry_idle":     "Claude idle seconds",
        "lbl_language":   "Language",
        "save_hint":      "Changes are saved to local config.json.",
        "btn_test_codex": "⚙ Test Codex",
        "btn_test_claude":"⚙ Test Claude",
        "btn_save":       "Save",
        # main window overlays
        "done_codex":     "Done! Codex finished.",
        "done_claude":    "Done! Claude session.",
        "eng_on":         "⚙ ENGINEER MODE ON",
        "eng_off":        "⚙ ENGINEER MODE OFF",
        "not_connected":  "usage: not connected",
        # data labels
        "lbl_today_io":   "today in/out : ",
        "lbl_today_tot":  "today total  : ",
        "lbl_cache_rsn":  "cached/reason: ",
        "lbl_all_tok":    "all tokens   : ",
        "lbl_latest":     "latest ",
        "lbl_cl_today":   "today total: ",
        "lbl_io_cache":   "in/out/cache: ",
        "lbl_month":      "month total: ",
        "lbl_mem":        "MEM now/avg/max: ",
        "lbl_mem_smp":    " MB  samples ",
    },
    "zh": {
        # right-click menu
        "compact_view":   "精簡模式",
        "full_view":      "完整模式",
        "min_to_tray":    "縮到系統匣",
        "snap_tray":      "貼齊右下角",
        "refresh":        "重新整理",
        "close_pet":      "關閉寵物",
        "eng_done_anim":  "⚙ 完成動畫",
        "eng_claude_pop": "⚙ Claude 彈窗",
        # settings window
        "settings_title": "Pixel Token Pet 設定",
        "lbl_theme":      "主題",
        "lbl_display":    "顯示",
        "ck_always_top":  "永遠在最上層",
        "ck_memory_log":  "記憶體記錄",
        "ck_snap_tray":   "啟動時貼齊右下角",
        "entry_refresh":  "更新間隔（秒）",
        "entry_mem_smp":  "記憶體取樣間隔（秒）",
        "lbl_triggers":   "觸發設定",
        "ck_pop_codex":   "新 Codex 完成時彈出",
        "ck_pop_goal":    "目標完成時彈出",
        "ck_pop_final":   "最後回應完成後彈出",
        "entry_delay":    "彈出延遲（秒）",
        "ck_pop_claude":  "新 Claude 完成時彈出",
        "entry_idle":     "Claude 閒置秒數",
        "lbl_language":   "語言 / Language",
        "save_hint":      "設定已儲存至 config.json。",
        "btn_test_codex": "⚙ 測試 Codex",
        "btn_test_claude":"⚙ 測試 Claude",
        "btn_save":       "儲存",
        # main window overlays
        "done_codex":     "完成！Codex 任務結束。",
        "done_claude":    "完成！Claude 工作階段結束。",
        "eng_on":         "⚙ 工程師模式 已開啟",
        "eng_off":        "⚙ 工程師模式 已關閉",
        "not_connected":  "未連線",
        # data labels
        "lbl_today_io":   "今日輸入/輸出：",
        "lbl_today_tot":  "今日合計：     ",
        "lbl_cache_rsn":  "快取/推理：    ",
        "lbl_all_tok":    "總計代幣：     ",
        "lbl_latest":     "最後 ",
        "lbl_cl_today":   "今日合計：",
        "lbl_io_cache":   "輸入/輸出/快取：",
        "lbl_month":      "月合計：  ",
        "lbl_mem":        "記憶體 現在/平均/最高：",
        "lbl_mem_smp":    " MB  取樣 ",
    },
}


def get_work_area():
    """Return Windows work area (screen minus taskbar) as a RECT-like object."""
    class _RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
    rect = _RECT()
    try:
        ctypes.windll.user32.SystemParametersInfoW(0x30, 0, ctypes.byref(rect), 0)
    except Exception:
        rect.right, rect.bottom = 1920, 1040
    return rect


def load_config():
    defaults = {
        "codex_logs_db": str(DEFAULT_CODEX_DB),
        "codex_goals_db": str(DEFAULT_CODEX_GOALS_DB),
        "claude_dir": str(DEFAULT_CLAUDE_DIR),
        "claude_exe": str(DEFAULT_CLAUDE_EXE),
        "claude_extra_dirs": [],
        "refresh_seconds": 5,
        "always_on_top": True,
        "language": "en",
        "snap_to_tray": False,
        "trigger_finish_popup_on_new_codex_completion": False,
        "trigger_finish_popup_on_goal_complete": True,
        "trigger_finish_popup_on_final_response": True,
        "finish_popup_delay_seconds": 3,
        "trigger_claude_popup_on_new_completion": False,
        "claude_idle_seconds": 30,
        "finish_signal_file": str(APP_DIR / "finish.signal"),
        "theme": DEFAULT_THEME,
        "memory_log_enabled": True,
        "memory_sample_seconds": 300,
        "memory_log_dir": str(APP_DIR / "logs"),
    }
    if CONFIG_PATH.exists():
        try:
            config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            changed = False
            for key, value in defaults.items():
                if key not in config:
                    config[key] = value
                    changed = True
            if changed:
                save_config(config)
            return config
        except Exception:
            pass
    save_config(defaults)
    return defaults


def save_config(config):
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


def expand_path(value):
    if not value:
        return Path()
    text = str(value)
    if text == "finish.signal":
        return APP_DIR / "finish.signal"
    if text == "logs":
        return APP_DIR / "logs"
    return Path(os_path_expand(text))


def os_path_expand(value):
    import os

    return os.path.expandvars(os.path.expanduser(value))


def available_themes():
    themes = []
    plugins_dir = APP_DIR / "plugins"
    if plugins_dir.exists():
        for path in sorted(plugins_dir.iterdir()):
            manifest = path / "pet_theme.json"
            if not manifest.exists():
                continue
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                name = data.get("name", path.name)
            except Exception:
                name = path.name
            themes.append({"id": path.name, "name": name})
    return themes


def human(n):
    try:
        n = int(n)
    except Exception:
        return "-"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def today_bounds():
    now = datetime.now()
    start = datetime(now.year, now.month, now.day)
    return int(start.timestamp()), int(time.time())


def month_bounds():
    now = datetime.now()
    start = datetime(now.year, now.month, 1)
    return int(start.timestamp()), int(time.time())


class PetTheme:
    def __init__(self, theme_id, data):
        self.theme_id = theme_id
        self.name = data.get("name", theme_id)
        self.pixel_size = int(data.get("pixel_size", PIXEL))
        self.origin = data.get("origin", {"x": 18, "y": 16})
        self.palette = data.get("palette", {})
        self.animations = data.get("animations", {})
        self.speech = data.get("speech", {})

    @classmethod
    def load(cls, config):
        theme_id = config.get("theme", DEFAULT_THEME)
        path = APP_DIR / "plugins" / theme_id / "pet_theme.json"
        if not path.exists():
            path = APP_DIR / "plugins" / DEFAULT_THEME / "pet_theme.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(path.parent.name, data)
        except Exception:
            return cls("built_in", cls.built_in())

    @staticmethod
    def built_in():
        return {
            "name": "Built-in Pixel Blob",
            "pixel_size": PIXEL,
            "origin": {"x": 18, "y": 16},
            "palette": {
                "outline": "#5a3d7a",
                "body": "#c9a8ff",
                "eye": "#231b2e",
                "cheek": "#ff8bd4",
            },
            "animations": {
                "idle": {
                    "blink_every": 26,
                    "blink_frames": [0, 1],
                    "bob_every": 18,
                    "bob_frames": 9,
                    "frames": [
                        [
                            "0011111100",
                            "0112222210",
                            "1122222221",
                            "1222323221",
                            "1222222221",
                            "1222442221",
                            "0122222210",
                            "0012112100",
                            "0001001000",
                        ]
                    ],
                }
            },
            "speech": {
                "title": "PIXEL TOKEN PET",
                "hint": "right click menu / dblclick done",
                "done_title": "DONE!",
                "done_body": "Codex finished the task.",
            },
        }

    def speech_text(self, key, fallback):
        value = self.speech.get(key)
        return value if isinstance(value, str) and value else fallback

    def idle_frame(self, frame):
        idle = self.animations.get("idle", {})
        frames = idle.get("frames") or self.built_in()["animations"]["idle"]["frames"]
        base = frames[(frame // 8) % len(frames)]
        blink_every = int(idle.get("blink_every", 0) or 0)
        blink_frames = set(idle.get("blink_frames", []))
        blink = blink_every > 0 and (frame % blink_every) in blink_frames
        bob_every = int(idle.get("bob_every", 0) or 0)
        bob_frames = int(idle.get("bob_frames", 0) or 0)
        bob = 1 if bob_every > 0 and (frame % bob_every) < bob_frames else 0
        return base, blink, bob

    def color_for(self, symbol, blink=False):
        if symbol in ("0", " ", "."):
            return None
        if blink and symbol == "3":
            return BG
        aliases = {"1": "outline", "2": "body", "3": "eye", "4": "cheek"}
        key = aliases.get(symbol, symbol)
        return self.palette.get(key, key if key.startswith("#") else INK)


class UsageReader:
    token_re = {
        "input": re.compile(r"input_token_count=(\d+)"),
        "output": re.compile(r"output_token_count=(\d+)"),
        "cached": re.compile(r"cached_token_count=(\d+)"),
        "reasoning": re.compile(r"reasoning_token_count=(\d+)"),
        "tool": re.compile(r"tool_token_count=(\d+)"),
        "model": re.compile(r"model=([^\s]+)"),
    }

    def __init__(self, config):
        self.config = config
        self._claude_version_cache = None

    def codex(self):
        db = expand_path(self.config.get("codex_logs_db", DEFAULT_CODEX_DB))
        empty = {
            "ok": False,
            "source": str(db),
            "today": {"input": 0, "output": 0, "cached": 0, "reasoning": 0, "tool": 0, "total": 0, "calls": 0},
            "all": {"input": 0, "output": 0, "cached": 0, "reasoning": 0, "tool": 0, "total": 0, "calls": 0},
            "latest_id": 0,
            "latest_model": "-",
            "latest_time": "-",
            "error": "",
        }
        if not db.exists():
            empty["error"] = "Codex log DB not found"
            return empty

        start, _ = today_bounds()
        try:
            uri = f"file:{db.as_posix()}?mode=ro"
            con = sqlite3.connect(uri, uri=True, timeout=1)
            rows = con.execute(
                """
                select id, ts, feedback_log_body
                from logs
                where feedback_log_body like '%response.completed%'
                  and feedback_log_body like '%usage%'
                order by id asc
                """
            ).fetchall()
            con.close()
        except Exception as exc:
            empty["error"] = str(exc)
            return empty

        totals = empty["all"].copy()
        today = empty["today"].copy()
        latest_model = "-"
        latest_time = "-"
        latest_id = 0

        seen = set()
        for row_id, ts, body in rows:
            parsed = self._parse_codex_completion(body or "")
            if not parsed:
                continue
            response_id = parsed.get("id") or f"row:{row_id}"
            if response_id in seen:
                continue
            seen.add(response_id)

            usage = parsed.get("usage") or {}
            input_details = usage.get("input_tokens_details") or {}
            output_details = usage.get("output_tokens_details") or {}
            item = {
                "input": int(usage.get("input_tokens") or 0),
                "output": int(usage.get("output_tokens") or 0),
                "cached": int(input_details.get("cached_tokens") or 0),
                "reasoning": int(output_details.get("reasoning_tokens") or 0),
                "tool": 0,
                "total": int(usage.get("total_tokens") or 0),
                "calls": 1,
            }

            for key in totals:
                totals[key] += item.get(key, 0)
            if ts >= start:
                for key in today:
                    today[key] += item.get(key, 0)

            latest_model = parsed.get("model") or latest_model
            latest_time = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
            latest_id = max(latest_id, row_id)

        return {
            "ok": True,
            "source": str(db),
            "today": today,
            "all": totals,
            "latest_id": latest_id,
            "latest_model": latest_model,
            "latest_time": latest_time,
            "error": "",
        }

    def codex_goal_state(self):
        db = expand_path(self.config.get("codex_goals_db", DEFAULT_CODEX_GOALS_DB))
        state = {
            "ok": False,
            "latest_completed_key": "",
            "latest_status": "",
            "latest_objective": "",
            "updated_at_ms": 0,
            "error": "",
        }
        if not db.exists():
            state["error"] = "Codex goals DB not found"
            return state
        try:
            uri = f"file:{db.as_posix()}?mode=ro"
            con = sqlite3.connect(uri, uri=True, timeout=1)
            row = con.execute(
                """
                select thread_id, goal_id, objective, status, updated_at_ms
                from thread_goals
                where status = 'complete'
                order by updated_at_ms desc
                limit 1
                """
            ).fetchone()
            con.close()
        except Exception as exc:
            state["error"] = str(exc)
            return state
        state["ok"] = True
        if row:
            thread_id, goal_id, objective, status, updated_at_ms = row
            state["latest_completed_key"] = f"{thread_id}:{goal_id}:{updated_at_ms}"
            state["latest_status"] = status
            state["latest_objective"] = objective
            state["updated_at_ms"] = int(updated_at_ms or 0)
        return state

    def codex_turn_activity(self):
        db = expand_path(self.config.get("codex_logs_db", DEFAULT_CODEX_DB))
        state = {
            "ok": False,
            "latest_response_id": 0,
            "latest_command_id": 0,
            "error": "",
        }
        if not db.exists():
            state["error"] = "Codex log DB not found"
            return state
        try:
            uri = f"file:{db.as_posix()}?mode=ro"
            con = sqlite3.connect(uri, uri=True, timeout=1)
            response_row = con.execute(
                """
                select id
                from logs
                where feedback_log_body like '%response.completed%'
                  and feedback_log_body not like '%response.function_call_arguments.done%'
                order by id desc
                limit 1
                """
            ).fetchone()
            command_row = con.execute(
                """
                select id
                from logs
                where feedback_log_body like '%commandExecution%'
                  and feedback_log_body like '%item/started%'
                  and feedback_log_body not like '%response.function_call_arguments.done%'
                order by id desc
                limit 1
                """
            ).fetchone()
            con.close()
        except Exception as exc:
            state["error"] = str(exc)
            return state

        state["ok"] = True
        state["latest_response_id"] = int(response_row[0] if response_row else 0)
        state["latest_command_id"] = int(command_row[0] if command_row else 0)
        return state

    def _parse_codex_completion(self, body):
        for marker in ("websocket event: ", "Received message "):
            idx = body.find(marker)
            if idx >= 0:
                raw = body[idx + len(marker) :].strip()
                parsed = self._loads_json_prefix(raw)
                if parsed:
                    break
        else:
            return None

        if not isinstance(parsed, dict):
            return None
        response = parsed.get("response")
        if not response and parsed.get("type") == "response.completed":
            response = parsed.get("response")
        if not response:
            return None
        if response.get("status") != "completed":
            return None
        if not response.get("usage"):
            return None
        return response

    @staticmethod
    def _loads_json_prefix(text):
        decoder = json.JSONDecoder()
        try:
            obj, _ = decoder.raw_decode(text)
            return obj
        except Exception:
            return None

    def claude(self):
        result = {
            "ok": False,
            "source": "",
            "today": {"input": 0, "output": 0, "cached": 0, "total": 0, "calls": 0, "cost": 0.0},
            "month": {"input": 0, "output": 0, "cached": 0, "total": 0, "calls": 0, "cost": 0.0},
            "note": "No Claude usage source found",
            "installed": False,
            "version": "",
        }

        ccusage = self._run(["ccusage", "daily", "--json"])
        if ccusage:
            try:
                parsed = self._parse_ccusage_daily(json.loads(ccusage))
                if parsed["ok"]:
                    result.update(parsed)
                    return result
            except Exception:
                result["note"] = "ccusage exists, but JSON shape was not recognized"

        claude_dir = expand_path(self.config.get("claude_dir", DEFAULT_CLAUDE_DIR))
        claude_exe = expand_path(self.config.get("claude_exe", DEFAULT_CLAUDE_EXE))
        if claude_exe.exists():
            result["installed"] = True
            if self._claude_version_cache is None:
                version = self._run([str(claude_exe), "--version"])
                self._claude_version_cache = version.strip() if version else "installed"
            result["version"] = self._claude_version_cache

        candidates = self._candidate_claude_dirs(claude_dir)
        result["source"] = "; ".join(str(path) for path in candidates)
        seen_files = 0
        for candidate in candidates:
            if not candidate.exists():
                continue
            jsonl_usage = self._read_claude_jsonl_usage(candidate)
            seen_files += jsonl_usage["seen_files"]
            if jsonl_usage["ok"]:
                jsonl_usage["installed"] = result["installed"]
                jsonl_usage["version"] = result["version"]
                result.update(jsonl_usage)
                return result
        if result["installed"]:
            result["ok"] = True
            result["source"] = str(claude_exe)
            result["note"] = f"Claude Code {result['version']}, no token logs found in {len(candidates)} locations"
        elif any(path.exists() for path in candidates):
            result["note"] = f"Claude folders found, no token usage in {seen_files} JSONL files"
        return result

    def _parse_ccusage_daily(self, data):
        result = {
            "ok": False,
            "source": "ccusage",
            "today": {"input": 0, "output": 0, "cached": 0, "total": 0, "calls": 0, "cost": 0.0},
            "month": {"input": 0, "output": 0, "cached": 0, "total": 0, "calls": 0, "cost": 0.0},
            "note": "",
        }
        today_key = datetime.now().strftime("%Y-%m-%d")
        month_key = datetime.now().strftime("%Y-%m")
        rows = data.get("daily", data if isinstance(data, list) else [])
        if not isinstance(rows, list):
            return result

        for row in rows:
            if not isinstance(row, dict):
                continue
            date = str(row.get("date", ""))
            cache_create = int(row.get("cacheCreationTokens", row.get("cache_creation_input_tokens", 0)) or 0)
            cache_read = int(row.get("cacheReadTokens", row.get("cache_read_input_tokens", 0)) or 0)
            item = {
                "input": int(row.get("inputTokens", row.get("input_tokens", 0)) or 0),
                "output": int(row.get("outputTokens", row.get("output_tokens", 0)) or 0),
                "cached": cache_create + cache_read,
                "total": int(row.get("totalTokens", row.get("tokens", 0)) or 0),
                "cost": float(row.get("totalCost", row.get("cost", 0)) or 0),
            }
            if item["total"] <= 0:
                item["total"] = item["input"] + item["output"] + item["cached"]
            if item["total"] <= 0:
                continue
            item["calls"] = int(row.get("requests", row.get("calls", 1)) or 1)
            if date.startswith(month_key):
                self._add_usage(result["month"], item)
            if date.startswith(today_key):
                self._add_usage(result["today"], item)

        result["ok"] = result["today"]["total"] > 0 or result["month"]["total"] > 0
        return result

    def _candidate_claude_dirs(self, configured_dir):
        candidates = [configured_dir]
        for raw in self.config.get("claude_extra_dirs", []) or []:
            candidates.append(expand_path(raw))

        env_paths = self._claude_env_dirs()
        candidates.extend(env_paths)

        unique = []
        seen = set()
        for path in candidates:
            try:
                key = str(path.resolve() if path.exists() else path)
            except Exception:
                key = str(path)
            if key not in seen:
                seen.add(key)
                unique.append(path)
        return unique

    @staticmethod
    def _claude_env_dirs():
        import os

        paths = [Path.home() / ".claude"]
        appdata = os.environ.get("APPDATA")
        if appdata:
            paths.append(Path(appdata) / "Claude")
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            local = Path(local_appdata)
            paths.extend([local / "Claude", local / "Claude-3p"])
            packages = local / "Packages"
            if packages.exists():
                try:
                    for package in packages.glob("Claude_*"):
                        paths.append(package / "LocalCache" / "Roaming" / "Claude")
                except Exception:
                    pass
        return paths

    def _read_claude_jsonl_usage(self, claude_dir):
        search_root = claude_dir / "projects" if (claude_dir / "projects").exists() else claude_dir
        result = {
            "ok": False,
            "source": str(search_root),
            "today": {"input": 0, "output": 0, "cached": 0, "total": 0, "calls": 0, "cost": 0.0},
            "month": {"input": 0, "output": 0, "cached": 0, "total": 0, "calls": 0, "cost": 0.0},
            "note": "",
            "seen_files": 0,
        }
        if not search_root.exists():
            return result

        today_start, _ = today_bounds()
        month_start, _ = month_bounds()
        seen_ids = set()
        files = list(search_root.rglob("*.jsonl"))
        result["seen_files"] = len(files)

        for path in files:
            try:
                with path.open("r", encoding="utf-8", errors="ignore") as handle:
                    for line in handle:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            event = json.loads(line)
                        except Exception:
                            continue
                        parsed = self._parse_claude_event(event)
                        if not parsed:
                            continue
                        key = parsed.get("id") or f"{path}:{parsed['ts']}:{parsed['input']}:{parsed['output']}"
                        if key in seen_ids:
                            continue
                        seen_ids.add(key)
                        if parsed["ts"] >= month_start:
                            self._add_usage(result["month"], parsed)
                        if parsed["ts"] >= today_start:
                            self._add_usage(result["today"], parsed)
            except Exception:
                continue

        result["ok"] = bool(seen_ids)
        result["note"] = "" if result["ok"] else f"Claude projects found, no token usage in {len(files)} JSONL files"
        return result

    @staticmethod
    def _add_usage(bucket, item):
        bucket["input"] += item["input"]
        bucket["output"] += item["output"]
        bucket["cached"] += item["cached"]
        bucket["total"] += item["total"]
        bucket["calls"] += int(item.get("calls", 1) or 1)
        bucket["cost"] += item["cost"]

    @staticmethod
    def _parse_claude_event(event):
        message = event.get("message") if isinstance(event.get("message"), dict) else event
        usage = message.get("usage") if isinstance(message, dict) else None
        if not isinstance(usage, dict):
            return None

        ts_raw = event.get("timestamp") or event.get("created_at") or message.get("timestamp")
        ts = UsageReader._parse_timestamp(ts_raw)
        if not ts:
            return None

        input_tokens = int(usage.get("input_tokens") or 0)
        output_tokens = int(usage.get("output_tokens") or 0)
        cache_create = int(usage.get("cache_creation_input_tokens") or 0)
        cache_read = int(usage.get("cache_read_input_tokens") or 0)
        cached = cache_create + cache_read
        total = input_tokens + output_tokens + cached
        if total <= 0:
            return None

        cost = float(event.get("costUSD") or event.get("cost_usd") or message.get("costUSD") or 0.0)
        return {
            "id": event.get("uuid") or event.get("id") or message.get("id"),
            "ts": ts,
            "input": input_tokens,
            "output": output_tokens,
            "cached": cached,
            "total": total,
            "cost": cost,
        }

    @staticmethod
    def _parse_timestamp(value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return int(value / 1000) if value > 10_000_000_000 else int(value)
        if isinstance(value, str):
            text = value.strip().replace("Z", "+00:00")
            try:
                return int(datetime.fromisoformat(text).timestamp())
            except Exception:
                return None
        return None

    @staticmethod
    def _run(args):
        try:
            startupinfo = None
            creationflags = 0
            if sys.platform.startswith("win"):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            proc = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=5,
                shell=False,
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout
        except Exception:
            return ""
        return ""


class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


class MemoryMonitor:
    def __init__(self, config):
        self.enabled = bool(config.get("memory_log_enabled", True))
        self.interval_seconds = max(30, int(config.get("memory_sample_seconds", 300)))
        self.log_dir = expand_path(config.get("memory_log_dir", APP_DIR / "logs"))
        self.last_sample = None

    def sample(self):
        now = datetime.now()
        data = {
            "timestamp": now.isoformat(timespec="seconds"),
            "rss_bytes": 0,
            "private_bytes": 0,
            "peak_rss_bytes": 0,
        }
        if sys.platform.startswith("win"):
            counters = PROCESS_MEMORY_COUNTERS_EX()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS_EX)
            psapi = ctypes.WinDLL("psapi.dll")
            kernel32 = ctypes.WinDLL("kernel32.dll")
            psapi.GetProcessMemoryInfo.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(PROCESS_MEMORY_COUNTERS_EX),
                wintypes.DWORD,
            ]
            psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            handle = kernel32.GetCurrentProcess()
            ok = psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
            if ok:
                data["rss_bytes"] = int(counters.WorkingSetSize)
                data["private_bytes"] = int(counters.PrivateUsage)
                data["peak_rss_bytes"] = int(counters.PeakWorkingSetSize)
        self.last_sample = data
        return data

    def record(self):
        if not self.enabled:
            return self.sample()
        data = self.sample()
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            day = datetime.now().strftime("%Y-%m-%d")
            path = self.log_dir / f"memory-{day}.jsonl"
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(data, ensure_ascii=False) + "\n")
        except Exception:
            pass
        return data

    def today_summary(self):
        day = datetime.now().strftime("%Y-%m-%d")
        path = self.log_dir / f"memory-{day}.jsonl"
        samples = []
        if path.exists():
            try:
                with path.open("r", encoding="utf-8", errors="ignore") as handle:
                    for line in handle:
                        try:
                            item = json.loads(line)
                        except Exception:
                            continue
                        if item.get("rss_bytes"):
                            samples.append(item)
            except Exception:
                pass
        if (
            self.last_sample
            and self.last_sample.get("rss_bytes")
            and not any(item.get("timestamp") == self.last_sample.get("timestamp") for item in samples)
        ):
            samples.append(self.last_sample)
        if not samples:
            return {"samples": 0, "current_mb": 0, "avg_mb": 0, "max_mb": 0, "private_mb": 0}
        rss_values = [item["rss_bytes"] for item in samples]
        private = samples[-1].get("private_bytes", 0)
        return {
            "samples": len(samples),
            "current_mb": round(rss_values[-1] / 1024 / 1024, 1),
            "avg_mb": round((sum(rss_values) / len(rss_values)) / 1024 / 1024, 1),
            "max_mb": round(max(rss_values) / 1024 / 1024, 1),
            "private_mb": round(private / 1024 / 1024, 1),
        }


class _TrayIcon:
    """Minimal Windows system-tray icon using Shell_NotifyIcon + WndProc subclass."""

    _WM_TRAYICON = 0x0401      # WM_USER + 1 — our private callback message
    _NIM_ADD = 0
    _NIM_DELETE = 2
    _NIF_MESSAGE = 0x1
    _NIF_ICON = 0x2
    _NIF_TIP = 0x4
    _IDI_APPLICATION = 32512
    _GWLP_WNDPROC = -4
    _WM_LBUTTONUP = 0x0202
    _WM_LBUTTONDBLCLK = 0x0203

    class _NID(ctypes.Structure):
        _fields_ = [
            ("cbSize",          wintypes.DWORD),
            ("hWnd",            wintypes.HWND),
            ("uID",             wintypes.UINT),
            ("uFlags",          wintypes.UINT),
            ("uCallbackMessage",wintypes.UINT),
            ("hIcon",           wintypes.HICON),
            ("szTip",           ctypes.c_wchar * 128),
        ]

    def __init__(self, hwnd, on_restore):
        self._hwnd = hwnd
        self._on_restore = on_restore
        self._proc_ref = None   # must stay alive while registered
        self._old_proc = None
        self._active = False

    def show(self):
        if self._active:
            return
        u32 = ctypes.windll.user32
        hicon = u32.LoadIconW(None, self._IDI_APPLICATION)
        nid = self._NID()
        nid.cbSize = ctypes.sizeof(self._NID)
        nid.hWnd = self._hwnd
        nid.uID = 1
        nid.uFlags = self._NIF_MESSAGE | self._NIF_ICON | self._NIF_TIP
        nid.uCallbackMessage = self._WM_TRAYICON
        nid.hIcon = hicon
        nid.szTip = "Pixel Token Pet"
        ctypes.windll.shell32.Shell_NotifyIconW(self._NIM_ADD, ctypes.byref(nid))

        # Subclass the window's WndProc to intercept tray callback messages.
        try:
            get_ptr = u32.GetWindowLongPtrW
            set_ptr = u32.SetWindowLongPtrW
        except AttributeError:
            get_ptr = u32.GetWindowLongW
            set_ptr = u32.SetWindowLongW
        get_ptr.restype = ctypes.c_ssize_t
        set_ptr.restype = ctypes.c_ssize_t

        old = get_ptr(self._hwnd, self._GWLP_WNDPROC)
        self._old_proc = old

        WM = self._WM_TRAYICON
        LBU = self._WM_LBUTTONUP
        LBD = self._WM_LBUTTONDBLCLK
        restore = self._on_restore

        PFUNC = ctypes.WINFUNCTYPE(
            ctypes.c_ssize_t,
            wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
        )

        @PFUNC
        def _proc(hwnd, msg, wp, lp):
            if msg == WM and lp in (LBU, LBD):
                restore()
                return 0
            return u32.CallWindowProcW(old, hwnd, msg, wp, lp)

        self._proc_ref = _proc
        set_ptr(self._hwnd, self._GWLP_WNDPROC, _proc)
        self._active = True

    def hide(self):
        if not self._active:
            return
        nid = self._NID()
        nid.cbSize = ctypes.sizeof(self._NID)
        nid.hWnd = self._hwnd
        nid.uID = 1
        ctypes.windll.shell32.Shell_NotifyIconW(self._NIM_DELETE, ctypes.byref(nid))
        try:
            u32 = ctypes.windll.user32
            try:
                set_ptr = u32.SetWindowLongPtrW
            except AttributeError:
                set_ptr = u32.SetWindowLongW
            set_ptr.restype = ctypes.c_ssize_t
            set_ptr(self._hwnd, self._GWLP_WNDPROC, self._old_proc)
        except Exception:
            pass
        self._proc_ref = None
        self._active = False


class PixelPet:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.reader = UsageReader(self.config)
        self.theme = PetTheme.load(self.config)
        self.memory = MemoryMonitor(self.config)
        self.memory_data = self.memory.record()
        self.last_codex_completion = 0
        self.last_completed_goal_key = ""
        self.last_final_response_id = 0
        self.last_claude_calls = 0
        self.pending_final_response = None
        self._pending_claude_popup = None
        self.last_signal_mtime = 0
        self.frame = 0
        self.drag = None
        self.message_until = 0
        self.done_label = ""
        self.settings_window = None
        self.compact = False
        self.engineer_mode = False
        self._gear_clicks = []
        self._tray = None
        self.gear_box = (330, 14, 352, 36)
        self.close_box = (10, 14, 32, 36)

        root.title("Pixel Token Pet")
        if self.config.get("snap_to_tray", False):
            rect = get_work_area()
            sx = rect.right - NORMAL_W - 4
            sy = rect.bottom - NORMAL_H - 4
            root.geometry(f"{NORMAL_W}x{NORMAL_H}+{sx}+{sy}")
        else:
            root.geometry(f"{NORMAL_W}x{NORMAL_H}+120+120")
        root.configure(bg=BG)
        root.overrideredirect(True)
        root.attributes("-topmost", bool(self.config.get("always_on_top", True)))

        self.canvas = tk.Canvas(root, width=NORMAL_W, height=NORMAL_H, highlightthickness=0, bg=BG)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        self.canvas.bind("<Double-Button-1>", lambda _e: self.finish_popup())
        self.canvas.bind("<Button-3>", self.show_menu)
        root.bind("<Destroy>", lambda _e: self._cleanup_tray())

        self.menu = tk.Menu(root, tearoff=0)
        self._rebuild_menu()

        self.codex_data = self.reader.codex()
        self.claude_data = self.reader.claude()
        self.goal_state = self.reader.codex_goal_state()
        self.turn_activity = self.reader.codex_turn_activity()
        self.last_codex_completion = self.codex_data.get("latest_id", 0)
        self.last_completed_goal_key = self.goal_state.get("latest_completed_key", "")
        self.last_final_response_id = self.turn_activity.get("latest_response_id", 0)
        self.last_claude_calls = self.claude_data.get("today", {}).get("calls", 0)
        self.refresh()
        self.record_memory()
        self.animate()

    def t(self, key):
        lang = self.config.get("language", "en")
        table = _LANG.get(lang, _LANG["en"])
        return table.get(key, _LANG["en"].get(key, key))

    # ── drag & hit testing ──────────────────────────────────────────────────

    def start_drag(self, event):
        if self.is_close_hit(event.x, event.y):
            self.root.destroy()
            return "break"
        if self.is_gear_hit(event.x, event.y):
            now = time.time()
            self._gear_clicks = [t for t in self._gear_clicks if now - t < 3.0]
            self._gear_clicks.append(now)
            if len(self._gear_clicks) >= 5:
                self._gear_clicks = []
                self._toggle_engineer_mode()
            else:
                self.open_settings()
            self.drag = None
            return "break"
        self.drag = (event.x_root, event.y_root, self.root.winfo_x(), self.root.winfo_y())

    def do_drag(self, event):
        if not self.drag:
            return
        x0, y0, win_x, win_y = self.drag
        self.root.geometry(f"+{win_x + event.x_root - x0}+{win_y + event.y_root - y0}")

    def show_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def is_gear_hit(self, x, y):
        x1, y1, x2, y2 = self.gear_box
        return x1 <= x <= x2 and y1 <= y <= y2

    def is_close_hit(self, x, y):
        x1, y1, x2, y2 = self.close_box
        return x1 <= x <= x2 and y1 <= y <= y2

    # ── menu / engineer mode / tray ─────────────────────────────────────────

    def _rebuild_menu(self):
        self.menu.delete(0, "end")
        compact_label = self.t("full_view") if self.compact else self.t("compact_view")
        self.menu.add_command(label=compact_label, command=self.toggle_compact)
        self.menu.add_command(label=self.t("min_to_tray"), command=self.minimize_to_tray)
        self.menu.add_command(label=self.t("snap_tray"), command=self.snap_to_tray)
        self.menu.add_separator()
        if self.engineer_mode:
            self.menu.add_command(label=self.t("eng_done_anim"), command=self.finish_popup)
            self.menu.add_command(label=self.t("eng_claude_pop"), command=self.claude_popup)
            self.menu.add_separator()
        self.menu.add_command(label=self.t("refresh"), command=self.refresh)
        self.menu.add_separator()
        self.menu.add_command(label=self.t("close_pet"), command=self.root.destroy)

    def _toggle_engineer_mode(self):
        self.engineer_mode = not self.engineer_mode
        self._rebuild_menu()
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.destroy()
        self.done_label = self.t("eng_on") if self.engineer_mode else self.t("eng_off")
        self.message_until = time.time() + 2.5
        self.draw()

    def snap_to_tray(self):
        rect = get_work_area()
        h = COMPACT_H if self.compact else NORMAL_H
        x = rect.right - NORMAL_W - 4
        y = rect.bottom - h - 4
        self.root.geometry(f"{NORMAL_W}x{h}+{x}+{y}")

    def minimize_to_tray(self):
        self.root.update_idletasks()
        hwnd = ctypes.windll.user32.FindWindowW(None, "Pixel Token Pet")
        if hwnd and self._tray is None:
            self._tray = _TrayIcon(hwnd, self._restore_from_tray)
        if self._tray:
            self._tray.show()
        self.root.withdraw()

    def _restore_from_tray(self):
        if self._tray:
            self._tray.hide()
            self._tray = None
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", bool(self.config.get("always_on_top", True)))

    def _cleanup_tray(self):
        if self._tray:
            try:
                self._tray.hide()
            except Exception:
                pass
            self._tray = None

    # ── compact toggle ──────────────────────────────────────────────────────

    def toggle_compact(self):
        self.compact = not self.compact
        wx, wy = self.root.winfo_x(), self.root.winfo_y()
        h = COMPACT_H if self.compact else NORMAL_H
        self.root.geometry(f"{NORMAL_W}x{h}+{wx}+{wy}")
        self._rebuild_menu()
        self.draw()

    # ── settings panel ──────────────────────────────────────────────────────

    def open_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return

        win = tk.Toplevel(self.root)
        self.settings_window = win
        win.title(self.t("settings_title"))
        win.configure(bg=BG)
        win.attributes("-topmost", bool(self.config.get("always_on_top", True)))
        win.resizable(False, False)
        wx = self.root.winfo_x() + self.root.winfo_width() + 8
        wy = self.root.winfo_y()
        win_h = 490 if self.engineer_mode else 470
        win.geometry(f"380x{win_h}+{wx}+{wy}")

        theme_options = available_themes()
        theme_ids = [item["id"] for item in theme_options] or [DEFAULT_THEME]

        selected_theme = tk.StringVar(value=self.config.get("theme", DEFAULT_THEME))
        always_top = tk.BooleanVar(value=bool(self.config.get("always_on_top", True)))
        memory_enabled = tk.BooleanVar(value=bool(self.config.get("memory_log_enabled", True)))
        refresh_seconds = tk.StringVar(value=str(self.config.get("refresh_seconds", 5)))
        memory_seconds = tk.StringVar(value=str(self.config.get("memory_sample_seconds", 300)))
        pop_new_codex = tk.BooleanVar(value=bool(self.config.get("trigger_finish_popup_on_new_codex_completion", False)))
        pop_goal = tk.BooleanVar(value=bool(self.config.get("trigger_finish_popup_on_goal_complete", True)))
        pop_final = tk.BooleanVar(value=bool(self.config.get("trigger_finish_popup_on_final_response", True)))
        popup_delay = tk.StringVar(value=str(self.config.get("finish_popup_delay_seconds", 3)))
        pop_claude = tk.BooleanVar(value=bool(self.config.get("trigger_claude_popup_on_new_completion", False)))
        claude_idle = tk.StringVar(value=str(self.config.get("claude_idle_seconds", 30)))
        snap_tray = tk.BooleanVar(value=bool(self.config.get("snap_to_tray", False)))
        lang_var = tk.StringVar(value=self.config.get("language", "en"))

        body = tk.Frame(win, bg=BG, padx=14, pady=12)
        body.pack(fill="both", expand=True)

        ck = dict(bg=BG, fg=INK, activebackground=BG, activeforeground=INK, selectcolor=PANEL, font=("Consolas", 9))

        # Language selector (always at top, always in bilingual label)
        lang_row = tk.Frame(body, bg=BG)
        lang_row.pack(fill="x", pady=(0, 8))
        tk.Label(lang_row, text=_LANG["zh"]["lbl_language"], bg=BG, fg=YELLOW,
                 font=("Consolas", 9, "bold"), anchor="w").pack(side="left")
        for code, label in (("en", "English"), ("zh", "中文")):
            tk.Radiobutton(lang_row, text=label, variable=lang_var, value=code,
                           bg=BG, fg=INK, activebackground=BG, activeforeground=INK,
                           selectcolor=PANEL, font=("Consolas", 9)).pack(side="left", padx=(8, 0))

        self.settings_label(body, self.t("lbl_theme"))
        theme_menu = tk.OptionMenu(body, selected_theme, *theme_ids)
        theme_menu.configure(bg=PANEL, fg=INK, activebackground="#383348", activeforeground=INK, highlightthickness=0)
        theme_menu["menu"].configure(bg=PANEL, fg=INK)
        theme_menu.pack(fill="x", pady=(3, 8))

        self.settings_label(body, self.t("lbl_display"))
        tk.Checkbutton(body, text=self.t("ck_always_top"), variable=always_top, **ck).pack(anchor="w")
        tk.Checkbutton(body, text=self.t("ck_memory_log"), variable=memory_enabled, **ck).pack(anchor="w")
        tk.Checkbutton(body, text=self.t("ck_snap_tray"), variable=snap_tray, **ck).pack(anchor="w", pady=(0, 4))
        self.settings_entry(body, self.t("entry_refresh"), refresh_seconds)
        self.settings_entry(body, self.t("entry_mem_smp"), memory_seconds)

        tk.Frame(body, bg=MUTED, height=1).pack(fill="x", pady=(10, 4))
        self.settings_label(body, self.t("lbl_triggers"))
        tk.Checkbutton(body, text=self.t("ck_pop_codex"), variable=pop_new_codex, **ck).pack(anchor="w")
        tk.Checkbutton(body, text=self.t("ck_pop_goal"), variable=pop_goal, **ck).pack(anchor="w")
        tk.Checkbutton(body, text=self.t("ck_pop_final"), variable=pop_final, **ck).pack(anchor="w", pady=(0, 4))
        self.settings_entry(body, self.t("entry_delay"), popup_delay)
        tk.Frame(body, bg="#383348", height=1).pack(fill="x", pady=(6, 4))
        tk.Checkbutton(body, text=self.t("ck_pop_claude"), variable=pop_claude, **ck).pack(anchor="w")
        self.settings_entry(body, self.t("entry_idle"), claude_idle)

        tk.Frame(body, bg=MUTED, height=1).pack(fill="x", pady=(8, 4))
        tk.Label(body, text=self.t("save_hint"), bg=BG, fg=MUTED, font=("Consolas", 8), anchor="w").pack(fill="x", pady=(2, 8))

        actions = tk.Frame(body, bg=BG)
        actions.pack(fill="x")
        if self.engineer_mode:
            tk.Button(actions, text=self.t("btn_test_codex"), command=self.finish_popup, bg=PANEL, fg=INK).pack(side="left")
            tk.Button(actions, text=self.t("btn_test_claude"), command=self.claude_popup, bg=PANEL, fg=CLAUDE_TITLE).pack(side="left", padx=(6, 0))
        tk.Button(actions, text=self.t("btn_save"), command=lambda: save_settings(), bg=PANEL, fg=GREEN).pack(side="right")

        def save_settings():
            try:
                refresh_value = max(1, int(refresh_seconds.get()))
            except Exception:
                refresh_value = 5
            try:
                memory_value = max(30, int(memory_seconds.get()))
            except Exception:
                memory_value = 300
            try:
                delay_value = max(1, int(popup_delay.get()))
            except Exception:
                delay_value = 3

            self.config["theme"] = selected_theme.get()
            self.config["always_on_top"] = bool(always_top.get())
            self.config["memory_log_enabled"] = bool(memory_enabled.get())
            self.config["refresh_seconds"] = refresh_value
            self.config["memory_sample_seconds"] = memory_value
            self.config["trigger_finish_popup_on_new_codex_completion"] = bool(pop_new_codex.get())
            self.config["trigger_finish_popup_on_goal_complete"] = bool(pop_goal.get())
            self.config["trigger_finish_popup_on_final_response"] = bool(pop_final.get())
            self.config["finish_popup_delay_seconds"] = delay_value
            self.config["trigger_claude_popup_on_new_completion"] = bool(pop_claude.get())
            try:
                self.config["claude_idle_seconds"] = max(5, int(claude_idle.get()))
            except Exception:
                self.config["claude_idle_seconds"] = 30
            self.config["snap_to_tray"] = bool(snap_tray.get())
            self.config["language"] = lang_var.get()
            save_config(self.config)

            self.theme = PetTheme.load(self.config)
            self.memory = MemoryMonitor(self.config)
            self.root.attributes("-topmost", bool(self.config.get("always_on_top", True)))
            self._rebuild_menu()
            self.draw()
            win.destroy()

    def settings_label(self, parent, text_value):
        tk.Label(parent, text=text_value, bg=BG, fg=YELLOW, font=("Consolas", 9, "bold"), anchor="w").pack(fill="x")

    def settings_entry(self, parent, label, variable):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=3)
        tk.Label(row, text=label, bg=BG, fg=INK, font=("Consolas", 9), anchor="w").pack(side="left")
        tk.Entry(row, textvariable=variable, width=8, bg=PANEL, fg=INK, insertbackground=INK).pack(side="right")

    # ── data refresh ────────────────────────────────────────────────────────

    def refresh(self):
        old_latest = self.codex_data.get("latest_id", 0) if hasattr(self, "codex_data") else 0
        self.codex_data = self.reader.codex()
        self.claude_data = self.reader.claude()
        self.goal_state = self.reader.codex_goal_state()
        self.turn_activity = self.reader.codex_turn_activity()
        new_latest = self.codex_data.get("latest_id", 0)

        if (
            old_latest
            and new_latest > old_latest
            and self.config.get("trigger_finish_popup_on_new_codex_completion", True)
        ):
            self.finish_popup()

        if self.config.get("trigger_finish_popup_on_goal_complete", True):
            completed_key = self.goal_state.get("latest_completed_key", "")
            if completed_key and self.last_completed_goal_key and completed_key != self.last_completed_goal_key:
                self.finish_popup()
            if completed_key:
                self.last_completed_goal_key = completed_key

        self.check_final_response_completion()
        self.check_finish_signal()
        self.last_codex_completion = new_latest

        new_claude_calls = self.claude_data.get("today", {}).get("calls", 0)
        if self.config.get("trigger_claude_popup_on_new_completion", False):
            if self.last_claude_calls and new_claude_calls > self.last_claude_calls:
                # Reset idle timer — fire only after Claude goes quiet
                idle = max(5, int(self.config.get("claude_idle_seconds", 30)))
                self._pending_claude_popup = time.time() + idle
            if self._pending_claude_popup and time.time() >= self._pending_claude_popup:
                self._pending_claude_popup = None
                self.claude_popup()
        self.last_claude_calls = new_claude_calls

        self.draw()
        self.root.after(int(self.config.get("refresh_seconds", 5)) * 1000, self.refresh)

    def check_final_response_completion(self):
        if not self.config.get("trigger_finish_popup_on_final_response", True):
            return

        response_id = int(self.turn_activity.get("latest_response_id", 0) or 0)
        command_id = int(self.turn_activity.get("latest_command_id", 0) or 0)
        if response_id > self.last_final_response_id:
            delay = max(1, int(self.config.get("finish_popup_delay_seconds", 3)))
            self.pending_final_response = {"id": response_id, "ready_at": time.time() + delay}
            self.last_final_response_id = response_id

        if not self.pending_final_response:
            return

        pending_id = int(self.pending_final_response.get("id", 0))
        ready_at = float(self.pending_final_response.get("ready_at", 0))
        if command_id > pending_id:
            self.pending_final_response = None
            return
        if time.time() >= ready_at:
            self.pending_final_response = None
            self.finish_popup()

    def record_memory(self):
        self.memory_data = self.memory.record()
        self.root.after(self.memory.interval_seconds * 1000, self.record_memory)

    def check_finish_signal(self):
        signal_path = expand_path(self.config.get("finish_signal_file", APP_DIR / "finish.signal"))
        try:
            stat = signal_path.stat()
        except FileNotFoundError:
            return
        except Exception:
            return
        if stat.st_mtime > self.last_signal_mtime:
            self.last_signal_mtime = stat.st_mtime
            self.finish_popup()

    # ── drawing primitives ──────────────────────────────────────────────────

    def rect(self, x, y, w, h, color):
        self.canvas.create_rectangle(x, y, x + w, y + h, fill=color, outline=color)

    def pixel(self, x, y, color):
        size = self.theme.pixel_size
        origin_x = int(self.theme.origin.get("x", 18))
        origin_y = int(self.theme.origin.get("y", 16))
        self.rect(x * size + origin_x, y * size + origin_y, size, size, color)

    def text(self, x, y, msg, color=INK, size=10, anchor="nw"):
        self.canvas.create_text(x, y, text=msg, fill=color, font=("Consolas", size, "bold"), anchor=anchor)

    def draw_pet(self):
        pattern, blink, bob = self.theme.idle_frame(self.frame)
        for y, line in enumerate(pattern):
            for x, ch in enumerate(line):
                color = self.theme.color_for(ch, blink=blink)
                if color:
                    self.pixel(x, y + bob, color)
        self.text(83, 28 + bob * 2, self.theme.speech_text("title", "PIXEL TOKEN PET"), YELLOW, 11)
        self.text(84, 45 + bob * 2, self.theme.speech_text("hint", "right click menu / dblclick done"), MUTED, 7)

    def draw_bar(self, x, y, w, pct, color, label):
        self.rect(x, y, w, 10, "#383348")
        self.rect(x, y, max(2, int(w * min(max(pct, 0), 1))), 10, color)
        self.text(x + w + 8, y - 2, label, MUTED, 8)

    def draw_gear(self):
        x1, y1, x2, y2 = self.gear_box
        self.rect(x1, y1, x2 - x1, y2 - y1, "#383348")
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        for dx, dy in ((0, -8), (0, 8), (-8, 0), (8, 0), (-6, -6), (6, -6), (-6, 6), (6, 6)):
            self.canvas.create_line(cx, cy, cx + dx, cy + dy, fill=YELLOW, width=2)
        self.canvas.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, outline=YELLOW, width=2)
        self.canvas.create_oval(cx - 2, cy - 2, cx + 2, cy + 2, fill=BG, outline=BG)

    def draw_close(self):
        x1, y1, x2, y2 = self.close_box
        self.rect(x1, y1, x2 - x1, y2 - y1, "#383348")
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        m = 5
        self.canvas.create_line(cx - m, cy - m, cx + m, cy + m, fill=RED, width=2)
        self.canvas.create_line(cx + m, cy - m, cx - m, cy + m, fill=RED, width=2)

    def draw_status_dot(self, x, y, ok):
        color = GREEN if ok else RED
        self.canvas.create_oval(x, y, x + 8, y + 8, fill=color, outline="")

    # ── main draw ───────────────────────────────────────────────────────────

    def draw(self):
        if self.compact:
            self._draw_compact()
            return

        self.canvas.delete("all")
        self.rect(0, 0, NORMAL_W, NORMAL_H, BG)
        self.rect(8, 8, NORMAL_W - 16, NORMAL_H - 16, PANEL)
        self.rect(12, 12, NORMAL_W - 24, NORMAL_H - 24, "#17151f")
        self.draw_gear()
        self.draw_close()
        self.draw_pet()

        # ── Codex section ──
        c = self.codex_data
        today = c["today"]
        all_time = c["all"]
        y = 88
        self.draw_status_dot(14, y + 4, c["ok"])
        self.text(27, y, "CODEX", BLUE, 12)
        if c["ok"]:
            self.text(27, y + 20, f"{self.t('lbl_today_io')}{human(today['input'])} / {human(today['output'])}", INK, 10)
            self.text(27, y + 38, f"{self.t('lbl_today_tot')}{human(today['total'])}  calls {today['calls']}", INK, 10)
            self.text(27, y + 56, f"{self.t('lbl_cache_rsn')}{human(today['cached'])} / {human(today['reasoning'])}", MUTED, 9)
            self.text(27, y + 74, f"{self.t('lbl_all_tok')}{human(all_time['total'])}", MUTED, 9)
            self.text(27, y + 92, f"{self.t('lbl_latest')}{c['latest_time']} {c['latest_model']}", GREEN, 9)
            denom = max(today["input"] + today["output"] + today["cached"], 1)
            self.draw_bar(215, y + 23, 80, today["output"] / denom, PINK, "out")
            self.draw_bar(215, y + 45, 80, today["cached"] / denom, BLUE, "cache")
        else:
            self.text(27, y + 24, c["error"], RED, 9)

        # ── separator ──
        self.canvas.create_line(24, 196, NORMAL_W - 24, 196, fill=MUTED, width=1)

        # ── Claude section ──
        cl = self.claude_data
        y = 204
        self.draw_status_dot(14, y + 4, cl["ok"])
        self.text(27, y, "CLAUDE", PINK, 12)
        if cl["ok"]:
            ct = cl["today"]
            cm = cl["month"]
            cost_str = f"  ${ct['cost']:.3f}" if ct.get("cost", 0) > 0.0001 else ""
            self.text(27, y + 20, f"{self.t('lbl_cl_today')}{human(ct['total'])}  calls {ct['calls']}{cost_str}", INK, 10)
            self.text(27, y + 38, f"{self.t('lbl_io_cache')}{human(ct['input'])}/{human(ct['output'])}/{human(ct['cached'])}", MUTED, 8)
            if ct["calls"]:
                month_cost = f"  ${cm['cost']:.3f}" if cm.get("cost", 0) > 0.0001 else ""
                self.text(27, y + 54, f"{self.t('lbl_month')}{human(cm['total'])}{month_cost}", MUTED, 8)
            else:
                self.text(27, y + 54, cl["note"], MUTED, 8)
        else:
            self.text(27, y + 20, self.t("not_connected"), YELLOW, 10)
            self.text(27, y + 38, cl["note"], MUTED, 8)

        # ── memory footer ──
        mem = self.memory.today_summary()
        self.text(
            24, 302,
            f"{self.t('lbl_mem')}{mem['current_mb']}/{mem['avg_mb']}/{mem['max_mb']}{self.t('lbl_mem_smp')}{mem['samples']}",
            MUTED, 8,
        )

        # ── done overlay ──
        if time.time() < self.message_until:
            label_color = GREEN if "Codex" in self.done_label else CLAUDE_TITLE
            self.rect(27, 278, 306, 20, "#3b2440")
            self.text(180, 288, self.done_label or "Done!", label_color, 10, anchor="center")

    def _draw_compact(self):
        self.canvas.delete("all")
        self.rect(0, 0, COMPACT_W, COMPACT_H, BG)
        self.rect(8, 8, COMPACT_W - 16, COMPACT_H - 16, PANEL)
        self.rect(12, 12, COMPACT_W - 24, COMPACT_H - 24, "#17151f")
        self.draw_gear()
        self.draw_close()
        self.draw_pet()

        codex_ok = self.codex_data.get("ok", False)
        claude_ok = self.claude_data.get("ok", False)
        c_today = human(self.codex_data["today"]["total"]) if codex_ok else "-"
        cl_today = human(self.claude_data["today"]["total"]) if claude_ok else "-"
        self.text(24, 68, f"cx {c_today} | cl {cl_today} today", MUTED, 8)

        if time.time() < self.message_until:
            label_color = GREEN if "Codex" in self.done_label else CLAUDE_TITLE
            self.rect(27, 66, 306, 16, "#3b2440")
            self.text(180, 74, self.done_label or "Done!", label_color, 8, anchor="center")

    def animate(self):
        self.frame += 1
        self.draw()
        self.root.after(280, self.animate)

    # ── popups ──────────────────────────────────────────────────────────────

    def finish_popup(self):
        """Codex-style completion popup: pink/green, falling square particles."""
        self.done_label = self.t("done_codex")
        self.message_until = time.time() + 4

        objective = (self.goal_state.get("latest_objective") or "").strip()
        if len(objective) > 44:
            objective = objective[:41] + "..."
        popup_h = 120 if objective else 100

        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg="#1a1022")
        wx, wy = self.root.winfo_x(), self.root.winfo_y()
        wh = self.root.winfo_height()
        popup.geometry(f"320x{popup_h}+{wx + 20}+{wy + wh + 4}")

        canvas = tk.Canvas(popup, width=320, height=popup_h, bg="#1a1022", highlightthickness=0)
        canvas.pack()
        canvas.bind("<Button-1>", lambda _e: popup.destroy())

        particles = []
        for i in range(32):
            particles.append([160, 48, (i % 8 - 3.5) * 2.2, -4 - (i % 5), [GREEN, PINK, YELLOW, BLUE][i % 4]])

        def tick(step=0):
            canvas.delete("all")
            canvas.create_rectangle(3, 3, 317, popup_h - 3, outline=PINK, width=3)
            canvas.create_text(
                160, 24,
                text=self.theme.speech_text("done_title", "DONE!"),
                fill=YELLOW, font=("Consolas", 15, "bold"),
            )
            canvas.create_text(
                160, 52,
                text=self.theme.speech_text("done_body", "Codex finished the task."),
                fill=INK, font=("Consolas", 10, "bold"),
            )
            if objective:
                canvas.create_text(160, 80, text=f'"{objective}"', fill=MUTED, font=("Consolas", 8))
            for p in particles:
                p[0] += p[2]
                p[1] += p[3]
                p[3] += 0.45
                canvas.create_rectangle(p[0], p[1], p[0] + 5, p[1] + 5, fill=p[4], outline=p[4])
            if step < 45:
                popup.after(45, lambda: tick(step + 1))
            else:
                popup.destroy()

        tick()

    def claude_popup(self):
        """Claude-style completion popup: indigo/purple, rising circular particles."""
        self.done_label = self.t("done_claude")
        self.message_until = time.time() + 4

        popup_h = 108

        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg=CLAUDE_BG)
        wx, wy = self.root.winfo_x(), self.root.winfo_y()
        wh = self.root.winfo_height()
        popup.geometry(f"320x{popup_h}+{wx + 20}+{wy + wh + 4}")

        canvas = tk.Canvas(popup, width=320, height=popup_h, bg=CLAUDE_BG, highlightthickness=0)
        canvas.pack()
        canvas.bind("<Button-1>", lambda _e: popup.destroy())

        # Particles rise from bottom with deceleration
        particles = []
        for i in range(28):
            particles.append([
                30 + (i * 9) % 260,
                popup_h - 8,
                (i % 7 - 3) * 1.4,
                -3.0 - (i % 5) * 0.6,
                CLAUDE_PARTICLES[i % len(CLAUDE_PARTICLES)],
            ])

        def tick(step=0):
            canvas.delete("all")
            # Dark inner fill + border
            canvas.create_rectangle(2, 2, 318, popup_h - 2, fill=CLAUDE_INNER, outline=CLAUDE_BORDER, width=2)
            # Subtle top accent line
            canvas.create_line(12, 4, 308, 4, fill=CLAUDE_BORDER, width=1)
            # Title with ✦ symbol
            canvas.create_text(
                160, 26,
                text="✦  CLAUDE DONE",
                fill=CLAUDE_TITLE, font=("Consolas", 14, "bold"),
            )
            canvas.create_text(
                160, 54,
                text="Claude Code finished the session.",
                fill=CLAUDE_BODY, font=("Consolas", 9),
            )
            canvas.create_text(
                160, 76,
                text="click to dismiss",
                fill=CLAUDE_MUTED, font=("Consolas", 7),
            )
            # Rising circular particles
            for p in particles:
                p[0] += p[2]
                p[1] += p[3]
                p[3] *= 0.94  # decelerate upward
                p[2] *= 0.98  # decelerate lateral
                if 0 <= p[0] <= 320 and -6 <= p[1] <= popup_h + 6:
                    r = 3
                    canvas.create_oval(p[0] - r, p[1] - r, p[0] + r, p[1] + r, fill=p[4], outline="")
            if step < 50:
                popup.after(45, lambda: tick(step + 1))
            else:
                popup.destroy()

        tick()


def main():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"Cannot start GUI: {exc}", file=sys.stderr)
        return 1
    PixelPet(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
