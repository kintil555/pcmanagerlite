"""
app.py - Main PCManagerApp class with CustomTkinter UI
"""

import os
import sys
import threading
import time
import queue
from datetime import datetime
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageTk
import psutil

# ── Theme ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg":           "#111318",
    "sidebar":      "#181B24",
    "card":         "#1E2130",
    "card_hover":   "#252840",
    "accent":       "#4F8EF7",
    "accent2":      "#6C63FF",
    "success":      "#22C55E",
    "warning":      "#F59E0B",
    "danger":       "#EF4444",
    "text":         "#E8EAF0",
    "text_dim":     "#8B90A8",
    "border":       "#2A2E42",
    "teal":         "#06B6D4",
}

FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_H2     = ("Segoe UI", 15, "bold")
FONT_H3     = ("Segoe UI", 13, "bold")
FONT_BODY   = ("Segoe UI", 12)
FONT_SMALL  = ("Segoe UI", 10)
FONT_TINY   = ("Segoe UI", 9)


def resource_path(rel: str) -> str:
    """Get absolute path to resource (works for dev and PyInstaller)."""
    if getattr(sys, '_MEIPASS', None):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel)


# ── Helper Widgets ─────────────────────────────────────────────────────────────

class Card(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["card"])
        kwargs.setdefault("corner_radius", 12)
        super().__init__(master, **kwargs)


class SectionTitle(ctk.CTkLabel):
    def __init__(self, master, text, **kwargs):
        super().__init__(master, text=text, font=FONT_H2,
                         text_color=COLORS["text"], **kwargs)


class DimLabel(ctk.CTkLabel):
    def __init__(self, master, text, **kwargs):
        super().__init__(master, text=text, font=FONT_SMALL,
                         text_color=COLORS["text_dim"], **kwargs)


class AccentButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["accent"])
        kwargs.setdefault("hover_color", COLORS["accent2"])
        kwargs.setdefault("text_color", "#FFFFFF")
        kwargs.setdefault("corner_radius", 8)
        kwargs.setdefault("font", FONT_BODY)
        super().__init__(master, **kwargs)


class CircularProgress(ctk.CTkCanvas):
    """Simple arc progress indicator."""
    def __init__(self, master, size=90, thickness=10, **kwargs):
        super().__init__(master, width=size, height=size,
                         bg=COLORS["card"], highlightthickness=0, **kwargs)
        self.size = size
        self.thickness = thickness
        self._value = 0
        self._draw(0, COLORS["accent"])

    def set(self, value: float, color: str = None):
        self._value = max(0, min(100, value))
        c = color or (
            COLORS["danger"] if self._value > 85 else
            COLORS["warning"] if self._value > 65 else
            COLORS["success"]
        )
        self._draw(self._value, c)

    def _draw(self, pct, color):
        self.delete("all")
        pad = self.thickness + 4
        s, e = pad, self.size - pad
        # background arc
        self.create_arc(s, e, e, s, start=90, extent=-360,
                        outline=COLORS["border"], style="arc", width=self.thickness)
        # value arc
        if pct > 0:
            extent = -3.6 * pct
            self.create_arc(s, e, e, s, start=90, extent=extent,
                            outline=color, style="arc", width=self.thickness)
        cx = cy = self.size / 2
        self.create_text(cx, cy, text=f"{pct:.0f}%",
                         fill=COLORS["text"], font=("Segoe UI", 12, "bold"))


# ── Sidebar Navigation ─────────────────────────────────────────────────────────

