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


def load_config():
    defaults = {
        "codex_logs_db": str(DEFAULT_CODEX_DB),
        "codex_goals_db": str(DEFAULT_CODEX_GOALS_DB),
        "claude_dir": str(DEFAULT_CLAUDE_DIR),
        "claude_exe": str(DEFAULT_CLAUDE_EXE),
        "refresh_seconds": 5,
        "always_on_top": True,
        "trigger_finish_popup_on_new_codex_completion": False,
        "trigger_finish_popup_on_goal_complete": True,
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
                data = json.loads(ccusage)
                today_key = datetime.now().strftime("%Y-%m-%d")
                rows = data.get("daily", data if isinstance(data, list) else [])
                today_rows = [r for r in rows if str(r.get("date", "")).startswith(today_key)]
                total_cost = sum(float(r.get("totalCost", r.get("cost", 0)) or 0) for r in today_rows)
                total_tokens = sum(int(r.get("totalTokens", r.get("tokens", 0)) or 0) for r in today_rows)
                result["ok"] = True
                result["source"] = "ccusage"
                result["today"]["total"] = total_tokens
                result["today"]["cost"] = total_cost
                result["note"] = ""
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

        result["source"] = str(claude_dir)
        if claude_dir.exists():
            jsonl_usage = self._read_claude_jsonl_usage(claude_dir)
            if jsonl_usage["seen_files"]:
                jsonl_usage["installed"] = result["installed"]
                jsonl_usage["version"] = result["version"]
                result.update(jsonl_usage)
                return result
            files = list(claude_dir.rglob("*"))
            if result["installed"]:
                result["ok"] = True
                result["source"] = str(claude_exe)
                result["note"] = f"Claude Code {result['version']}, no usage logs yet"
            else:
                result["note"] = f"Claude folder found, no usage logs ({len(files)} files)"
        return result

    def _read_claude_jsonl_usage(self, claude_dir):
        result = {
            "ok": False,
            "source": str(claude_dir / "projects"),
            "today": {"input": 0, "output": 0, "cached": 0, "total": 0, "calls": 0, "cost": 0.0},
            "month": {"input": 0, "output": 0, "cached": 0, "total": 0, "calls": 0, "cost": 0.0},
            "note": "",
            "seen_files": 0,
        }
        projects = claude_dir / "projects"
        if not projects.exists():
            return result

        today_start, _ = today_bounds()
        month_start, _ = month_bounds()
        seen_ids = set()
        files = list(projects.rglob("*.jsonl"))
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
        bucket["calls"] += 1
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
        self.last_signal_mtime = 0
        self.frame = 0
        self.drag = None
        self.message_until = 0
        self.settings_window = None
        self.gear_box = (300, 14, 322, 36)

        root.title("Pixel Token Pet")
        root.geometry("340x286+120+120")
        root.configure(bg=BG)
        root.overrideredirect(True)
        root.attributes("-topmost", bool(self.config.get("always_on_top", True)))

        self.canvas = tk.Canvas(root, width=340, height=286, highlightthickness=0, bg=BG)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        self.canvas.bind("<Double-Button-1>", lambda _e: self.finish_popup())
        self.canvas.bind("<Button-3>", self.show_menu)

        self.menu = tk.Menu(root, tearoff=0)
        self.menu.add_command(label="Done animation", command=self.finish_popup)
        self.menu.add_command(label="Refresh", command=self.refresh)
        self.menu.add_separator()
        self.menu.add_command(label="Close pet", command=root.destroy)

        self.codex_data = self.reader.codex()
        self.claude_data = self.reader.claude()
        self.goal_state = self.reader.codex_goal_state()
        self.last_codex_completion = self.codex_data.get("latest_id", 0)
        self.last_completed_goal_key = self.goal_state.get("latest_completed_key", "")
        self.refresh()
        self.record_memory()
        self.animate()

    def start_drag(self, event):
        if self.is_gear_hit(event.x, event.y):
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

    def open_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return

        win = tk.Toplevel(self.root)
        self.settings_window = win
        win.title("Pixel Token Pet Settings")
        win.configure(bg=BG)
        win.attributes("-topmost", bool(self.config.get("always_on_top", True)))
        win.resizable(False, False)
        win.geometry(f"360x292+{self.root.winfo_x() + 348}+{self.root.winfo_y()}")

        theme_options = available_themes()
        theme_ids = [item["id"] for item in theme_options] or [DEFAULT_THEME]
        theme_label = {item["id"]: f"{item['name']} ({item['id']})" for item in theme_options}

        selected_theme = tk.StringVar(value=self.config.get("theme", DEFAULT_THEME))
        always_top = tk.BooleanVar(value=bool(self.config.get("always_on_top", True)))
        memory_enabled = tk.BooleanVar(value=bool(self.config.get("memory_log_enabled", True)))
        refresh_seconds = tk.StringVar(value=str(self.config.get("refresh_seconds", 5)))
        memory_seconds = tk.StringVar(value=str(self.config.get("memory_sample_seconds", 300)))

        body = tk.Frame(win, bg=BG, padx=14, pady=14)
        body.pack(fill="both", expand=True)
        self.settings_label(body, "Theme")

        theme_menu = tk.OptionMenu(body, selected_theme, *theme_ids)
        theme_menu.configure(bg=PANEL, fg=INK, activebackground="#383348", activeforeground=INK, highlightthickness=0)
        theme_menu["menu"].configure(bg=PANEL, fg=INK)
        theme_menu.pack(fill="x", pady=(3, 10))

        tk.Checkbutton(
            body,
            text="Always on top",
            variable=always_top,
            bg=BG,
            fg=INK,
            activebackground=BG,
            activeforeground=INK,
            selectcolor=PANEL,
        ).pack(anchor="w")
        tk.Checkbutton(
            body,
            text="Memory logging",
            variable=memory_enabled,
            bg=BG,
            fg=INK,
            activebackground=BG,
            activeforeground=INK,
            selectcolor=PANEL,
        ).pack(anchor="w", pady=(0, 8))

        self.settings_entry(body, "Refresh seconds", refresh_seconds)
        self.settings_entry(body, "Memory sample seconds", memory_seconds)

        hint = tk.Label(
            body,
            text="Changes are saved to local config.json.",
            bg=BG,
            fg=MUTED,
            font=("Consolas", 8),
            anchor="w",
        )
        hint.pack(fill="x", pady=(8, 10))

        actions = tk.Frame(body, bg=BG)
        actions.pack(fill="x")
        tk.Button(actions, text="Test popup", command=self.finish_popup, bg=PANEL, fg=INK).pack(side="left")
        tk.Button(actions, text="Save", command=lambda: save_settings(), bg=PANEL, fg=GREEN).pack(side="right")

        def save_settings():
            try:
                refresh_value = max(1, int(refresh_seconds.get()))
            except Exception:
                refresh_value = 5
            try:
                memory_value = max(30, int(memory_seconds.get()))
            except Exception:
                memory_value = 300

            self.config["theme"] = selected_theme.get()
            self.config["always_on_top"] = bool(always_top.get())
            self.config["memory_log_enabled"] = bool(memory_enabled.get())
            self.config["refresh_seconds"] = refresh_value
            self.config["memory_sample_seconds"] = memory_value
            save_config(self.config)

            self.theme = PetTheme.load(self.config)
            self.memory = MemoryMonitor(self.config)
            self.root.attributes("-topmost", bool(self.config.get("always_on_top", True)))
            self.draw()
            win.destroy()

    def settings_label(self, parent, text_value):
        tk.Label(parent, text=text_value, bg=BG, fg=YELLOW, font=("Consolas", 9, "bold"), anchor="w").pack(fill="x")

    def settings_entry(self, parent, label, variable):
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=3)
        tk.Label(row, text=label, bg=BG, fg=INK, font=("Consolas", 9), anchor="w").pack(side="left")
        tk.Entry(row, textvariable=variable, width=8, bg=PANEL, fg=INK, insertbackground=INK).pack(side="right")

    def refresh(self):
        old_latest = self.codex_data.get("latest_id", 0) if hasattr(self, "codex_data") else 0
        self.codex_data = self.reader.codex()
        self.claude_data = self.reader.claude()
        self.goal_state = self.reader.codex_goal_state()
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
        self.check_finish_signal()
        self.last_codex_completion = new_latest
        self.draw()
        self.root.after(int(self.config.get("refresh_seconds", 5)) * 1000, self.refresh)

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

    def draw(self):
        self.canvas.delete("all")
        self.rect(0, 0, 340, 286, BG)
        self.rect(8, 8, 324, 270, PANEL)
        self.rect(12, 12, 316, 262, "#17151f")
        self.draw_gear()
        self.draw_pet()

        c = self.codex_data
        today = c["today"]
        all_time = c["all"]
        y = 88
        self.text(24, y, "CODEX", BLUE, 12)
        if c["ok"]:
            self.text(24, y + 20, f"today in/out : {human(today['input'])} / {human(today['output'])}", INK, 10)
            self.text(24, y + 38, f"today total  : {human(today['total'])}  calls {today['calls']}", INK, 10)
            self.text(24, y + 56, f"cached/reason: {human(today['cached'])} / {human(today['reasoning'])}", MUTED, 9)
            self.text(24, y + 74, f"all tokens   : {human(all_time['total'])}", MUTED, 9)
            self.text(24, y + 92, f"latest {c['latest_time']} {c['latest_model']}", GREEN, 9)
            denom = max(today["input"] + today["output"] + today["cached"], 1)
            self.draw_bar(205, y + 23, 70, today["output"] / denom, PINK, "out")
            self.draw_bar(205, y + 45, 70, today["cached"] / denom, BLUE, "cache")
        else:
            self.text(24, y + 24, c["error"], RED, 9)

        cl = self.claude_data
        y = 205
        self.text(24, y, "CLAUDE", PINK, 12)
        if cl["ok"]:
            ct = cl["today"]
            cm = cl["month"]
            self.text(24, y + 20, f"today total: {human(ct['total'])}  calls {ct['calls']}", INK, 10)
            self.text(24, y + 38, f"in/out/cache: {human(ct['input'])}/{human(ct['output'])}/{human(ct['cached'])}", MUTED, 8)
            if ct["calls"]:
                self.text(24, y + 54, f"month total: {human(cm['total'])}", MUTED, 8)
            else:
                self.text(24, y + 54, cl["note"], MUTED, 8)
        else:
            self.text(24, y + 20, "usage: not connected", YELLOW, 10)
            self.text(24, y + 38, cl["note"], MUTED, 8)

        mem = self.memory.today_summary()
        self.text(
            24,
            268,
            f"MEM now/avg/max: {mem['current_mb']}/{mem['avg_mb']}/{mem['max_mb']} MB  samples {mem['samples']}",
            MUTED,
            7,
        )

        if time.time() < self.message_until:
            self.rect(57, 246, 226, 20, "#3b2440")
            self.text(170, 256, "Done! Codex finished.", GREEN, 10, anchor="center")

    def animate(self):
        self.frame += 1
        self.draw()
        self.root.after(280, self.animate)

    def finish_popup(self):
        self.message_until = time.time() + 4
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg="#1a1022")
        x = self.root.winfo_x() + 25
        y = self.root.winfo_y() + 295
        popup.geometry(f"292x98+{x}+{y}")
        canvas = tk.Canvas(popup, width=292, height=98, bg="#1a1022", highlightthickness=0)
        canvas.pack()

        particles = []
        for i in range(28):
            particles.append([146, 48, (i % 7 - 3) * 2.2, -4 - (i % 5), [GREEN, PINK, YELLOW, BLUE][i % 4]])

        def tick(step=0):
            canvas.delete("all")
            canvas.create_rectangle(3, 3, 289, 95, outline=PINK, width=3)
            canvas.create_text(
                146,
                22,
                text=self.theme.speech_text("done_title", "DONE!"),
                fill=YELLOW,
                font=("Consolas", 15, "bold"),
            )
            canvas.create_text(
                146,
                49,
                text=self.theme.speech_text("done_body", "Codex finished the task."),
                fill=INK,
                font=("Consolas", 10, "bold"),
            )
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
