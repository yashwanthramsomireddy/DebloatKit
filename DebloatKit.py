"""
DebloatKit v1.0
Samsung Galaxy Debloater for Windows
Author: Yashwanth Ram Somireddy | TeamExyKings | Chennai, India
License: MIT — Free & Open Source
GitHub: https://github.com/yashwanthramsomireddy/DebloatKit

DISCLAIMER: DebloatKit is an independent open-source tool not affiliated with,
endorsed by, or connected to Samsung Electronics Co., Ltd. Samsung and Galaxy
are trademarks of Samsung Electronics. This tool uses Android's standard ADB
debugging interface.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import os
import sys
import webbrowser
from datetime import datetime

from core.adb_manager import ADBManager, DeviceInfo
from core.app_scanner import AppScanner, AppEntry
from core.debloater import Debloater
from ui.themes import get_theme, get_risk_color, get_state_color, get_risk_label, THEMES

APP_NAME    = "DebloatKit"
APP_VERSION = "v1.0"
APP_AUTHOR  = "Yashwanth Ram Somireddy"
APP_BRAND   = "TeamExyKings"
APP_GITHUB  = "https://github.com/yashwanthramsomireddy/DebloatKit"
APP_LICENSE = "MIT — Free & Open Source"
WINDOW_W    = 1280
WINDOW_H    = 820


class DebloatKit(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.current_theme_name = "Green"
        self.T = get_theme(self.current_theme_name)
        self._apply_ctk_theme()

        self.title(f"{APP_NAME} {APP_VERSION} — {APP_BRAND}")
        self.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.minsize(1100, 700)
        self.configure(fg_color=self.T["bg"])

        # Core modules
        self.adb = ADBManager(log_callback=self._log)
        self.scanner = AppScanner(self.adb, log_callback=self._log)
        self.debloater = Debloater(self.adb, log_callback=self._log)

        # State
        self.device_info: DeviceInfo | None = None
        self.app_data: dict[str, list[AppEntry]] = {
            "system": [], "core": [], "user": [], "thirdparty": [], "keep": []
        }
        self.dry_run_var = tk.BooleanVar(value=False)
        self.compact_var = tk.BooleanVar(value=True)
        self._scanning = False
        self._action_running = False

        self._build_ui()
        self._start_device_polling()

    # ─── Theme ────────────────────────────────────────────────────────────────

    def _apply_ctk_theme(self):
        ctk.set_appearance_mode("dark" if self.T["bg"] < "#888888" else "light")
        ctk.set_default_color_theme("green")

    def _switch_theme(self, name: str):
        self.current_theme_name = name
        self.T = get_theme(name)
        self._apply_ctk_theme()
        self._rebuild_ui()

    def _rebuild_ui(self):
        for w in self.winfo_children():
            w.destroy()
        self.configure(fg_color=self.T["bg"])
        self._build_ui()
        if self.device_info:
            self._refresh_device_card()
        self._refresh_all_tabs()

    # ─── UI Construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        T = self.T
        # Topbar
        self.topbar = ctk.CTkFrame(self, fg_color=T["topbar_bg"], height=52, corner_radius=0)
        self.topbar.pack(fill="x", side="top")
        self.topbar.pack_propagate(False)
        self._build_topbar()

        # Main body
        self.body = ctk.CTkFrame(self, fg_color=T["bg"], corner_radius=0)
        self.body.pack(fill="both", expand=True)

        # Tabview
        self.tabview = ctk.CTkTabview(
            self.body,
            fg_color=T["bg_card"],
            segmented_button_fg_color=T["bg"],
            segmented_button_selected_color=T["accent"],
            segmented_button_selected_hover_color=T["accent_dim"],
            segmented_button_unselected_color=T["bg"],
            segmented_button_unselected_hover_color=T["bg_hover"],
            text_color=T["text"],
            text_color_disabled=T["text_dim"],
            corner_radius=8
        )
        self.tabview.pack(fill="both", expand=True, padx=12, pady=(8, 0))

        # Create tabs
        self.tab_system     = self.tabview.add("  System Apps  ")
        self.tab_core       = self.tabview.add("  Core Apps  ")
        self.tab_user       = self.tabview.add("  User Apps  ")
        self.tab_thirdparty = self.tabview.add("  3rd Party  ")
        self.tab_logs       = self.tabview.add("  Logs  ")
        self.tab_settings   = self.tabview.add("  Settings  ")
        self.tab_about      = self.tabview.add("  About  ")

        # Device info strip
        self.device_strip = ctk.CTkFrame(self.body, fg_color=T["bg_card"], height=42, corner_radius=6)
        self.device_strip.pack(fill="x", padx=12, pady=(4, 0))
        self.device_strip.pack_propagate(False)
        self._build_device_strip()

        # Log strip at bottom
        self.log_strip = ctk.CTkFrame(self.body, fg_color=T["log_bg"], height=110, corner_radius=0)
        self.log_strip.pack(fill="x", side="bottom")
        self.log_strip.pack_propagate(False)
        self._build_log_strip()

        # Build tab contents
        self._build_app_tab(self.tab_system, "system")
        self._build_core_tab()
        self._build_app_tab(self.tab_user, "user")
        self._build_app_tab(self.tab_thirdparty, "thirdparty")
        self._build_logs_tab()
        self._build_settings_tab()
        self._build_about_tab()

    def _build_topbar(self):
        T = self.T
        tb = self.topbar

        # Left — logo
        left = ctk.CTkFrame(tb, fg_color="transparent")
        left.pack(side="left", padx=16, pady=8)

        ctk.CTkLabel(left, text="⬡", font=("Segoe UI", 22), text_color=T["accent"]).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(left, text=APP_NAME, font=("Segoe UI", 16, "bold"), text_color=T["text"]).pack(side="left")
        ctk.CTkLabel(left, text=APP_VERSION, font=("Segoe UI", 11), text_color=T["text_muted"]).pack(side="left", padx=(4, 0), pady=(4, 0))

        # Right — controls
        right = ctk.CTkFrame(tb, fg_color="transparent")
        right.pack(side="right", padx=16, pady=8)

        # Dry Run
        ctk.CTkLabel(right, text="Dry Run", font=("Segoe UI", 12), text_color=T["text_muted"]).pack(side="left", padx=(0, 4))
        self.dry_run_switch = ctk.CTkSwitch(
            right, variable=self.dry_run_var, text="",
            progress_color=T["warning"], button_color=T["warning"],
            width=42, command=self._on_dry_run_toggle
        )
        self.dry_run_switch.pack(side="left", padx=(0, 16))

        # Compact toggle
        ctk.CTkLabel(right, text="Compact", font=("Segoe UI", 12), text_color=T["text_muted"]).pack(side="left", padx=(0, 4))
        self.compact_switch = ctk.CTkSwitch(
            right, variable=self.compact_var, text="",
            progress_color=T["accent"], button_color=T["accent"],
            width=42, command=self._refresh_all_tabs
        )
        self.compact_switch.pack(side="left", padx=(0, 20))

        # Connection status
        self.status_dot = ctk.CTkLabel(right, text="●", font=("Segoe UI", 14), text_color="#444444")
        self.status_dot.pack(side="left", padx=(0, 4))
        self.status_label = ctk.CTkLabel(right, text="No Device", font=("Segoe UI", 12), text_color=T["text_muted"])
        self.status_label.pack(side="left")

    def _build_device_strip(self):
        T = self.T
        ds = self.device_strip

        self.dev_model_lbl  = ctk.CTkLabel(ds, text="No device connected", font=("Segoe UI", 12, "bold"), text_color=T["text_muted"])
        self.dev_model_lbl.pack(side="left", padx=14, pady=10)

        self.dev_info_lbl   = ctk.CTkLabel(ds, text="Connect your device via USB and enable USB Debugging", font=("Segoe UI", 11), text_color=T["text_dim"])
        self.dev_info_lbl.pack(side="left", padx=4)

        self.scan_btn = ctk.CTkButton(
            ds, text="Scan Device", font=("Segoe UI", 12, "bold"),
            fg_color=T["accent"], text_color=T["btn_primary_text"],
            hover_color=T["accent_dim"], width=120, height=28,
            command=self._start_scan, state="disabled"
        )
        self.scan_btn.pack(side="right", padx=12)

        self.bat_lbl = ctk.CTkLabel(ds, text="", font=("Segoe UI", 11), text_color=T["text_muted"])
        self.bat_lbl.pack(side="right", padx=6)

    def _build_log_strip(self):
        T = self.T
        ls = self.log_strip

        hdr = ctk.CTkFrame(ls, fg_color="transparent")
        hdr.pack(fill="x", padx=8, pady=(4, 0))
        ctk.CTkLabel(hdr, text="LOG", font=("Segoe UI", 10, "bold"), text_color=T["accent"]).pack(side="left")
        ctk.CTkButton(
            hdr, text="Clear", font=("Segoe UI", 10),
            fg_color="transparent", text_color=T["text_dim"],
            hover_color=T["bg_hover"], width=40, height=18,
            command=self._clear_log_strip
        ).pack(side="right")

        self.log_strip_text = ctk.CTkTextbox(
            ls, fg_color=T["log_bg"], text_color=T["text"],
            font=("Consolas", 11), height=80, corner_radius=0,
            scrollbar_button_color=T["scrollbar"]
        )
        self.log_strip_text.pack(fill="both", expand=True, padx=6, pady=(0, 4))
        self.log_strip_text.configure(state="disabled")

    # ─── App Tab (reused for System, User, 3rd Party) ─────────────────────────

    def _build_app_tab(self, parent: ctk.CTkFrame, category: str):
        T = self.T

        # Filter bar
        filter_bar = ctk.CTkFrame(parent, fg_color="transparent")
        filter_bar.pack(fill="x", pady=(8, 4), padx=8)

        search_var = tk.StringVar()
        search_box = ctk.CTkEntry(
            filter_bar, placeholder_text="Search packages...",
            textvariable=search_var, width=240, height=30,
            fg_color=T["bg_card"], border_color=T["border"],
            text_color=T["text"]
        )
        search_box.pack(side="left", padx=(0, 8))

        # Subcategory filter
        subcat_var = tk.StringVar(value="All")
        self.__dict__[f"subcat_var_{category}"] = subcat_var
        subcat_menu = ctk.CTkOptionMenu(
            filter_bar, variable=subcat_var,
            values=["All"], width=160, height=30,
            fg_color=T["bg_card"], button_color=T["accent"],
            dropdown_fg_color=T["bg_card"], text_color=T["text"],
            command=lambda v, c=category: self._filter_tab(c)
        )
        subcat_menu.pack(side="left", padx=(0, 8))
        self.__dict__[f"subcat_menu_{category}"] = subcat_menu

        count_lbl = ctk.CTkLabel(filter_bar, text="0 packages", font=("Segoe UI", 11), text_color=T["text_muted"])
        count_lbl.pack(side="left", padx=8)
        self.__dict__[f"count_lbl_{category}"] = count_lbl

        # Scrollable list
        scroll = ctk.CTkScrollableFrame(
            parent, fg_color=T["bg"],
            scrollbar_button_color=T["scrollbar"],
            scrollbar_button_hover_color=T["accent"]
        )
        scroll.pack(fill="both", expand=True, padx=8, pady=4)
        self.__dict__[f"scroll_{category}"] = scroll

        # Action bar at bottom
        action_bar = ctk.CTkFrame(parent, fg_color=T["bg_card"], height=48, corner_radius=6)
        action_bar.pack(fill="x", padx=8, pady=(4, 8))
        action_bar.pack_propagate(False)
        self._build_action_bar(action_bar, category)

        # Bind search
        search_var.trace_add("write", lambda *a, c=category, sv=search_var: self._filter_tab(c, sv.get()))
        self.__dict__[f"search_var_{category}"] = search_var

    def _build_action_bar(self, parent, category: str):
        T = self.T

        ctk.CTkButton(
            parent, text="Select All", font=("Segoe UI", 11),
            fg_color=T["bg_hover"], text_color=T["text"], hover_color=T["border"],
            width=90, height=30,
            command=lambda c=category: self._select_all(c, True)
        ).pack(side="left", padx=(10, 4), pady=9)

        ctk.CTkButton(
            parent, text="Deselect All", font=("Segoe UI", 11),
            fg_color=T["bg_hover"], text_color=T["text"], hover_color=T["border"],
            width=95, height=30,
            command=lambda c=category: self._select_all(c, False)
        ).pack(side="left", padx=4, pady=9)

        # Progress bar (hidden by default)
        prog = ctk.CTkProgressBar(parent, fg_color=T["progress_bg"], progress_color=T["accent"], height=6)
        prog.set(0)
        prog.pack(side="left", padx=16, pady=16, fill="x", expand=True)
        prog.pack_forget()
        self.__dict__[f"prog_{category}"] = prog

        ctk.CTkButton(
            parent, text="Disable Selected", font=("Segoe UI", 11, "bold"),
            fg_color=T["bg_hover"], text_color=T["warning"], hover_color=T["bg_hover"],
            border_width=1, border_color=T["warning"],
            width=130, height=30,
            command=lambda c=category: self._run_action(c, "disable")
        ).pack(side="right", padx=4, pady=9)

        ctk.CTkButton(
            parent, text="Uninstall Selected", font=("Segoe UI", 11, "bold"),
            fg_color=T["btn_danger"], text_color="#ffffff", hover_color="#cc0033",
            width=140, height=30,
            command=lambda c=category: self._run_action(c, "uninstall")
        ).pack(side="right", padx=(4, 10), pady=9)

    def _build_core_tab(self):
        T = self.T
        parent = self.tab_core

        # Warning banner
        warn_frame = ctk.CTkFrame(parent, fg_color="#1a0505", corner_radius=6, border_width=1, border_color=T["core_red"])
        warn_frame.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkLabel(
            warn_frame,
            text="⛔  Core system apps — disabling may affect device stability. "
                 "Each app requires individual confirmation. All changes are reversible via Re-enable or Panic Restore.",
            font=("Segoe UI", 11), text_color=T["core_red"], wraplength=900
        ).pack(padx=12, pady=8)

        # Filter
        filter_bar = ctk.CTkFrame(parent, fg_color="transparent")
        filter_bar.pack(fill="x", pady=(0, 4), padx=8)

        search_var = tk.StringVar()
        ctk.CTkEntry(
            filter_bar, placeholder_text="Search core packages...",
            textvariable=search_var, width=240, height=30,
            fg_color=T["bg_card"], border_color=T["border"], text_color=T["text"]
        ).pack(side="left")

        count_lbl = ctk.CTkLabel(filter_bar, text="0 packages", font=("Segoe UI", 11), text_color=T["text_muted"])
        count_lbl.pack(side="left", padx=12)
        self.count_lbl_core = count_lbl

        scroll = ctk.CTkScrollableFrame(
            parent, fg_color=T["bg"],
            scrollbar_button_color=T["scrollbar"],
            scrollbar_button_hover_color=T["core_red"]
        )
        scroll.pack(fill="both", expand=True, padx=8, pady=4)
        self.scroll_core = scroll

        # Action bar
        action_bar = ctk.CTkFrame(parent, fg_color=T["bg_card"], height=48, corner_radius=6)
        action_bar.pack(fill="x", padx=8, pady=(4, 8))
        action_bar.pack_propagate(False)

        ctk.CTkButton(
            action_bar, text="Deselect All", font=("Segoe UI", 11),
            fg_color=T["bg_hover"], text_color=T["text"], hover_color=T["border"],
            width=95, height=30,
            command=lambda: self._select_all("core", False)
        ).pack(side="left", padx=(10, 4), pady=9)

        self.prog_core = ctk.CTkProgressBar(action_bar, fg_color=T["progress_bg"], progress_color=T["core_red"], height=6)
        self.prog_core.set(0)
        self.prog_core.pack(side="left", padx=16, pady=16, fill="x", expand=True)
        self.prog_core.pack_forget()

        ctk.CTkButton(
            action_bar, text="Disable Selected", font=("Segoe UI", 11, "bold"),
            fg_color=T["bg_hover"], text_color=T["warning"], hover_color=T["bg_hover"],
            border_width=1, border_color=T["warning"], width=130, height=30,
            command=lambda: self._run_action("core", "disable")
        ).pack(side="right", padx=4, pady=9)

        ctk.CTkButton(
            action_bar, text="Uninstall Selected", font=("Segoe UI", 11, "bold"),
            fg_color=T["btn_danger"], text_color="#ffffff", hover_color="#cc0033",
            width=140, height=30,
            command=lambda: self._run_action("core", "uninstall")
        ).pack(side="right", padx=(4, 10), pady=9)

        search_var.trace_add("write", lambda *a: self._filter_tab("core", search_var.get()))
        self.search_var_core = search_var

    def _build_logs_tab(self):
        T = self.T
        parent = self.tab_logs

        toolbar = ctk.CTkFrame(parent, fg_color="transparent")
        toolbar.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkButton(
            toolbar, text="Export Log", font=("Segoe UI", 11),
            fg_color=T["bg_card"], text_color=T["text"], hover_color=T["bg_hover"],
            width=100, height=28, command=self._export_log
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            toolbar, text="Clear Log", font=("Segoe UI", 11),
            fg_color=T["bg_card"], text_color=T["text_muted"], hover_color=T["bg_hover"],
            width=80, height=28, command=self._clear_full_log
        ).pack(side="left")

        self.full_log = ctk.CTkTextbox(
            parent, fg_color=T["log_bg"], text_color=T["text"],
            font=("Consolas", 12), corner_radius=6,
            scrollbar_button_color=T["scrollbar"]
        )
        self.full_log.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.full_log.configure(state="disabled")

    def _build_settings_tab(self):
        T = self.T
        parent = self.tab_settings

        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=8)

        def section(title: str):
            ctk.CTkLabel(scroll, text=title, font=("Segoe UI", 12, "bold"), text_color=T["accent"]).pack(anchor="w", pady=(12, 4))
            ctk.CTkFrame(scroll, fg_color=T["border"], height=1).pack(fill="x", pady=(0, 8))

        def row(label: str, widget_fn):
            f = ctk.CTkFrame(scroll, fg_color="transparent")
            f.pack(fill="x", pady=4)
            ctk.CTkLabel(f, text=label, font=("Segoe UI", 12), text_color=T["text"], width=200, anchor="w").pack(side="left")
            widget_fn(f)

        # ADB
        section("ADB Configuration")
        self.adb_path_var = tk.StringVar(value=self.adb.adb_path)

        def adb_row(f):
            e = ctk.CTkEntry(f, textvariable=self.adb_path_var, width=300, fg_color=T["bg_card"],
                             border_color=T["border"], text_color=T["text"])
            e.pack(side="left", padx=(0, 6))
            ctk.CTkButton(f, text="Browse", width=70, height=28, fg_color=T["bg_hover"],
                          text_color=T["text"], command=self._browse_adb).pack(side="left", padx=(0, 6))
            ctk.CTkButton(f, text="Test ADB", width=80, height=28, fg_color=T["accent"],
                          text_color=T["btn_primary_text"], command=self._test_adb).pack(side="left")
        row("ADB executable path", adb_row)

        # Backup
        section("Backup")
        self.backup_path_var = tk.StringVar(value=self.debloater.backup_dir)

        def backup_row(f):
            e = ctk.CTkEntry(f, textvariable=self.backup_path_var, width=300, fg_color=T["bg_card"],
                             border_color=T["border"], text_color=T["text"])
            e.pack(side="left", padx=(0, 6))
            ctk.CTkButton(f, text="Browse", width=70, height=28, fg_color=T["bg_hover"],
                          text_color=T["text"], command=self._browse_backup).pack(side="left")
        row("Backup folder", backup_row)

        ctk.CTkButton(
            scroll, text="Open Backup Folder", font=("Segoe UI", 11),
            fg_color=T["bg_card"], text_color=T["text"], hover_color=T["bg_hover"],
            width=160, command=lambda: os.startfile(self.debloater.backup_dir) if os.path.exists(self.debloater.backup_dir) else None
        ).pack(anchor="w", pady=4)

        # Theme
        section("Appearance")

        def theme_row(f):
            for name in THEMES:
                t = get_theme(name)
                ctk.CTkButton(
                    f, text=name, width=80, height=28,
                    fg_color=t["accent"], text_color=t["btn_primary_text"],
                    command=lambda n=name: self._switch_theme(n)
                ).pack(side="left", padx=(0, 6))
        row("Theme", theme_row)

        # Panic restore
        section("Emergency Recovery")
        ctk.CTkButton(
            scroll, text="⚡  Panic Restore (latest backup)", font=("Segoe UI", 12, "bold"),
            fg_color=T["core_red"], text_color="#ffffff", hover_color="#cc0000",
            width=260, height=36,
            command=self._panic_restore
        ).pack(anchor="w", pady=8)
        ctk.CTkLabel(
            scroll,
            text="Re-enables ALL packages from the most recent automatic backup.\n"
                 "Use this if your device has issues after debloating.",
            font=("Segoe UI", 11), text_color=T["text_muted"]
        ).pack(anchor="w")

    def _build_about_tab(self):
        T = self.T
        parent = self.tab_about

        outer = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        outer.pack(fill="both", expand=True)

        card = ctk.CTkFrame(outer, fg_color=T["bg_card"], corner_radius=12, border_width=1, border_color=T["border"])
        card.pack(padx=40, pady=20, fill="x")

        # Logo row
        logo_row = ctk.CTkFrame(card, fg_color="transparent")
        logo_row.pack(pady=(24, 4))
        ctk.CTkLabel(logo_row, text="⬡", font=("Segoe UI", 44), text_color=T["accent"]).pack()
        ctk.CTkLabel(logo_row, text=APP_NAME, font=("Segoe UI", 26, "bold"), text_color=T["text"]).pack()
        ctk.CTkLabel(logo_row, text=f"{APP_VERSION}  —  Samsung Galaxy Debloater for Windows", font=("Segoe UI", 12), text_color=T["text_muted"]).pack(pady=(0, 4))

        # Info rows
        ctk.CTkFrame(card, fg_color=T["border"], height=1).pack(fill="x", padx=24, pady=12)

        info_grid = ctk.CTkFrame(card, fg_color=T["bg"], corner_radius=8)
        info_grid.pack(fill="x", padx=24, pady=(0, 8))

        def info_row(label: str, value: str, value_color: str = None):
            f = ctk.CTkFrame(info_grid, fg_color="transparent")
            f.pack(fill="x", padx=16, pady=6)
            ctk.CTkLabel(f, text=label, font=("Segoe UI", 11), text_color=T["text_muted"], width=120, anchor="w").pack(side="left")
            ctk.CTkLabel(f, text=value, font=("Segoe UI", 11, "bold"), text_color=value_color or T["text"]).pack(side="left")

        info_row("Built by", APP_AUTHOR)
        info_row("Brand", APP_BRAND, T["accent"])
        info_row("Location", "Chennai, India")
        info_row("License", APP_LICENSE, T["accent"])
        info_row("Platform", "Windows 10 / 11")
        info_row("Version", APP_VERSION)

        ctk.CTkFrame(card, fg_color=T["border"], height=1).pack(fill="x", padx=24, pady=12)

        # GitHub
        ctk.CTkLabel(card, text="GitHub Repository", font=("Segoe UI", 11), text_color=T["text_muted"]).pack()
        ctk.CTkButton(
            card, text=APP_GITHUB, font=("Segoe UI", 11),
            fg_color=T["accent"], text_color=T["btn_primary_text"],
            hover_color=T["accent_dim"], width=420, height=34,
            command=lambda: webbrowser.open(APP_GITHUB)
        ).pack(pady=(4, 12))

        # Donate
        ctk.CTkFrame(card, fg_color=T["border"], height=1).pack(fill="x", padx=24, pady=(0, 12))
        ctk.CTkLabel(card, text="☕  Support Development", font=("Segoe UI", 13, "bold"), text_color=T["text"]).pack()
        ctk.CTkLabel(
            card,
            text="DebloatKit is free and open source. If it helped you, consider buying me a coffee!",
            font=("Segoe UI", 11), text_color=T["text_muted"]
        ).pack(pady=(2, 8))

        donate_row = ctk.CTkFrame(card, fg_color="transparent")
        donate_row.pack(pady=(0, 16))
        ctk.CTkButton(
            donate_row, text="Buy Me a Coffee", font=("Segoe UI", 11, "bold"),
            fg_color="#FFDD00", text_color="#000000", width=160, height=34,
            command=lambda: webbrowser.open("https://buymeacoffee.com/yashwanthramsomireddy")
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            donate_row, text="UPI / GPay", font=("Segoe UI", 11),
            fg_color=T["bg_hover"], text_color=T["text"], width=120, height=34,
            command=lambda: messagebox.showinfo("UPI", "UPI ID: yashwanthramsomireddy@okaxis\n\nThank you for your support!")
        ).pack(side="left", padx=6)

        # Disclaimer
        ctk.CTkFrame(card, fg_color=T["border"], height=1).pack(fill="x", padx=24, pady=(0, 12))
        ctk.CTkLabel(
            card,
            text="DebloatKit is an independent open-source tool not affiliated with, endorsed by, or connected to\n"
                 "Samsung Electronics Co., Ltd. Samsung and Galaxy are trademarks of Samsung Electronics.\n"
                 "Credits: XDA Developers community · @Vordx · Universal Android Debloater project",
            font=("Segoe UI", 10), text_color=T["text_dim"], justify="center"
        ).pack(pady=(0, 20))

    # ─── Package Rows ─────────────────────────────────────────────────────────

    def _build_package_row(self, parent, entry: AppEntry, compact: bool = True) -> ctk.CTkFrame:
        T = self.T
        is_keep = entry.risk == "KEEP"
        is_core = entry.risk == "CORE"
        row_h = 36 if compact else 56

        row = ctk.CTkFrame(
            parent,
            fg_color=T["bg_card"] if entry.state == "enabled" else T["disabled_bg"],
            corner_radius=4, height=row_h
        )
        row.pack(fill="x", pady=1, padx=2)
        row.pack_propagate(False)

        # Checkbox
        var = tk.BooleanVar(value=entry.checked)
        cb = ctk.CTkCheckBox(
            row, variable=var, text="",
            width=20,
            checkbox_width=16, checkbox_height=16,
            fg_color=T["core_red"] if is_core else T["accent"],
            hover_color=T["accent_dim"],
            state="disabled" if is_keep else "normal",
            command=lambda e=entry, v=var: self._on_check(e, v, is_core)
        )
        cb.pack(side="left", padx=(8, 4), pady=10)
        entry._var = var
        entry._row = row

        # Risk badge
        risk_color = get_risk_color(entry.risk, self.current_theme_name)
        badge_frame = ctk.CTkFrame(row, fg_color="transparent", width=100)
        badge_frame.pack(side="left", padx=4)
        badge_frame.pack_propagate(False)
        ctk.CTkLabel(
            badge_frame,
            text=get_risk_label(entry.risk),
            font=("Segoe UI", 10, "bold"),
            text_color=risk_color
        ).pack(anchor="w", pady=10)

        # Name + package
        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=4)

        name_text = entry.name if entry.in_db else f"{entry.name} *"
        ctk.CTkLabel(
            info_frame,
            text=name_text,
            font=("Segoe UI", 12, "bold"),
            text_color=T["text_dim"] if is_keep else T["text"],
            anchor="w"
        ).pack(anchor="w", pady=(8, 0) if not compact else 0, padx=2)

        if not compact:
            ctk.CTkLabel(
                info_frame,
                text=entry.pkg,
                font=("Consolas", 10),
                text_color=T["text_muted"],
                anchor="w"
            ).pack(anchor="w", padx=2)
            if entry.description:
                ctk.CTkLabel(
                    info_frame,
                    text=entry.description,
                    font=("Segoe UI", 10),
                    text_color=T["text_dim"],
                    anchor="w"
                ).pack(anchor="w", padx=2, pady=(0, 6))

        # Package name (compact — show on hover via tooltip approach)
        if compact:
            ctk.CTkLabel(
                info_frame,
                text=entry.pkg,
                font=("Consolas", 10),
                text_color=T["text_dim"],
                anchor="w"
            ).pack(anchor="w", pady=2)

        # Subcategory
        if entry.subcategory:
            ctk.CTkLabel(
                row,
                text=entry.subcategory,
                font=("Segoe UI", 10),
                text_color=T["text_dim"],
                width=110, anchor="e"
            ).pack(side="right", padx=4)

        # State indicator
        state_color = get_state_color(entry.state)
        state_lbl = ctk.CTkLabel(
            row, text=entry.state.title(),
            font=("Segoe UI", 10, "bold"),
            text_color=state_color, width=70, anchor="e"
        )
        state_lbl.pack(side="right", padx=4)
        entry._state_lbl = state_lbl
        entry._row_frame = row

        # Re-enable button (shows when disabled/uninstalled)
        if entry.state in ("disabled", "uninstalled"):
            re_btn = ctk.CTkButton(
                row, text="Re-enable", font=("Segoe UI", 10),
                fg_color=T["accent"], text_color=T["btn_primary_text"],
                hover_color=T["accent_dim"], width=80, height=24,
                command=lambda e=entry: self._reenable_single(e)
            )
            re_btn.pack(side="right", padx=4)
            entry._re_btn = re_btn

        return row

    # ─── Tab Rendering ────────────────────────────────────────────────────────

    def _render_tab(self, category: str, entries: list[AppEntry] = None):
        T = self.T
        compact = self.compact_var.get()
        scroll = self.__dict__.get(f"scroll_{category}")
        if not scroll:
            return

        for w in scroll.winfo_children():
            w.destroy()

        entries = entries or self.app_data.get(category, [])
        if not entries:
            ctk.CTkLabel(
                scroll,
                text="No packages found. Scan your device first." if not self.device_info else "No packages in this category.",
                font=("Segoe UI", 12), text_color=T["text_muted"]
            ).pack(pady=40)
            self._update_count(category, 0)
            return

        # Group by subcategory
        subcats: dict[str, list[AppEntry]] = {}
        for e in entries:
            subcats.setdefault(e.subcategory or "Other", []).append(e)

        total = 0
        for subcat, items in subcats.items():
            # Subcategory header
            hdr = ctk.CTkFrame(scroll, fg_color="transparent")
            hdr.pack(fill="x", pady=(8, 2))
            ctk.CTkLabel(
                hdr, text=subcat.upper(),
                font=("Segoe UI", 10, "bold"),
                text_color=T["accent"] if category != "core" else T["core_red"]
            ).pack(side="left", padx=4)
            ctk.CTkFrame(hdr, fg_color=T["border"], height=1).pack(side="left", fill="x", expand=True, padx=4, pady=5)
            ctk.CTkLabel(hdr, text=str(len(items)), font=("Segoe UI", 10), text_color=T["text_dim"]).pack(side="right", padx=4)

            for entry in items:
                self._build_package_row(scroll, entry, compact=compact)
                total += 1

        self._update_count(category, total)
        self._update_subcat_filter(category)

    def _update_count(self, category: str, count: int):
        lbl = self.__dict__.get(f"count_lbl_{category}")
        if lbl:
            lbl.configure(text=f"{count} packages")

    def _update_subcat_filter(self, category: str):
        menu = self.__dict__.get(f"subcat_menu_{category}")
        if not menu:
            return
        entries = self.app_data.get(category, [])
        subcats = sorted(set(e.subcategory for e in entries if e.subcategory))
        menu.configure(values=["All"] + subcats)

    def _filter_tab(self, category: str, query: str = ""):
        entries = self.app_data.get(category, [])
        subcat_var = self.__dict__.get(f"subcat_var_{category}")
        selected_subcat = subcat_var.get() if subcat_var else "All"

        filtered = entries
        if selected_subcat != "All":
            filtered = [e for e in filtered if e.subcategory == selected_subcat]
        if query:
            q = query.lower()
            filtered = [e for e in filtered if q in e.pkg.lower() or q in e.name.lower()]

        self._render_tab(category, filtered)

    def _refresh_all_tabs(self):
        for cat in ("system", "core", "user", "thirdparty"):
            self._render_tab(cat)

    # ─── Checkbox / Selection ────────────────────────────────────────────────

    def _on_check(self, entry: AppEntry, var: tk.BooleanVar, is_core: bool):
        if is_core and var.get():
            self._show_core_warning(entry, var)
        else:
            entry.checked = var.get()

    def _show_core_warning(self, entry: AppEntry, var: tk.BooleanVar):
        T = self.T
        win = ctk.CTkToplevel(self)
        win.title("Core System App — Confirmation Required")
        win.geometry("520x300")
        win.configure(fg_color=T["bg"])
        win.grab_set()
        win.resizable(False, False)

        ctk.CTkLabel(win, text="⛔  Core System App", font=("Segoe UI", 16, "bold"), text_color=T["core_red"]).pack(pady=(20, 4))
        ctk.CTkLabel(win, text=f"{entry.name}", font=("Segoe UI", 13, "bold"), text_color=T["text"]).pack()
        ctk.CTkLabel(win, text=entry.pkg, font=("Consolas", 10), text_color=T["text_muted"]).pack(pady=(0, 8))

        msg_frame = ctk.CTkFrame(win, fg_color="#1a0505", corner_radius=8, border_width=1, border_color=T["core_red"])
        msg_frame.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(
            msg_frame,
            text=f"{entry.description}\n\n"
                 "⚠ Disabling this may affect device stability.\n"
                 "✓ Fully reversible — re-enable anytime while device is connected.",
            font=("Segoe UI", 11), text_color=T["text"], wraplength=440, justify="left"
        ).pack(padx=12, pady=10)

        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(pady=16)

        def on_cancel():
            var.set(False)
            entry.checked = False
            win.destroy()

        def on_proceed():
            entry.checked = True
            win.destroy()

        ctk.CTkButton(btn_row, text="Cancel", width=120, fg_color=T["bg_hover"], text_color=T["text"], command=on_cancel).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="I understand, proceed", width=160, fg_color=T["core_red"], text_color="#ffffff", command=on_proceed).pack(side="left", padx=8)

    def _select_all(self, category: str, state: bool):
        entries = self.app_data.get(category, [])
        for e in entries:
            if e.risk != "KEEP":
                if not state or e.risk != "CORE":
                    e.checked = state
                    if hasattr(e, "_var"):
                        e._var.set(state)

    # ─── Actions ──────────────────────────────────────────────────────────────

    def _run_action(self, category: str, action: str):
        if self._action_running:
            messagebox.showwarning("Busy", "An action is already running. Please wait.")
            return
        if not self.device_info:
            messagebox.showerror("No Device", "Connect your device first.")
            return

        entries = self.app_data.get(category, [])
        selected = [e for e in entries if e.checked and e.risk != "KEEP"]
        if not selected:
            messagebox.showinfo("Nothing Selected", "Select at least one package first.")
            return

        verb = "disable" if action == "disable" else "uninstall"
        if not messagebox.askyesno(
            f"Confirm {verb.title()}",
            f"{'[DRY RUN] ' if self.dry_run_var.get() else ''}"
            f"{verb.title()} {len(selected)} selected package(s)?\n\n"
            "All changes are reversible via Re-enable or Panic Restore."
        ):
            return

        self._action_running = True
        prog = self.__dict__.get(f"prog_{category}")
        if prog:
            prog.pack(side="left", padx=16, pady=16, fill="x", expand=True)
            prog.set(0)

        all_entries = [e for cat_entries in self.app_data.values() for e in cat_entries]

        def progress_cb(val, msg):
            self.after(0, lambda: prog.set(val) if prog else None)
            self._log(msg, "info")

        def result_cb(entry: AppEntry, result):
            def update():
                if hasattr(entry, "_state_lbl"):
                    entry._state_lbl.configure(
                        text=entry.state.title(),
                        text_color=get_state_color(entry.state)
                    )
                if hasattr(entry, "_row_frame") and entry.state in ("disabled", "uninstalled"):
                    entry._row_frame.configure(fg_color=self.T["disabled_bg"])
            self.after(0, update)

        def run():
            if action == "disable":
                results = self.debloater.disable_packages(selected, all_entries, progress_cb, result_cb)
            else:
                results = self.debloater.uninstall_packages(selected, all_entries, progress_cb, result_cb)

            summary = self.debloater.get_summary(results)
            self.after(0, lambda: self._show_summary(summary, action))
            self.after(0, lambda: prog.pack_forget() if prog else None)
            self._action_running = False

            # SoundAlive hint
            diag_pkg = "com.sec.android.diagmonagent"
            if any(e.pkg == diag_pkg for e in selected):
                self.after(0, self._offer_soundalive_fix)

        threading.Thread(target=run, daemon=True).start()

    def _reenable_single(self, entry: AppEntry):
        if not self.device_info:
            messagebox.showerror("No Device", "Device not connected.")
            return

        def run():
            if entry.state == "disabled":
                ok, msg = self.adb.enable_package(entry.pkg)
            else:
                ok, msg = self.adb.reinstall_package(entry.pkg)

            def update():
                if ok:
                    entry.state = "enabled"
                    if hasattr(entry, "_state_lbl"):
                        entry._state_lbl.configure(text="Enabled", text_color=get_state_color("enabled"))
                    if hasattr(entry, "_row_frame"):
                        entry._row_frame.configure(fg_color=self.T["bg_card"])
                    if hasattr(entry, "_re_btn"):
                        entry._re_btn.destroy()
            self.after(0, update)

        threading.Thread(target=run, daemon=True).start()

    def _offer_soundalive_fix(self):
        if messagebox.askyesno(
            "SoundAlive Fix",
            "You disabled the Diagnostic Monitor (diagmonagent).\n\n"
            "Run SoundAlive flush to fix potential audio issues?\n"
            "(Recommended — clears SoundAlive cache)"
        ):
            self.debloater.soundalive_fix()

    def _show_summary(self, summary: dict, action: str):
        T = self.T
        win = ctk.CTkToplevel(self)
        win.title("Action Complete")
        win.geometry("380x220")
        win.configure(fg_color=T["bg"])
        win.grab_set()

        ctk.CTkLabel(win, text="✓ Complete", font=("Segoe UI", 16, "bold"), text_color=T["success"]).pack(pady=(20, 8))

        info = ctk.CTkFrame(win, fg_color=T["bg_card"], corner_radius=8)
        info.pack(fill="x", padx=24, pady=4)

        def row(label, value, color=None):
            f = ctk.CTkFrame(info, fg_color="transparent")
            f.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(f, text=label, font=("Segoe UI", 11), text_color=T["text_muted"]).pack(side="left")
            ctk.CTkLabel(f, text=str(value), font=("Segoe UI", 11, "bold"), text_color=color or T["text"]).pack(side="right")

        row("Action", action.title())
        row("Total", summary["total"])
        row("Succeeded", summary["success"], T["success"])
        if summary["failed"] > 0:
            row("Failed", summary["failed"], T["error"])
        if not summary["dry_run"]:
            row("Backup", "Saved automatically", T["accent"])
        else:
            row("Mode", "DRY RUN — no changes made", T["warning"])

        ctk.CTkButton(win, text="Close", fg_color=T["accent"], text_color=T["btn_primary_text"],
                      width=100, command=win.destroy).pack(pady=16)

    # ─── Device Polling & Scan ────────────────────────────────────────────────

    def _start_device_polling(self):
        self.adb.start_polling(
            on_status_change=self._on_device_status,
            on_connected=self._on_device_connected,
            on_disconnected=self._on_device_disconnected
        )

    def _on_device_status(self, status: str):
        colors = {"no_device": "#444444", "unauthorized": "#ffab00", "ready": "#00e676"}
        labels = {"no_device": "No Device", "unauthorized": "Unauthorized", "ready": "Connected"}
        color = colors.get(status, "#444444")
        label = labels.get(status, status)

        def update():
            self.status_dot.configure(text_color=color)
            self.status_label.configure(text=label)
            if status == "unauthorized":
                self._show_usb_guide()
        self.after(0, update)

    def _on_device_connected(self, info: DeviceInfo):
        self.device_info = info

        def update():
            self.dev_model_lbl.configure(
                text=f"{info.brand} {info.model}",
                text_color=self.T["text"]
            )
            bat_color = self.T["error"] if info.battery_level < 20 else self.T["text_muted"]
            self.dev_info_lbl.configure(
                text=f"Android {info.android_version}  ·  One UI {info.oneui_version or '?'}  ·  API {info.api_level}  ·  {info.get_era_label()}",
                text_color=self.T["text_muted"]
            )
            self.bat_lbl.configure(text=f"🔋 {info.battery_level}%", text_color=bat_color)
            self.scan_btn.configure(state="normal")
        self.after(0, update)

    def _on_device_disconnected(self):
        self.device_info = None

        def update():
            self.dev_model_lbl.configure(text="No device connected", text_color=self.T["text_muted"])
            self.dev_info_lbl.configure(text="Connect your device via USB and enable USB Debugging", text_color=self.T["text_dim"])
            self.bat_lbl.configure(text="")
            self.scan_btn.configure(state="disabled")
        self.after(0, update)

    def _refresh_device_card(self):
        if self.device_info:
            self._on_device_connected(self.device_info)

    def _show_usb_guide(self):
        T = self.T
        win = ctk.CTkToplevel(self)
        win.title("Enable USB Debugging")
        win.geometry("500x420")
        win.configure(fg_color=T["bg"])

        ctk.CTkLabel(win, text="Enable USB Debugging", font=("Segoe UI", 16, "bold"), text_color=T["accent"]).pack(pady=(20, 12))

        steps = [
            ("1", "Open Settings on your Galaxy device"),
            ("2", "Go to About Phone → Software Information"),
            ("3", "Tap Build Number 7 times to unlock Developer Options"),
            ("4", "Go back to Settings → Developer Options"),
            ("5", "Enable USB Debugging"),
            ("6", "Connect via USB — tap Allow on your phone"),
            ("7", "DebloatKit will detect your device automatically"),
        ]

        for num, step in steps:
            row = ctk.CTkFrame(win, fg_color=T["bg_card"], corner_radius=6)
            row.pack(fill="x", padx=24, pady=2)
            ctk.CTkLabel(row, text=num, font=("Segoe UI", 11, "bold"), text_color=T["accent"], width=24).pack(side="left", padx=10, pady=6)
            ctk.CTkLabel(row, text=step, font=("Segoe UI", 11), text_color=T["text"], anchor="w").pack(side="left", padx=4)

        ctk.CTkButton(win, text="Got it", fg_color=T["accent"], text_color=T["btn_primary_text"],
                      width=120, command=win.destroy).pack(pady=16)

    def _start_scan(self):
        if self._scanning:
            return
        if not self.device_info:
            messagebox.showerror("No Device", "Connect your device first.")
            return

        self._scanning = True
        self.scan_btn.configure(state="disabled", text="Scanning...")

        prog = ctk.CTkProgressBar(self.device_strip, fg_color=self.T["progress_bg"], progress_color=self.T["accent"], height=4)
        prog.set(0)
        prog.pack(side="right", padx=12, fill="x", expand=True)

        def progress_cb(val, msg):
            self.after(0, lambda: prog.set(val))

        def run():
            data = self.scanner.scan(self.device_info, progress_callback=progress_cb)
            self.app_data = data

            def done():
                prog.destroy()
                self.scan_btn.configure(state="normal", text="Re-Scan")
                self._refresh_all_tabs()
                self._scanning = False
            self.after(0, done)

        threading.Thread(target=run, daemon=True).start()

    # ─── Log ─────────────────────────────────────────────────────────────────

    def _log(self, message: str, level: str = "info"):
        T = self.T
        color_map = {
            "info": T["log_info"],
            "success": T["log_success"],
            "warning": T["log_warning"],
            "error": T["log_error"],
        }
        color = color_map.get(level, T["log_info"])
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {message}\n"

        def update():
            # Strip log
            self.log_strip_text.configure(state="normal")
            self.log_strip_text.insert("end", line)
            self.log_strip_text.see("end")
            self.log_strip_text.configure(state="disabled")

            # Full log tab
            if hasattr(self, "full_log"):
                self.full_log.configure(state="normal")
                self.full_log.insert("end", line)
                self.full_log.see("end")
                self.full_log.configure(state="disabled")

        self.after(0, update)

    def _clear_log_strip(self):
        self.log_strip_text.configure(state="normal")
        self.log_strip_text.delete("1.0", "end")
        self.log_strip_text.configure(state="disabled")

    def _clear_full_log(self):
        self.full_log.configure(state="normal")
        self.full_log.delete("1.0", "end")
        self.full_log.configure(state="disabled")
        self._clear_log_strip()

    def _export_log(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"DebloatKit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if path:
            content = self.full_log.get("1.0", "end")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self._log(f"Log exported: {path}", "success")

    # ─── Settings Helpers ─────────────────────────────────────────────────────

    def _browse_adb(self):
        path = filedialog.askopenfilename(filetypes=[("ADB executable", "adb.exe"), ("All files", "*.*")])
        if path:
            self.adb_path_var.set(path)
            self.adb.adb_path = path

    def _test_adb(self):
        self.adb.adb_path = self.adb_path_var.get()
        if self.adb.is_adb_available():
            self._log("ADB is working correctly.", "success")
            messagebox.showinfo("ADB Test", "ADB is working correctly!")
        else:
            self._log("ADB not found or not working.", "error")
            messagebox.showerror("ADB Test", "ADB not found. Check the path in Settings.")

    def _browse_backup(self):
        path = filedialog.askdirectory()
        if path:
            self.backup_path_var.set(path)
            self.debloater.backup_dir = path

    def _panic_restore(self):
        backup_path = self.debloater.get_latest_backup_path()
        if not backup_path:
            messagebox.showinfo("Panic Restore", "No backups found.")
            return
        if not self.device_info:
            messagebox.showerror("No Device", "Device must be connected for Panic Restore.")
            return
        if messagebox.askyesno(
            "Panic Restore",
            f"Re-enable ALL packages from:\n{os.path.basename(backup_path)}\n\nProceed?"
        ):
            threading.Thread(target=self.debloater.panic_restore, args=(backup_path,), daemon=True).start()

    def _on_dry_run_toggle(self):
        self.debloater.set_dry_run(self.dry_run_var.get())

    def on_close(self):
        self.adb.stop_polling()
        self.destroy()


def main():
    app = DebloatKit()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()


if __name__ == "__main__":
    main()