NAV_ITEMS = [
    ("🏠", "Home"),
    ("⚡", "Boost"),
    ("🗑️", "Deep Clean"),
    ("🔄", "Processes"),
    ("🚀", "Startup"),
    ("❤️", "Health"),
    ("⚙️", "Settings"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_select, **kwargs):
        super().__init__(master, width=200, fg_color=COLORS["sidebar"],
                         corner_radius=0, **kwargs)
        self.on_select = on_select
        self._buttons = {}
        self._active = "Home"
        self._build()

    def _build(self):
        # Logo area
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(pady=(24, 8), padx=16, fill="x")

        try:
            icon_img = Image.open(resource_path("assets/icon.png")).resize((36, 36))
            icon_ctk = ctk.CTkImage(icon_img, size=(36, 36))
            ctk.CTkLabel(logo_frame, image=icon_ctk, text="").pack(side="left", padx=(0, 10))
        except Exception:
            pass

        ctk.CTkLabel(logo_frame, text="PC Manager", font=("Segoe UI", 15, "bold"),
                     text_color=COLORS["text"]).pack(side="left")

        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=16, pady=(8, 16))

        # Nav buttons
        for icon, label in NAV_ITEMS:
            btn = ctk.CTkButton(
                self,
                text=f"  {icon}  {label}",
                anchor="w",
                font=FONT_BODY,
                fg_color="transparent",
                hover_color=COLORS["card"],
                text_color=COLORS["text_dim"],
                corner_radius=8,
                height=42,
                command=lambda l=label: self._select(l),
            )
            btn.pack(padx=12, pady=2, fill="x")
            self._buttons[label] = btn

        self._select("Home")

        # Version at bottom
        ctk.CTkLabel(self, text="v1.0.0", font=FONT_TINY,
                     text_color=COLORS["text_dim"]).pack(side="bottom", pady=16)

    def _select(self, label):
        if self._active in self._buttons:
            self._buttons[self._active].configure(
                fg_color="transparent", text_color=COLORS["text_dim"])
        self._active = label
        self._buttons[label].configure(
            fg_color=COLORS["card"], text_color=COLORS["accent"])
        self.on_select(label)


# ── PAGE: HOME ────────────────────────────────────────────────────────────────

