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
WINDOW_W    = 1300
WINDOW_H    = 840


class DebloatKit(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.current_theme_name = "Green"
        self.T = get_theme(self.current_theme_name)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.title(f"{APP_NAME} {APP_VERSION} — {APP_BRAND}")
        self.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.minsize(1100, 720)
        self.configure(fg_color=self.T["bg"])

        # Core modules
        self.adb      = ADBManager(log_callback=self._log)
        self.scanner  = AppScanner(self.adb, log_callback=self._log)
        self.debloater = Debloater(self.adb, log_callback=self._log)

        # State
        self.device_info: DeviceInfo | None = None
        self.app_data: dict[str, list[AppEntry]] = {
            "system": [], "core": [], "user": [], "thirdparty": [], "keep": []
        }
        self.compact_var     = tk.BooleanVar(value=True)
        self._spacious_mode  = False   # False = compact (default ON)
        self._scanning       = False
        self._action_running = False
        self._active_tab     = "system"

        self._build_ui()
        self._start_device_polling()

    # ─── Build UI ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        T = self.T

        # ── Topbar ───────────────────────────────────────────────────────────
        self.topbar = ctk.CTkFrame(self, fg_color=T["topbar_bg"], height=56, corner_radius=0)
        self.topbar.pack(fill="x", side="top")
        self.topbar.pack_propagate(False)
        self._build_topbar()

        # ── Bottom bar (START DEBLOAT + Log btn) ─────────────────────────────
        self.bottombar = ctk.CTkFrame(self, fg_color=T["bg"], height=62, corner_radius=0)
        self.bottombar.pack(fill="x", side="bottom")
        self.bottombar.pack_propagate(False)
        self._build_bottombar()

        # ── Status strip (Ready / scanning) ──────────────────────────────────
        self.statusbar = ctk.CTkFrame(self, fg_color=T["bg"], height=22, corner_radius=0)
        self.statusbar.pack(fill="x", side="bottom")
        self.statusbar.pack_propagate(False)
        self.status_text = ctk.CTkLabel(
            self.statusbar, text="Connect your device via USB and enable USB Debugging.",
            font=("Segoe UI", 10), text_color=T["text_muted"], anchor="w"
        )
        self.status_text.pack(side="left", padx=14)
        self.progress_bar = ctk.CTkProgressBar(
            self.statusbar, fg_color=T["progress_bg"], progress_color=T["accent"],
            height=4, width=200
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(side="left", padx=8, pady=8)

        # ── Body: sidebar + content ───────────────────────────────────────────
        self.body = ctk.CTkFrame(self, fg_color=T["bg"], corner_radius=0)
        self.body.pack(fill="both", expand=True)

        # Sidebar (spacious mode — hidden in compact)
        self.sidebar = ctk.CTkFrame(self.body, fg_color=T["bg"], width=160, corner_radius=0)
        # Don't pack sidebar yet — compact mode is default

        # Content area
        self.content = ctk.CTkFrame(self.body, fg_color=T["bg"], corner_radius=0)
        self.content.pack(fill="both", expand=True)

        # ── Device info card ─────────────────────────────────────────────────
        self.device_card = ctk.CTkFrame(self.content, fg_color=T["bg_card"], height=44, corner_radius=6)
        self.device_card.pack(fill="x", padx=12, pady=(6, 0))
        self.device_card.pack_propagate(False)
        self._build_device_card()

        # ── Tab bar (compact: horizontal tabs) ───────────────────────────────
        self.tabbar = ctk.CTkFrame(self.content, fg_color=T["bg"], height=38, corner_radius=0)
        self.tabbar.pack(fill="x", padx=12, pady=(4, 0))
        self.tabbar.pack_propagate(False)
        self._build_tabbar()

        # ── Select All / Deselect All + total count row ───────────────────────
        self.sel_bar = ctk.CTkFrame(self.content, fg_color=T["bg"], height=38, corner_radius=0)
        self.sel_bar.pack(fill="x", padx=12, pady=(2, 0))
        self.sel_bar.pack_propagate(False)
        self._build_sel_bar()

        # ── Total selected strip ──────────────────────────────────────────────
        self.info_strip = ctk.CTkFrame(self.content, fg_color=T["bg_card"], height=30, corner_radius=4)
        self.info_strip.pack(fill="x", padx=12, pady=(2, 0))
        self.info_strip.pack_propagate(False)
        self.info_lbl = ctk.CTkLabel(
            self.info_strip, text="💾  No device scanned yet",
            font=("Segoe UI", 10), text_color=T["accent"], anchor="w"
        )
        self.info_lbl.pack(side="left", padx=10)

        # ── Package list scroll area ──────────────────────────────────────────
        self.pkg_scroll = ctk.CTkScrollableFrame(
            self.content, fg_color=T["bg"],
            scrollbar_button_color=T["scrollbar"],
            scrollbar_button_hover_color=T["accent"]
        )
        self.pkg_scroll.pack(fill="both", expand=True, padx=12, pady=(4, 0))

        # ── Log panel (right side — hidden by default, shown via Log btn) ─────
        self.log_panel = ctk.CTkFrame(self.body, fg_color=T["log_bg"], width=280, corner_radius=0)
        self.log_visible = False
        self._log_header_built = False

        # Build log content lazily
        self._build_log_panel()

        # Pages dictionary for tab switching
        self._tab_btns = {}

    def _build_topbar(self):
        T = self.T
        tb = self.topbar

        # Left: logo + name
        left = ctk.CTkFrame(tb, fg_color="transparent")
        left.pack(side="left", padx=14, pady=8)

        ctk.CTkLabel(
            left, text="⬡", font=("Segoe UI", 26), text_color=T["accent"]
        ).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            left, text=APP_NAME, font=("Segoe UI", 18, "bold"), text_color=T["accent"]
        ).pack(side="left")
        ctk.CTkLabel(
            left, text=f" {APP_VERSION}", font=("Segoe UI", 11), text_color=T["text_muted"]
        ).pack(side="left", pady=(5, 0))

        # Right: compact toggle + connection dot
        right = ctk.CTkFrame(tb, fg_color="transparent")
        right.pack(side="right", padx=14, pady=8)

        # Connection status
        self.status_dot   = ctk.CTkLabel(right, text="●", font=("Segoe UI", 14), text_color="#333333")
        self.status_label = ctk.CTkLabel(right, text="No Device", font=("Segoe UI", 11), text_color=T["text_muted"])
        self.status_label.pack(side="right", padx=(4, 0))
        self.status_dot.pack(side="right", padx=(12, 0))

        # Compact toggle — matches PurgeKit exactly
        self.compact_switch = ctk.CTkSwitch(
            right, variable=self.compact_var, text="",
            progress_color=T["accent"], button_color=T["accent"],
            button_hover_color=T["accent_dim"],
            width=46, height=22,
            command=self._on_compact_toggle
        )
        self.compact_switch.pack(side="right", padx=(4, 0))
        self.compact_switch.select()   # ON by default

        ctk.CTkLabel(
            right, text="Compact", font=("Segoe UI", 11), text_color=T["text_muted"]
        ).pack(side="right", padx=(16, 2))

    def _build_device_card(self):
        T = self.T
        dc = self.device_card

        self.dev_model_lbl = ctk.CTkLabel(
            dc, text="No device connected",
            font=("Segoe UI", 11, "bold"), text_color=T["text_muted"], anchor="w"
        )
        self.dev_model_lbl.pack(side="left", padx=12)

        self.dev_info_lbl = ctk.CTkLabel(
            dc, text="Plug in your Galaxy device and enable USB Debugging",
            font=("Segoe UI", 10), text_color=T["text_dim"], anchor="w"
        )
        self.dev_info_lbl.pack(side="left", padx=4)

        self.bat_lbl = ctk.CTkLabel(dc, text="", font=("Segoe UI", 10), text_color=T["text_muted"])
        self.bat_lbl.pack(side="right", padx=8)

        self.scan_btn = ctk.CTkButton(
            dc, text="⟳  Scan", font=("Segoe UI", 11, "bold"),
            fg_color=T["accent"], text_color=T["btn_primary_text"],
            hover_color=T["accent_dim"], width=100, height=28,
            command=self._start_scan, state="disabled"
        )
        self.scan_btn.pack(side="right", padx=8, pady=6)

    def _build_tabbar(self):
        T = self.T
        tb = self.tabbar

        tabs = [
            ("system",     "System Apps"),
            ("core",       "Core Apps"),
            ("user",       "User Apps"),
            ("thirdparty", "3rd Party"),
            ("logs",       "Log"),
            ("settings",   "Settings"),
            ("about",      "About"),
        ]

        self._tab_btns = {}
        for key, label in tabs:
            btn = ctk.CTkButton(
                tb, text=label,
                font=("Segoe UI", 11),
                fg_color=T["accent"] if key == "system" else "transparent",
                text_color=T["btn_primary_text"] if key == "system" else T["text_muted"],
                hover_color=T["bg_hover"],
                corner_radius=6,
                height=30, width=0,
                command=lambda k=key: self._switch_tab(k)
            )
            btn.pack(side="left", padx=(0, 2))
            self._tab_btns[key] = btn

    def _build_sel_bar(self):
        T = self.T
        sb = self.sel_bar

        self.sel_all_btn = ctk.CTkButton(
            sb, text="✓  Select All",
            font=("Segoe UI", 11, "bold"),
            fg_color=T["accent"], text_color=T["btn_primary_text"],
            hover_color=T["accent_dim"],
            width=120, height=28,
            command=lambda: self._select_all(self._active_tab, True)
        )
        self.sel_all_btn.pack(side="left", padx=(0, 6))

        self.desel_all_btn = ctk.CTkButton(
            sb, text="✕  Deselect All",
            font=("Segoe UI", 11),
            fg_color=T["bg_card"], text_color=T["text"],
            hover_color=T["bg_hover"],
            width=120, height=28,
            command=lambda: self._select_all(self._active_tab, False)
        )
        self.desel_all_btn.pack(side="left", padx=(0, 6))

        # Subcategory filter
        self.subcat_var = tk.StringVar(value="All")
        self.subcat_menu = ctk.CTkOptionMenu(
            sb, variable=self.subcat_var,
            values=["All"], width=160, height=28,
            fg_color=T["bg_card"], button_color=T["accent"],
            dropdown_fg_color=T["bg_card"], text_color=T["text"],
            command=lambda v: self._filter_active_tab()
        )
        self.subcat_menu.pack(side="left", padx=(0, 6))

        # Search
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._filter_active_tab())
        ctk.CTkEntry(
            sb, placeholder_text="Search...",
            textvariable=self.search_var,
            width=200, height=28,
            fg_color=T["bg_card"], border_color=T["border"],
            text_color=T["text"]
        ).pack(side="left", padx=(0, 6))

        self.count_lbl = ctk.CTkLabel(
            sb, text="", font=("Segoe UI", 10), text_color=T["text_muted"]
        )
        self.count_lbl.pack(side="left", padx=6)

    def _build_bottombar(self):
        T = self.T
        bb = self.bottombar

        # START DEBLOAT — big green button like PurgeKit START PURGE
        self.start_btn = ctk.CTkButton(
            bb, text="⚡  START DEBLOAT",
            font=("Segoe UI", 14, "bold"),
            fg_color=T["accent"], text_color=T["btn_primary_text"],
            hover_color=T["accent_dim"],
            corner_radius=6, height=44,
            command=self._on_start_debloat
        )
        self.start_btn.pack(side="left", padx=(12, 6), pady=9, fill="x", expand=True)

        # Log toggle button (right side like PurgeKit)
        self.log_toggle_btn = ctk.CTkButton(
            bb, text="📋  Log",
            font=("Segoe UI", 11),
            fg_color=T["bg_card"], text_color=T["text"],
            hover_color=T["bg_hover"],
            width=80, height=44,
            command=self._toggle_log_panel
        )
        self.log_toggle_btn.pack(side="right", padx=(6, 12), pady=9)

        # Re-enable selected (right of start)
        self.reenable_btn = ctk.CTkButton(
            bb, text="↩  Re-enable",
            font=("Segoe UI", 11),
            fg_color=T["bg_card"], text_color=T["warning"],
            hover_color=T["bg_hover"],
            border_width=1, border_color=T["warning"],
            width=120, height=44,
            command=self._on_start_reenable
        )
        self.reenable_btn.pack(side="right", padx=(0, 6), pady=9)

    def _build_log_panel(self):
        T = self.T
        lp = self.log_panel

        hdr = ctk.CTkFrame(lp, fg_color=T["bg_card"], height=32, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="LOG", font=("Segoe UI", 10, "bold"), text_color=T["accent"]).pack(side="left", padx=10, pady=6)
        ctk.CTkButton(
            hdr, text="Export", font=("Segoe UI", 9),
            fg_color="transparent", text_color=T["text_muted"],
            hover_color=T["bg_hover"], width=50, height=22,
            command=self._export_log
        ).pack(side="right", padx=4)
        ctk.CTkButton(
            hdr, text="Clear", font=("Segoe UI", 9),
            fg_color="transparent", text_color=T["text_muted"],
            hover_color=T["bg_hover"], width=44, height=22,
            command=self._clear_log
        ).pack(side="right")

        self.log_text = ctk.CTkTextbox(
            lp, fg_color=T["log_bg"], text_color=T["text"],
            font=("Consolas", 10), corner_radius=0,
            scrollbar_button_color=T["scrollbar"]
        )
        self.log_text.pack(fill="both", expand=True, padx=0, pady=0)
        self.log_text.configure(state="disabled")

    # ─── Tab switching ────────────────────────────────────────────────────────

    def _switch_tab(self, key: str):
        T = self.T
        self._active_tab = key

        # Update tab button styles
        for k, btn in self._tab_btns.items():
            if k == key:
                btn.configure(fg_color=T["accent"], text_color=T["btn_primary_text"])
            else:
                btn.configure(fg_color="transparent", text_color=T["text_muted"])

        # Show/hide sel_bar and info_strip based on tab type
        app_tabs = ("system", "core", "user", "thirdparty")
        if key in app_tabs:
            self.sel_bar.pack(fill="x", padx=12, pady=(2, 0))
            self.info_strip.pack(fill="x", padx=12, pady=(2, 0))
            self.pkg_scroll.pack(fill="both", expand=True, padx=12, pady=(4, 0))
            self._render_app_tab(key)
        else:
            self.sel_bar.pack_forget()
            self.info_strip.pack_forget()
            self.pkg_scroll.pack_forget()
            # Show dedicated pages
            if key == "logs":
                self._show_logs_page()
            elif key == "settings":
                self._show_settings_page()
            elif key == "about":
                self._show_about_page()

    def _show_logs_page(self):
        """Show full log view in main content area."""
        self._clear_page()
        T = self.T
        f = ctk.CTkFrame(self.content, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=12, pady=8)

        toolbar = ctk.CTkFrame(f, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 6))
        ctk.CTkButton(toolbar, text="Export Log", width=100, height=28,
                      fg_color=T["bg_card"], text_color=T["text"],
                      hover_color=T["bg_hover"], command=self._export_log).pack(side="left", padx=(0, 6))
        ctk.CTkButton(toolbar, text="Clear", width=60, height=28,
                      fg_color=T["bg_card"], text_color=T["text_muted"],
                      hover_color=T["bg_hover"], command=self._clear_log).pack(side="left")

        log_view = ctk.CTkTextbox(f, fg_color=T["log_bg"], text_color=T["text"],
                                  font=("Consolas", 11), corner_radius=6,
                                  scrollbar_button_color=T["scrollbar"])
        log_view.pack(fill="both", expand=True)
        log_view.configure(state="disabled")
        # Mirror log content
        try:
            content = self.log_text.get("1.0", "end")
            log_view.configure(state="normal")
            log_view.insert("1.0", content)
            log_view.see("end")
            log_view.configure(state="disabled")
        except Exception:
            pass
        self._page_frame = f

    def _show_settings_page(self):
        self._clear_page()
        T = self.T
        f = ctk.CTkFrame(self.content, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=12, pady=8)

        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        def section(title):
            ctk.CTkLabel(scroll, text=title, font=("Segoe UI", 12, "bold"),
                         text_color=T["accent"]).pack(anchor="w", pady=(12, 2))
            ctk.CTkFrame(scroll, fg_color=T["border"], height=1).pack(fill="x", pady=(0, 8))

        def row(label, widget_fn):
            fr = ctk.CTkFrame(scroll, fg_color="transparent")
            fr.pack(fill="x", pady=4)
            ctk.CTkLabel(fr, text=label, font=("Segoe UI", 11), text_color=T["text"],
                         width=180, anchor="w").pack(side="left")
            widget_fn(fr)

        section("ADB Configuration")
        self.adb_path_var = tk.StringVar(value=self.adb.adb_path)
        def adb_row(fr):
            ctk.CTkEntry(fr, textvariable=self.adb_path_var, width=280,
                         fg_color=T["bg_card"], border_color=T["border"],
                         text_color=T["text"]).pack(side="left", padx=(0,6))
            ctk.CTkButton(fr, text="Browse", width=70, height=28, fg_color=T["bg_card"],
                          text_color=T["text"], command=self._browse_adb).pack(side="left", padx=(0,6))
            ctk.CTkButton(fr, text="Test ADB", width=80, height=28, fg_color=T["accent"],
                          text_color=T["btn_primary_text"], command=self._test_adb).pack(side="left")
        row("ADB executable", adb_row)

        section("Backup")
        self.backup_path_var = tk.StringVar(value=self.debloater.backup_dir)
        def bk_row(fr):
            ctk.CTkEntry(fr, textvariable=self.backup_path_var, width=280,
                         fg_color=T["bg_card"], border_color=T["border"],
                         text_color=T["text"]).pack(side="left", padx=(0,6))
            ctk.CTkButton(fr, text="Browse", width=70, height=28, fg_color=T["bg_card"],
                          text_color=T["text"], command=self._browse_backup).pack(side="left", padx=(0,6))
            ctk.CTkButton(fr, text="Open Folder", width=90, height=28, fg_color=T["bg_card"],
                          text_color=T["text"],
                          command=lambda: os.startfile(self.debloater.backup_dir)
                          if os.path.exists(self.debloater.backup_dir) else None).pack(side="left")
        row("Backup folder", bk_row)

        section("Appearance")
        def theme_row(fr):
            for name in THEMES:
                t = get_theme(name)
                ctk.CTkButton(fr, text=name, width=80, height=28,
                              fg_color=t["accent"], text_color=t["btn_primary_text"],
                              command=lambda n=name: self._switch_theme(n)).pack(side="left", padx=(0,6))
        row("Theme", theme_row)

        section("Emergency Recovery")
        ctk.CTkButton(
            scroll, text="⚡  Panic Restore (re-enable all from latest backup)",
            font=("Segoe UI", 11, "bold"),
            fg_color=T["core_red"], text_color="#ffffff",
            hover_color="#cc0000", width=320, height=36,
            command=self._panic_restore
        ).pack(anchor="w", pady=8)
        ctk.CTkLabel(scroll,
                     text="Re-enables ALL packages from the most recent automatic backup.",
                     font=("Segoe UI", 10), text_color=T["text_muted"]).pack(anchor="w")

        self._page_frame = f

    def _show_about_page(self):
        self._clear_page()
        T = self.T
        f = ctk.CTkFrame(self.content, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=12, pady=8)

        scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Info card — exact PurgeKit layout
        card = ctk.CTkFrame(scroll, fg_color=T["bg_card"], corner_radius=10,
                            border_width=1, border_color=T["border"])
        card.pack(fill="x", pady=(0, 12))

        info_rows = [
            ("Built by",  APP_AUTHOR),
            ("Location",  "Chennai, India"),
            ("Brand",     APP_BRAND),
            ("License",   APP_LICENSE),
            ("Platform",  "Windows 10 / 11"),
            ("Version",   APP_VERSION),
        ]
        for label, value in info_rows:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=6)
            ctk.CTkLabel(row, text=label, font=("Segoe UI", 11),
                         text_color=T["text_muted"], width=100, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, font=("Segoe UI", 11, "bold"),
                         text_color=T["text"], anchor="w").pack(side="left")

        # GitHub
        ctk.CTkLabel(scroll, text="GitHub Repository",
                     font=("Segoe UI", 10), text_color=T["text_muted"]).pack(pady=(8, 2))
        ctk.CTkButton(
            scroll, text=APP_GITHUB, font=("Segoe UI", 11),
            fg_color=T["accent"], text_color=T["btn_primary_text"],
            hover_color=T["accent_dim"], height=34,
            command=lambda: webbrowser.open(APP_GITHUB)
        ).pack(fill="x", pady=(0, 8))

        # Version check placeholder
        ver_frame = ctk.CTkFrame(scroll, fg_color=T["bg_card"], corner_radius=6,
                                 border_width=1, border_color=T["border"])
        ver_frame.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(ver_frame, text=f"☑  You are on the latest version ({APP_VERSION})",
                     font=("Segoe UI", 11), text_color=T["text_muted"]).pack(padx=14, pady=10)

        # Donate card — matches PurgeKit About exactly
        don_card = ctk.CTkFrame(scroll, fg_color=T["bg_card"], corner_radius=10,
                                border_width=1, border_color=T["border"])
        don_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(don_card, text="⬡  Support DebloatKit",
                     font=("Segoe UI", 13, "bold"), text_color=T["text"]).pack(pady=(14, 2))
        ctk.CTkLabel(don_card,
                     text="DebloatKit is free forever. If it saved you time, consider supporting!",
                     font=("Segoe UI", 10), text_color=T["text_muted"]).pack(pady=(0, 8))

        ctk.CTkLabel(don_card, text="🌐  International — Pay in $",
                     font=("Segoe UI", 10, "bold"), text_color=T["accent"]).pack(pady=(0, 4))

        ctk.CTkButton(
            don_card, text="💙  Donate via PayPal ($)",
            font=("Segoe UI", 11, "bold"),
            fg_color="#003087", text_color="#FFFFFF",
            hover_color="#001f5b", height=36,
            command=lambda: webbrowser.open("https://paypal.me/yash92duster")
        ).pack(fill="x", padx=20, pady=(0, 6))

        ctk.CTkButton(
            don_card, text="🟦  Donate via Razorpay (₹)",
            font=("Segoe UI", 11, "bold"),
            fg_color=T["accent"], text_color=T["btn_primary_text"],
            hover_color=T["accent_dim"], height=36,
            command=lambda: webbrowser.open("https://rzp.io/rzp/nsogoeD")
        ).pack(fill="x", padx=20, pady=(0, 14))

        # Disclaimer
        ctk.CTkLabel(
            scroll,
            text="DebloatKit is 100% open source under the MIT License.\nFree to use, modify, and distribute.\n\n"
                 "Not affiliated with Samsung Electronics Co., Ltd.\nSamsung and Galaxy are trademarks of Samsung Electronics.",
            font=("Segoe UI", 9), text_color=T["text_dim"], justify="center"
        ).pack(pady=8)

        self._page_frame = f

    def _clear_page(self):
        """Remove any floating page frame."""
        if hasattr(self, "_page_frame") and self._page_frame.winfo_exists():
            self._page_frame.destroy()

    # ─── Package row (PurgeKit style) ─────────────────────────────────────────

    def _build_package_row(self, parent, entry: AppEntry) -> ctk.CTkFrame:
        T    = self.T
        comp = not self._spacious_mode   # compact = True when spacious_mode=False

        is_keep = entry.risk == "KEEP"
        is_core = entry.risk == "CORE"
        row_h   = 36 if comp else 64

        row = ctk.CTkFrame(
            parent,
            fg_color=T["bg_card"] if entry.state == "enabled" else T["disabled_bg"],
            corner_radius=4, height=row_h
        )
        row.pack(fill="x", pady=1, padx=0)
        row.pack_propagate(False)

        # Checkbox
        cb_wrap = ctk.CTkFrame(row, fg_color="transparent", width=32)
        cb_wrap.pack(side="left", padx=(8, 0))
        cb_wrap.pack_propagate(False)
        var = tk.BooleanVar(value=entry.checked)
        ctk.CTkCheckBox(
            cb_wrap, variable=var, text="",
            checkbox_width=16, checkbox_height=16,
            fg_color=T["core_red"] if is_core else T["accent"],
            hover_color=T["accent_dim"],
            state="disabled" if is_keep else "normal",
            command=lambda e=entry, v=var: self._on_check(e, v, is_core)
        ).pack(expand=True)
        entry._var = var
        entry._row_frame = row

        # Right-side widgets first (state + re-enable)
        state_color = get_state_color(entry.state)
        state_lbl = ctk.CTkLabel(
            row, text=entry.state.title(),
            font=("Segoe UI", 9, "bold"),
            text_color=state_color, width=72, anchor="e"
        )
        state_lbl.pack(side="right", padx=(2, 10))
        entry._state_lbl = state_lbl

        if entry.state in ("disabled", "uninstalled"):
            re_btn = ctk.CTkButton(
                row, text="Re-enable", font=("Segoe UI", 9),
                fg_color=T["accent"], text_color=T["btn_primary_text"],
                hover_color=T["accent_dim"], width=80, height=22,
                command=lambda e=entry: self._reenable_single(e)
            )
            re_btn.pack(side="right", padx=4)
            entry._re_btn = re_btn

        # Risk badge
        risk_color = get_risk_color(entry.risk, self.current_theme_name)
        risk_wrap = ctk.CTkFrame(row, fg_color="transparent", width=110)
        risk_wrap.pack(side="left", padx=(4, 0))
        risk_wrap.pack_propagate(False)
        ctk.CTkLabel(
            risk_wrap,
            text=get_risk_label(entry.risk),
            font=("Segoe UI", 9, "bold"),
            text_color=risk_color, anchor="w"
        ).pack(fill="x", expand=True, padx=2)

        # Info (fills remaining space)
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=(4, 2))

        name_text = entry.name if entry.in_db else f"{entry.name} *"

        if comp:
            # PurgeKit compact: name bold LEFT, path/pkg dim RIGHT
            ctk.CTkLabel(
                info, text=name_text,
                font=("Segoe UI", 11, "bold"),
                text_color=T["text_dim"] if is_keep else T["text"],
                anchor="w"
            ).pack(side="left", padx=(0, 8))

            ctk.CTkLabel(
                info, text=entry.pkg,
                font=("Consolas", 9),
                text_color=T["text_dim"], anchor="e"
            ).pack(side="right", padx=(0, 4))
        else:
            # Spacious: 3 lines
            ctk.CTkLabel(
                info, text=name_text,
                font=("Segoe UI", 12, "bold"),
                text_color=T["text_dim"] if is_keep else T["text"],
                anchor="w"
            ).pack(anchor="w", padx=2, pady=(6, 0))
            ctk.CTkLabel(
                info, text=entry.pkg,
                font=("Consolas", 9),
                text_color=T["text_muted"], anchor="w"
            ).pack(anchor="w", padx=2)
            if entry.description:
                ctk.CTkLabel(
                    info, text=entry.description,
                    font=("Segoe UI", 9),
                    text_color=T["text_dim"], anchor="w", wraplength=520
                ).pack(anchor="w", padx=2, pady=(0, 4))

        return row

    # ─── Section header (PurgeKit style — green bar with X / ✓) ──────────────

    def _build_section_header(self, parent, title: str, category: str) -> ctk.CTkFrame:
        T = self.T
        hdr = ctk.CTkFrame(parent, fg_color=T["accent"], corner_radius=4, height=34)
        hdr.pack(fill="x", pady=(8, 2))
        hdr.pack_propagate(False)

        # Icon + title
        ctk.CTkLabel(
            hdr, text=f"⚙  {title}",
            font=("Segoe UI", 11, "bold"),
            text_color=T["btn_primary_text"], anchor="w"
        ).pack(side="left", padx=12)

        # ✓ select section button
        ctk.CTkButton(
            hdr, text="✓", width=28, height=22,
            fg_color=T["accent_dim"], text_color=T["btn_primary_text"],
            hover_color=T["accent"], corner_radius=4,
            command=lambda c=category: self._select_all(c, True)
        ).pack(side="right", padx=(2, 6))

        # ✕ deselect section button
        ctk.CTkButton(
            hdr, text="✕", width=28, height=22,
            fg_color=T["accent_dim"], text_color=T["btn_primary_text"],
            hover_color=T["accent"], corner_radius=4,
            command=lambda c=category: self._select_all(c, False)
        ).pack(side="right", padx=2)

        return hdr

    # ─── Render tab ───────────────────────────────────────────────────────────

    def _render_app_tab(self, category: str, entries: list[AppEntry] = None):
        T = self.T

        # Clear scroll area
        for w in self.pkg_scroll.winfo_children():
            w.destroy()

        entries = entries or self.app_data.get(category, [])

        if not entries:
            ctk.CTkLabel(
                self.pkg_scroll,
                text="No packages found. Scan your device first." if not self.device_info
                     else "No packages in this category.",
                font=("Segoe UI", 12), text_color=T["text_muted"]
            ).pack(pady=40)
            self.count_lbl.configure(text="0 packages")
            return

        # Group by subcategory
        subcats: dict[str, list[AppEntry]] = {}
        for e in entries:
            subcats.setdefault(e.subcategory or "Other", []).append(e)

        total = 0
        for subcat, items in subcats.items():
            self._build_section_header(self.pkg_scroll, subcat, category)
            for entry in items:
                self._build_package_row(self.pkg_scroll, entry)
                total += 1

        self.count_lbl.configure(text=f"{total} packages")

        # Update subcategory filter
        subcats_list = sorted(set(e.subcategory for e in self.app_data.get(category, []) if e.subcategory))
        self.subcat_menu.configure(values=["All"] + subcats_list)

        # Update info strip
        checked = sum(1 for e in entries if getattr(e, "checked", False))
        self.info_lbl.configure(
            text=f"💾  {total} packages loaded  ·  {checked} selected"
            if self.device_info else f"💾  No device scanned yet"
        )

    def _refresh_all_tabs(self):
        """Rebuild current tab with updated compact state."""
        if self._active_tab in ("system", "core", "user", "thirdparty"):
            self._render_app_tab(self._active_tab)

    # ─── Compact toggle ───────────────────────────────────────────────────────

    def _on_compact_toggle(self):
        self._spacious_mode = not self.compact_var.get()
        self._refresh_all_tabs()

    def _select_all(self, category: str, state: bool):
        for e in self.app_data.get(category, []):
            if e.risk not in ("KEEP",):
                if not state or e.risk != "CORE":
                    e.checked = state
                    if hasattr(e, "_var"):
                        e._var.set(state)

    def _filter_active_tab(self):
        cat     = self._active_tab
        entries = self.app_data.get(cat, [])
        subcat  = self.subcat_var.get()
        query   = self.search_var.get().lower()

        filtered = entries
        if subcat != "All":
            filtered = [e for e in filtered if e.subcategory == subcat]
        if query:
            filtered = [e for e in filtered if query in e.pkg.lower() or query in e.name.lower()]

        self._render_app_tab(cat, filtered)

    # ─── Core warning dialog ──────────────────────────────────────────────────

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

        ctk.CTkLabel(win, text="⛔  Core System App",
                     font=("Segoe UI", 16, "bold"), text_color=T["core_red"]).pack(pady=(20, 4))
        ctk.CTkLabel(win, text=f"{entry.name}",
                     font=("Segoe UI", 13, "bold"), text_color=T["text"]).pack()
        ctk.CTkLabel(win, text=entry.pkg,
                     font=("Consolas", 10), text_color=T["text_muted"]).pack(pady=(0, 8))

        msg_frame = ctk.CTkFrame(win, fg_color="#1a0505", corner_radius=8,
                                 border_width=1, border_color=T["core_red"])
        msg_frame.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(
            msg_frame,
            text=f"{entry.description}\n\n"
                 "⚠ Disabling may affect device stability.\n"
                 "✓ Fully reversible — re-enable anytime while connected.",
            font=("Segoe UI", 11), text_color=T["text"], wraplength=440, justify="left"
        ).pack(padx=12, pady=10)

        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.pack(pady=14)

        def cancel():
            var.set(False); entry.checked = False; win.destroy()
        def proceed():
            entry.checked = True; win.destroy()

        ctk.CTkButton(btn_row, text="Cancel", width=120,
                      fg_color=T["bg_hover"], text_color=T["text"],
                      command=cancel).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="I understand, proceed", width=180,
                      fg_color=T["core_red"], text_color="#ffffff",
                      command=proceed).pack(side="left", padx=8)

    # ─── Actions ──────────────────────────────────────────────────────────────

    def _on_start_debloat(self):
        self._run_action(self._active_tab, "uninstall")

    def _on_start_reenable(self):
        self._run_action(self._active_tab, "enable")

    def _run_action(self, category: str, action: str):
        if self._action_running:
            messagebox.showwarning("Busy", "An action is already running.")
            return
        if not self.device_info:
            messagebox.showerror("No Device", "Connect your device first.")
            return

        entries  = self.app_data.get(category, [])
        selected = [e for e in entries if e.checked and e.risk != "KEEP"]
        if not selected:
            messagebox.showinfo("Nothing Selected", "Select at least one package first.")
            return

        verb = "uninstall" if action == "uninstall" else "re-enable"
        if not messagebox.askyesno(
            f"Confirm {verb.title()}",
            f"{verb.title()} {len(selected)} package(s)?\n\nAll changes are reversible."
        ):
            return

        self._action_running = True
        self.start_btn.configure(state="disabled", text="Running...")
        self.progress_bar.set(0)
        self.progress_bar.pack(side="left", padx=8, pady=8)
        all_entries = [e for cat in self.app_data.values() for e in cat]

        def progress_cb(val, msg):
            self.after(0, lambda: self.progress_bar.set(val))
            self.after(0, lambda: self.status_text.configure(text=msg))

        def result_cb(entry: AppEntry, result):
            def update():
                if hasattr(entry, "_state_lbl") and entry._state_lbl.winfo_exists():
                    entry._state_lbl.configure(
                        text=entry.state.title(),
                        text_color=get_state_color(entry.state)
                    )
                if hasattr(entry, "_row_frame") and entry._row_frame.winfo_exists():
                    if entry.state in ("disabled", "uninstalled"):
                        entry._row_frame.configure(fg_color=self.T["disabled_bg"])
            self.after(0, update)

        def run():
            if action == "uninstall":
                results = self.debloater.uninstall_packages(selected, all_entries, progress_cb, result_cb)
            else:
                results = self.debloater.restore_packages(selected, progress_cb, result_cb)

            summary = self.debloater.get_summary(results)
            self.after(0, lambda: self._show_summary(summary, verb))
            self.after(0, lambda: self.start_btn.configure(state="normal", text="⚡  START DEBLOAT"))
            self.after(0, lambda: self.status_text.configure(
                text=f"Done — {summary['success']} succeeded · {summary['failed']} failed"
            ))
            self._action_running = False

            if any(e.pkg == "com.sec.android.diagmonagent" for e in selected):
                self.after(0, self._offer_soundalive_fix)

        threading.Thread(target=run, daemon=True).start()

    def _reenable_single(self, entry: AppEntry):
        if not self.device_info:
            messagebox.showerror("No Device", "Device not connected.")
            return
        def run():
            if entry.state == "disabled":
                ok, _ = self.adb.enable_package(entry.pkg)
            else:
                ok, _ = self.adb.reinstall_package(entry.pkg)
            if ok:
                entry.state = "enabled"
                def update():
                    if hasattr(entry, "_state_lbl") and entry._state_lbl.winfo_exists():
                        entry._state_lbl.configure(text="Enabled", text_color=get_state_color("enabled"))
                    if hasattr(entry, "_row_frame") and entry._row_frame.winfo_exists():
                        entry._row_frame.configure(fg_color=self.T["bg_card"])
                    if hasattr(entry, "_re_btn") and entry._re_btn.winfo_exists():
                        entry._re_btn.destroy()
                self.after(0, update)
        threading.Thread(target=run, daemon=True).start()

    def _show_summary(self, summary: dict, action: str):
        T = self.T
        win = ctk.CTkToplevel(self)
        win.title("Action Complete")
        win.geometry("360x200")
        win.configure(fg_color=T["bg"])
        win.grab_set()

        ctk.CTkLabel(win, text="✓  Complete",
                     font=("Segoe UI", 15, "bold"), text_color=T["success"]).pack(pady=(18, 8))
        info = ctk.CTkFrame(win, fg_color=T["bg_card"], corner_radius=8)
        info.pack(fill="x", padx=24, pady=4)

        def row(label, value, color=None):
            fr = ctk.CTkFrame(info, fg_color="transparent")
            fr.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(fr, text=label, font=("Segoe UI", 10), text_color=T["text_muted"]).pack(side="left")
            ctk.CTkLabel(fr, text=str(value), font=("Segoe UI", 10, "bold"),
                         text_color=color or T["text"]).pack(side="right")

        row("Action",    action.title())
        row("Succeeded", summary["success"], T["success"])
        if summary["failed"] > 0:
            row("Failed", summary["failed"], T["error"])
        row("Backup",    "Saved automatically", T["accent"])

        ctk.CTkButton(win, text="Close", fg_color=T["accent"],
                      text_color=T["btn_primary_text"], width=100,
                      command=win.destroy).pack(pady=14)

    def _offer_soundalive_fix(self):
        if messagebox.askyesno("SoundAlive Fix",
                               "Diagnostic Monitor was removed.\n\nRun SoundAlive flush to fix audio? (Recommended)"):
            self.debloater.soundalive_fix()

    # ─── Log panel ────────────────────────────────────────────────────────────

    def _toggle_log_panel(self):
        if self.log_visible:
            self.log_panel.pack_forget()
            self.log_visible = False
            self.log_toggle_btn.configure(fg_color=self.T["bg_card"])
        else:
            self.log_panel.pack(side="right", fill="y", in_=self.body)
            self.log_visible = True
            self.log_toggle_btn.configure(fg_color=self.T["accent"])

    def _log(self, message: str, level: str = "info"):
        T = self.T
        color_map = {
            "info":    T["log_info"],
            "success": T["log_success"],
            "warning": T["log_warning"],
            "error":   T["log_error"],
        }
        ts   = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {message}\n"

        def update():
            if hasattr(self, "log_text") and self.log_text.winfo_exists():
                self.log_text.configure(state="normal")
                self.log_text.insert("end", line)
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        self.after(0, update)

    def _clear_log(self):
        if hasattr(self, "log_text"):
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", "end")
            self.log_text.configure(state="disabled")

    def _export_log(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"DebloatKit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if path and hasattr(self, "log_text"):
            content = self.log_text.get("1.0", "end")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self._log(f"Log exported: {path}", "success")

    # ─── Device polling ───────────────────────────────────────────────────────

    def _start_device_polling(self):
        self.adb.start_polling(
            on_status_change=self._on_device_status,
            on_connected=self._on_device_connected,
            on_disconnected=self._on_device_disconnected
        )

    def _on_device_status(self, status: str):
        colors = {"no_device": "#333333", "unauthorized": "#ffab00", "ready": "#00e676"}
        labels = {"no_device": "No Device", "unauthorized": "Unauthorized", "ready": "Connected"}

        def update():
            self.status_dot.configure(text_color=colors.get(status, "#333333"))
            self.status_label.configure(text=labels.get(status, status))
            if status == "unauthorized":
                self._show_usb_guide()
        self.after(0, update)

    def _on_device_connected(self, info: DeviceInfo):
        self.device_info = info
        def update():
            self.dev_model_lbl.configure(
                text=f"{info.brand} {info.model}", text_color=self.T["text"]
            )
            self.dev_info_lbl.configure(
                text=f"Android {info.android_version}  ·  One UI {info.oneui_version or '?'}  ·  API {info.api_level}  ·  {info.get_era_label()}",
                text_color=self.T["text_muted"]
            )
            bat_color = self.T["error"] if info.battery_level < 20 else self.T["text_muted"]
            self.bat_lbl.configure(text=f"🔋 {info.battery_level}%", text_color=bat_color)
            self.scan_btn.configure(state="normal")
            self.status_text.configure(text=f"Device ready — {info.brand} {info.model}")
        self.after(0, update)

    def _on_device_disconnected(self):
        self.device_info = None
        def update():
            self.dev_model_lbl.configure(text="No device connected", text_color=self.T["text_muted"])
            self.dev_info_lbl.configure(
                text="Plug in your Galaxy device and enable USB Debugging",
                text_color=self.T["text_dim"]
            )
            self.bat_lbl.configure(text="")
            self.scan_btn.configure(state="disabled")
            self.status_text.configure(text="No device connected.")
        self.after(0, update)

    def _show_usb_guide(self):
        T = self.T
        win = ctk.CTkToplevel(self)
        win.title("Enable USB Debugging")
        win.geometry("500x400")
        win.configure(fg_color=T["bg"])

        ctk.CTkLabel(win, text="Enable USB Debugging",
                     font=("Segoe UI", 15, "bold"), text_color=T["accent"]).pack(pady=(18, 10))

        steps = [
            "Open Settings on your Galaxy device",
            "Go to About Phone → Software Information",
            "Tap Build Number 7 times to unlock Developer Options",
            "Go back to Settings → Developer Options",
            "Enable USB Debugging",
            "Connect via USB — tap Allow on your phone",
            "DebloatKit detects your device automatically",
        ]
        for i, step in enumerate(steps, 1):
            row = ctk.CTkFrame(win, fg_color=T["bg_card"], corner_radius=6)
            row.pack(fill="x", padx=22, pady=2)
            ctk.CTkLabel(row, text=str(i), font=("Segoe UI", 11, "bold"),
                         text_color=T["accent"], width=24).pack(side="left", padx=10, pady=6)
            ctk.CTkLabel(row, text=step, font=("Segoe UI", 11),
                         text_color=T["text"], anchor="w").pack(side="left", padx=4)

        ctk.CTkButton(win, text="Got it", fg_color=T["accent"],
                      text_color=T["btn_primary_text"], width=120,
                      command=win.destroy).pack(pady=14)

    def _start_scan(self):
        if self._scanning: return
        if not self.device_info:
            messagebox.showerror("No Device", "Connect your device first.")
            return

        self._scanning = True
        self.scan_btn.configure(state="disabled", text="Scanning...")
        self.status_text.configure(text="Scanning device packages...")
        self.progress_bar.set(0)

        def progress_cb(val, msg):
            self.after(0, lambda: self.progress_bar.set(val))
            self.after(0, lambda: self.status_text.configure(text=msg))

        def run():
            data = self.scanner.scan(self.device_info, progress_callback=progress_cb)
            self.app_data = data

            def done():
                self.scan_btn.configure(state="normal", text="⟳  Re-Scan")
                self._scanning = False
                self._switch_tab(self._active_tab)
                total = sum(len(v) for v in data.values())
                self.status_text.configure(text=f"Scan complete — {total} packages found")
            self.after(0, done)

        threading.Thread(target=run, daemon=True).start()

    # ─── Theme ────────────────────────────────────────────────────────────────

    def _switch_theme(self, name: str):
        self.current_theme_name = name
        self.T = get_theme(name)
        for w in self.winfo_children():
            w.destroy()
        self.configure(fg_color=self.T["bg"])
        self._build_ui()
        if self.device_info:
            self._on_device_connected(self.device_info)
        self._switch_tab(self._active_tab)

    # ─── Settings helpers ─────────────────────────────────────────────────────

    def _browse_adb(self):
        path = filedialog.askopenfilename(filetypes=[("ADB", "adb.exe"), ("All", "*.*")])
        if path:
            self.adb_path_var.set(path)
            self.adb.adb_path = path

    def _test_adb(self):
        self.adb.adb_path = self.adb_path_var.get()
        if self.adb.is_adb_available():
            messagebox.showinfo("ADB Test", "ADB is working correctly!")
        else:
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
        if messagebox.askyesno("Panic Restore",
                               f"Re-enable ALL from:\n{os.path.basename(backup_path)}\n\nProceed?"):
            threading.Thread(target=self.debloater.panic_restore, args=(backup_path,), daemon=True).start()

    def on_close(self):
        self.adb.stop_polling()
        self.destroy()


def main():
    app = DebloatKit()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()


if __name__ == "__main__":
    main()