class HomePage(ctk.CTkScrollableFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._build()

    def _build(self):
        SectionTitle(self, "System Overview").pack(anchor="w", pady=(8, 16))

        # Top row - CPU / RAM / Disk
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", pady=(0, 16))
        row.columnconfigure((0, 1, 2), weight=1, uniform="col")

        self.cpu_arc   = self._stat_card(row, 0, "CPU")
        self.ram_arc   = self._stat_card(row, 1, "RAM")
        self.disk_arc  = self._stat_card(row, 2, "Disk (C:)")

        # Quick actions
        SectionTitle(self, "Quick Actions").pack(anchor="w", pady=(0, 12))
        actions_row = ctk.CTkFrame(self, fg_color="transparent")
        actions_row.pack(fill="x", pady=(0, 16))

        quick = [
            ("⚡ Boost Now",   self.app.quick_boost,         COLORS["accent"]),
            ("🗑️ Quick Clean", self.app.quick_clean,          COLORS["teal"]),
            ("❤️ Health Check", self.app.quick_health,        COLORS["success"]),
        ]
        for i, (text, cmd, color) in enumerate(quick):
            btn = ctk.CTkButton(actions_row, text=text, font=FONT_H3,
                                fg_color=color, hover_color=COLORS["card_hover"],
                                corner_radius=10, height=52, command=cmd)
            btn.grid(row=0, column=i, padx=(0 if i == 0 else 8, 0), sticky="ew")
            actions_row.columnconfigure(i, weight=1)

        # Status bar
        self.status_lbl = ctk.CTkLabel(self, text="", font=FONT_SMALL,
                                       text_color=COLORS["text_dim"])
        self.status_lbl.pack(anchor="w", pady=(0, 8))

        # Recent activity
        SectionTitle(self, "Recent Activity").pack(anchor="w", pady=(8, 12))
        self.activity_frame = ctk.CTkFrame(self, fg_color=COLORS["card"],
                                           corner_radius=12)
        self.activity_frame.pack(fill="x")
        self.activity_labels = []
        for _ in range(5):
            lbl = ctk.CTkLabel(self.activity_frame, text="", font=FONT_SMALL,
                               text_color=COLORS["text_dim"], anchor="w")
            lbl.pack(anchor="w", padx=16, pady=2)
            self.activity_labels.append(lbl)

    def _stat_card(self, parent, col, title):
        card = Card(parent)
        card.grid(row=0, column=col, padx=(0 if col == 0 else 8, 0), sticky="ew")
        ctk.CTkLabel(card, text=title, font=FONT_H3,
                     text_color=COLORS["text"]).pack(pady=(14, 4))
        arc = CircularProgress(card, size=100, thickness=10)
        arc.pack(pady=(4, 14))
        return arc

    def update_stats(self, info: dict):
        self.cpu_arc.set(info["cpu_percent"])
        self.ram_arc.set(info["mem_percent"])
        self.disk_arc.set(info["disk_percent"])

    def add_activity(self, msg: str):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M")
        entry = f"[{timestamp}]  {msg}"
        # Shift labels down
        for i in range(len(self.activity_labels) - 1, 0, -1):
            self.activity_labels[i].configure(
                text=self.activity_labels[i-1].cget("text"))
        self.activity_labels[0].configure(text=entry)

    def set_status(self, msg: str):
        self.status_lbl.configure(text=msg)


# ── PAGE: BOOST ───────────────────────────────────────────────────────────────

class BoostPage(ctk.CTkScrollableFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._build()

    def _build(self):
        SectionTitle(self, "⚡ PC Boost").pack(anchor="w", pady=(8, 4))
        DimLabel(self, "Free up memory and clear temporary files quickly").pack(anchor="w", pady=(0, 16))

        card = Card(self)
        card.pack(fill="x", pady=(0, 16))

        self.temp_lbl = ctk.CTkLabel(card, text="Scanning...", font=FONT_H3,
                                     text_color=COLORS["text"])
        self.temp_lbl.pack(pady=(20, 4))
        DimLabel(card, "Temporary files detected").pack()

        mem = psutil.virtual_memory()
        ram_text = f"RAM: {mem.percent:.0f}% used  ({mem.available // (1024**2)} MB free)"
        ctk.CTkLabel(card, text=ram_text, font=FONT_BODY,
                     text_color=COLORS["text_dim"]).pack(pady=(8, 4))

        self.boost_btn = AccentButton(card, text="⚡  Boost Now",
                                     font=FONT_H3, height=48,
                                     command=self._do_boost)
        self.boost_btn.pack(pady=(12, 20), padx=40, fill="x")

        self.result_lbl = ctk.CTkLabel(self, text="", font=FONT_BODY,
                                       text_color=COLORS["success"])
        self.result_lbl.pack()

        # Refresh temp size
        threading.Thread(target=self._scan_temp, daemon=True).start()

    def _scan_temp(self):
        from system_utils import get_temp_size, format_bytes
        size = get_temp_size()
        self.temp_lbl.configure(text=format_bytes(size))

    def _do_boost(self):
        self.boost_btn.configure(state="disabled", text="Boosting...")
        self.result_lbl.configure(text="")
        threading.Thread(target=self._boost_worker, daemon=True).start()

    def _boost_worker(self):
        from system_utils import boost_pc, format_bytes
        result = boost_pc()
        freed = result["freed"]
        msg = f"✓  Freed {format_bytes(freed)} — PC boosted!"
        self.after(0, lambda: self._boost_done(msg))

    def _boost_done(self, msg):
        self.boost_btn.configure(state="normal", text="⚡  Boost Now")
        self.result_lbl.configure(text=msg, text_color=COLORS["success"])
        self.app.home_page.add_activity(msg)
        threading.Thread(target=self._scan_temp, daemon=True).start()


# ── PAGE: DEEP CLEAN ──────────────────────────────────────────────────────────

class DeepCleanPage(ctk.CTkScrollableFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._checks = {}
        self._sizes  = {}
        self._build()

    def _build(self):
        SectionTitle(self, "🗑️ Deep Cleanup").pack(anchor="w", pady=(8, 4))
        DimLabel(self, "Select categories to clean").pack(anchor="w", pady=(0, 16))

        from system_utils import CLEANUP_TARGETS
        for category in CLEANUP_TARGETS:
            row = Card(self)
            row.pack(fill="x", pady=4)
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=10)

            var = ctk.BooleanVar(value=True)
            chk = ctk.CTkCheckBox(inner, text=category, variable=var,
                                   font=FONT_BODY, text_color=COLORS["text"])
            chk.pack(side="left")

            size_lbl = ctk.CTkLabel(inner, text="...", font=FONT_SMALL,
                                     text_color=COLORS["text_dim"])
            size_lbl.pack(side="right")

            self._checks[category] = var
            self._sizes[category]  = size_lbl

        self.scan_btn   = AccentButton(self, text="🔍  Scan",
                                       command=self._do_scan, height=44)
        self.scan_btn.pack(pady=(16, 6), fill="x")

        self.clean_btn  = AccentButton(self, text="🗑️  Clean Selected",
                                       fg_color=COLORS["danger"],
                                       hover_color="#C53030",
                                       command=self._do_clean, height=44,
                                       state="disabled")
        self.clean_btn.pack(pady=(0, 12), fill="x")

        self.result_lbl = ctk.CTkLabel(self, text="", font=FONT_BODY,
                                       text_color=COLORS["success"])
        self.result_lbl.pack()

    def _do_scan(self):
        self.scan_btn.configure(state="disabled", text="Scanning...")
        self.clean_btn.configure(state="disabled")
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        from system_utils import scan_cleanup, format_bytes
        sizes = scan_cleanup()
        def update():
            for cat, sz in sizes.items():
                if cat in self._sizes:
                    self._sizes[cat].configure(
                        text=format_bytes(sz) if sz > 0 else "Empty")
            self.scan_btn.configure(state="normal", text="🔍  Scan")
            self.clean_btn.configure(state="normal")
        self.after(0, update)

    def _do_clean(self):
        selected = [cat for cat, var in self._checks.items() if var.get()]
        if not selected:
            return
        self.clean_btn.configure(state="disabled", text="Cleaning...")
        threading.Thread(target=self._clean_worker, args=(selected,), daemon=True).start()

    def _clean_worker(self, selected):
        from system_utils import deep_cleanup, format_bytes
        result = deep_cleanup(selected)
        freed = result["freed"]
        msg = f"✓  Cleaned {len(result['cleaned'])} categories — {format_bytes(freed)} freed"
        def done():
            self.clean_btn.configure(state="normal", text="🗑️  Clean Selected")
            self.result_lbl.configure(text=msg, text_color=COLORS["success"])
            self.app.home_page.add_activity(msg)
            self._do_scan()
        self.after(0, done)


# ── PAGE: PROCESSES ───────────────────────────────────────────────────────────

class ProcessPage(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._procs = []
        self._sort = "memory"
        self._build()
        self._refresh()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(8, 12))

        SectionTitle(header, "🔄 Process Manager").pack(side="left")

        ctk.CTkButton(header, text="🔃 Refresh", font=FONT_SMALL,
                      fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                      text_color=COLORS["text"], corner_radius=8, height=32,
                      command=self._refresh).pack(side="right")

        # Sort controls
        sort_frame = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=8)
        sort_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(sort_frame, text="Sort:", font=FONT_SMALL,
                     text_color=COLORS["text_dim"]).pack(side="left", padx=(12, 6), pady=6)
        for label, key in [("Memory", "memory"), ("CPU", "cpu"), ("Name", "name")]:
            ctk.CTkButton(sort_frame, text=label, font=FONT_SMALL,
                          fg_color="transparent", hover_color=COLORS["card_hover"],
                          text_color=COLORS["text"], corner_radius=6, height=28, width=70,
                          command=lambda k=key: self._sort_by(k)).pack(side="left", padx=2, pady=4)

        # Column headers
        cols = ctk.CTkFrame(self, fg_color=COLORS["border"], corner_radius=4)
        cols.pack(fill="x", pady=(0, 2))
        for text, w in [("Process Name", 200), ("PID", 70), ("Status", 90),
                        ("Memory", 90), ("CPU%", 70), ("", 80)]:
            ctk.CTkLabel(cols, text=text, font=("Segoe UI", 10, "bold"),
                         text_color=COLORS["text_dim"], width=w, anchor="w").pack(
                side="left", padx=6, pady=4)

        # Scrollable list
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=COLORS["card"],
                                                  corner_radius=12)
        self.list_frame.pack(fill="both", expand=True)

    def _sort_by(self, key):
        self._sort = key
        self._refresh()

    def _refresh(self):
        threading.Thread(target=self._fetch_procs, daemon=True).start()

    def _fetch_procs(self):
        from system_utils import get_processes
        procs = get_processes(self._sort)[:60]  # limit to 60 for performance
        self.after(0, lambda: self._render(procs))

    def _render(self, procs):
        for w in self.list_frame.winfo_children():
            w.destroy()

        from system_utils import format_bytes
        for p in procs:
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent",
                               corner_radius=6)
            row.pack(fill="x", pady=1, padx=4)

            color = COLORS["text"] if p['status'] == 'running' else COLORS["text_dim"]

            def mk_lbl(text, width, clr=color):
                return ctk.CTkLabel(row, text=str(text)[:28], font=FONT_SMALL,
                                    text_color=clr, width=width, anchor="w")

            mk_lbl(p['name'], 200).pack(side="left", padx=6, pady=3)
            mk_lbl(p['pid'], 70).pack(side="left", padx=2)
            mk_lbl(p['status'], 90).pack(side="left", padx=2)
            mk_lbl(format_bytes(p['memory']), 90).pack(side="left", padx=2)
            mk_lbl(f"{p['cpu']:.1f}", 70).pack(side="left", padx=2)

            ctk.CTkButton(row, text="End", font=FONT_TINY, width=60, height=24,
                          fg_color=COLORS["danger"], hover_color="#C53030",
                          text_color="white", corner_radius=6,
                          command=lambda pid=p['pid']: self._end(pid)).pack(
                side="right", padx=6, pady=3)

    def _end(self, pid):
        from system_utils import kill_process
        if kill_process(pid):
            self.app.home_page.add_activity(f"Ended process PID {pid}")
            self._refresh()


# ── PAGE: STARTUP ─────────────────────────────────────────────────────────────

class StartupPage(ctk.CTkFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._items = []
        self._build()
        self._load()

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(8, 12))
        SectionTitle(header, "🚀 Startup Manager").pack(side="left")
        ctk.CTkButton(header, text="🔃 Refresh", font=FONT_SMALL,
                      fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                      text_color=COLORS["text"], corner_radius=8, height=32,
                      command=self._load).pack(side="right")

        DimLabel(self, "Manage programs that start automatically with Windows").pack(anchor="w", pady=(0, 12))

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=COLORS["card"],
                                                  corner_radius=12)
        self.list_frame.pack(fill="both", expand=True)

    def _load(self):
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        from system_utils import get_startup_items
        try:
            items = get_startup_items()
        except Exception:
            items = []
        self.after(0, lambda: self._render(items))

    def _render(self, items):
        self._items = items
        for w in self.list_frame.winfo_children():
            w.destroy()

        if not items:
            ctk.CTkLabel(self.list_frame, text="No startup items found",
                         font=FONT_BODY, text_color=COLORS["text_dim"]).pack(pady=40)
            return

        for item in items:
            card = ctk.CTkFrame(self.list_frame, fg_color=COLORS["card_hover"],
                                corner_radius=8)
            card.pack(fill="x", padx=8, pady=3)

            left = ctk.CTkFrame(card, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=12, pady=10)

            ctk.CTkLabel(left, text=item["name"], font=FONT_BODY,
                         text_color=COLORS["text"], anchor="w").pack(anchor="w")
            path_text = (item["path"][:60] + "...") if len(item["path"]) > 60 else item["path"]
            ctk.CTkLabel(left, text=path_text, font=FONT_TINY,
                         text_color=COLORS["text_dim"], anchor="w").pack(anchor="w")

            btn_text = "Disable" if item["enabled"] else "Enable"
            btn_color = COLORS["warning"] if item["enabled"] else COLORS["success"]
            ctk.CTkButton(card, text=btn_text, font=FONT_SMALL,
                          fg_color=btn_color, hover_color=COLORS["card"],
                          text_color="white", corner_radius=6,
                          width=80, height=30,
                          command=lambda i=item: self._toggle(i)).pack(
                side="right", padx=12, pady=10)

    def _toggle(self, item):
        from system_utils import disable_startup_item, enable_startup_item
        if item["enabled"]:
            disable_startup_item(item)
            self.app.home_page.add_activity(f"Disabled startup: {item['name']}")
        else:
            enable_startup_item(item)
            self.app.home_page.add_activity(f"Enabled startup: {item['name']}")
        self._load()


# ── PAGE: HEALTH ──────────────────────────────────────────────────────────────

class HealthPage(ctk.CTkScrollableFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._build()

    def _build(self):
        SectionTitle(self, "❤️ Health Check").pack(anchor="w", pady=(8, 4))
        DimLabel(self, "Comprehensive system health analysis").pack(anchor="w", pady=(0, 16))

        self.run_btn = AccentButton(self, text="▶  Run Health Check",
                                    font=FONT_H3, height=48,
                                    command=self._run)
        self.run_btn.pack(fill="x", pady=(0, 16))

        self.results_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True)

        self.last_check_lbl = DimLabel(self, text="")
        self.last_check_lbl.pack(anchor="w", pady=(12, 0))

    def _run(self):
        self.run_btn.configure(state="disabled", text="Running check...")
        for w in self.results_frame.winfo_children():
            w.destroy()
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        from system_utils import run_health_check
        findings = run_health_check()
        self.after(0, lambda: self._render(findings))

    def _render(self, findings):
        status_colors = {
            "ok":       COLORS["success"],
            "warning":  COLORS["warning"],
            "critical": COLORS["danger"],
        }
        status_icons = {
            "ok":       "✓",
            "warning":  "⚠",
            "critical": "✗",
        }

        for f in findings:
            color = status_colors.get(f["status"], COLORS["text_dim"])
            icon  = status_icons.get(f["status"], "•")

            card = Card(self.results_frame)
            card.pack(fill="x", pady=4)

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=12)

            ctk.CTkLabel(row, text=icon, font=("Segoe UI", 18, "bold"),
                         text_color=color, width=30).pack(side="left")

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=12)

            ctk.CTkLabel(info, text=f["category"], font=FONT_H3,
                         text_color=COLORS["text"], anchor="w").pack(anchor="w")
            ctk.CTkLabel(info, text=f["message"], font=FONT_SMALL,
                         text_color=COLORS["text_dim"], anchor="w").pack(anchor="w")
            if f.get("action"):
                ctk.CTkLabel(info, text=f"→ {f['action']}", font=FONT_TINY,
                             text_color=color, anchor="w").pack(anchor="w")

        ok_count = sum(1 for f in findings if f["status"] == "ok")
        summary = f"✓  {ok_count}/{len(findings)} checks passed"
        self.app.home_page.add_activity(summary)
        self.run_btn.configure(state="normal", text="▶  Run Health Check")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_check_lbl.configure(text=f"Last check: {now}")


# ── PAGE: SETTINGS ────────────────────────────────────────────────────────────

class SettingsPage(ctk.CTkScrollableFrame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.app = app
        self._build()

    def _build(self):
        SectionTitle(self, "⚙️ Settings").pack(anchor="w", pady=(8, 16))

        sections = [
            ("Appearance", [
                ("Theme", "dropdown", ["Dark", "Light", "System"]),
            ]),
            ("Behavior", [
                ("Start minimized to tray", "toggle", True),
                ("Auto-boost on startup",   "toggle", False),
                ("Show notifications",       "toggle", True),
            ]),
            ("Performance", [
                ("Refresh interval (seconds)", "dropdown", ["5", "10", "30", "60"]),
            ]),
        ]

        for section_title, items in sections:
            ctk.CTkLabel(self, text=section_title, font=FONT_H3,
                         text_color=COLORS["text_dim"]).pack(anchor="w", pady=(12, 4))
            card = Card(self)
            card.pack(fill="x", pady=(0, 8))

            for label, kind, value in items:
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=16, pady=8)
                ctk.CTkLabel(row, text=label, font=FONT_BODY,
                             text_color=COLORS["text"]).pack(side="left")
                if kind == "toggle":
                    var = ctk.BooleanVar(value=value)
                    ctk.CTkSwitch(row, text="", variable=var,
                                  onvalue=True, offvalue=False).pack(side="right")
                elif kind == "dropdown":
                    ctk.CTkOptionMenu(row, values=value, width=120,
                                      fg_color=COLORS["card"]).pack(side="right")

        # About section
        ctk.CTkLabel(self, text="About", font=FONT_H3,
                     text_color=COLORS["text_dim"]).pack(anchor="w", pady=(12, 4))
        about_card = Card(self)
        about_card.pack(fill="x")
        for line in ["PC Manager Lite  v1.0.0",
                     "A lightweight system optimizer for Windows",
                     "Built with Python & CustomTkinter"]:
            ctk.CTkLabel(about_card, text=line, font=FONT_SMALL,
                         text_color=COLORS["text_dim"]).pack(anchor="w", padx=16, pady=3)
        about_card.pack(pady=(0, 24))


# ── MAIN APP ──────────────────────────────────────────────────────────────────

class PCManagerApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("PC Manager Lite")
        self.root.geometry("920x640")
        self.root.minsize(820, 560)
        self.root.configure(fg_color=COLORS["bg"])

        # Load window icon
        try:
            icon_path = resource_path("assets/icon.ico")
            self.root.iconbitmap(icon_path)
        except Exception:
            pass

        self._pages = {}
        self._current_page = None
        self._tray = None
        self._running = True

        self._build_ui()
        self._start_monitor()
        self._setup_tray()

        # Close to tray
        self.root.protocol("WM_DELETE_WINDOW", self._hide_to_tray)

    def _build_ui(self):
        container = ctk.CTkFrame(self.root, fg_color="transparent")
        container.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = Sidebar(container, self._navigate)
        self.sidebar.pack(side="left", fill="y")

        # Divider
        ctk.CTkFrame(container, width=1, fg_color=COLORS["border"]).pack(
            side="left", fill="y")

        # Main content area
        self.content = ctk.CTkFrame(container, fg_color=COLORS["bg"],
                                     corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

        # Build all pages (lazy show/hide)
        self.home_page    = HomePage(self.content, self)
        self.boost_page   = BoostPage(self.content, self)
        self.clean_page   = DeepCleanPage(self.content, self)
        self.process_page = ProcessPage(self.content, self)
        self.startup_page = StartupPage(self.content, self)
        self.health_page  = HealthPage(self.content, self)
        self.settings_page = SettingsPage(self.content, self)

        self._pages = {
            "Home":      self.home_page,
            "Boost":     self.boost_page,
            "Deep Clean": self.clean_page,
            "Processes": self.process_page,
            "Startup":   self.startup_page,
            "Health":    self.health_page,
            "Settings":  self.settings_page,
        }

        self._navigate("Home")

    def _navigate(self, page_name: str):
        if self._current_page:
            self._current_page.pack_forget()
        page = self._pages.get(page_name)
        if page:
            page.pack(fill="both", expand=True, padx=24, pady=16)
            self._current_page = page

    def _start_monitor(self):
        """Background thread to update system stats."""
        def monitor():
            while self._running:
                try:
                    from system_utils import get_system_info
                    info = get_system_info()
                    self.root.after(0, lambda i=info: self.home_page.update_stats(i))
                except Exception:
                    pass
                time.sleep(5)
        threading.Thread(target=monitor, daemon=True).start()

    def _setup_tray(self):
        """Setup system tray icon."""
        try:
            import pystray
            from PIL import Image as PILImage

            icon_path = resource_path("assets/icon.png")
            tray_image = PILImage.open(icon_path).resize((64, 64))

            menu = pystray.Menu(
                pystray.MenuItem("Open PC Manager", self._show_window, default=True),
                pystray.MenuItem("Boost Now", lambda: threading.Thread(
                    target=self.quick_boost, daemon=True).start()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", self._quit),
            )

            self._tray = pystray.Icon(
                "PCManager", tray_image, "PC Manager Lite", menu)
            threading.Thread(target=self._tray.run, daemon=True).start()
        except Exception as e:
            print(f"Tray unavailable: {e}")

    def _hide_to_tray(self):
        self.root.withdraw()

    def _show_window(self, *args):
        self.root.after(0, self.root.deiconify)
        self.root.after(0, self.root.lift)

    def _quit(self, *args):
        self._running = False
        if self._tray:
            try:
                self._tray.stop()
            except Exception:
                pass
        self.root.after(0, self.root.destroy)

    # ── Quick Actions ──────────────────────────────────────────────────────

    def quick_boost(self):
        from system_utils import boost_pc, format_bytes
        result = boost_pc()
        msg = f"Boost: freed {format_bytes(result['freed'])}"
        self.home_page.add_activity(msg)
        self.home_page.set_status(f"✓ {msg}")

    def quick_clean(self):
        from system_utils import deep_cleanup, format_bytes, CLEANUP_TARGETS
        result = deep_cleanup(list(CLEANUP_TARGETS.keys()))
        msg = f"Clean: freed {format_bytes(result['freed'])}"
        self.home_page.add_activity(msg)
        self.home_page.set_status(f"✓ {msg}")

    def quick_health(self):
        self._navigate("Health")
        self.sidebar._select("Health")
        self.root.after(200, self.health_page._run)

    def run(self):
        self.root.mainloop()
