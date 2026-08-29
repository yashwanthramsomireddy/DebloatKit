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
from PIL import Image

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
WINDOW_H    = 800


def _load_logo(size: int):
    """Load the DebloatKit logo. Returns CTkImage or None."""
    base  = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(base, "assets", "debloatkit_logo.png"),
        os.path.join(base, "assets", f"logo_{size}.png"),
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                img = Image.open(p).convert("RGBA").resize((size, size), Image.LANCZOS)
                return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
            except Exception:
                pass
    return None


# ─── App icon ─────────────────────────────────────────────────────────────────
def _set_icon(win):
    base = os.path.dirname(os.path.abspath(__file__))
    ico  = os.path.join(base, "assets", "icon.ico")
    if os.path.exists(ico):
        try:
            win.iconbitmap(ico)
        except Exception:
            pass


class DebloatKit(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.current_theme_name = "Green"
        self.T = get_theme(self.current_theme_name)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.title(f"{APP_NAME} {APP_VERSION} — {APP_BRAND}")
        self.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.minsize(900, 660)
        self.after(0, lambda: self.state("zoomed"))   # start maximized
        self.configure(fg_color=self.T["bg"])
        _set_icon(self)

        # Core modules
        self.adb       = ADBManager(log_callback=self._log)
        self.scanner   = AppScanner(self.adb, log_callback=self._log)
        self.debloater = Debloater(self.adb, log_callback=self._log)

        # State
        self.device_info: DeviceInfo | None = None
        self.app_data: dict[str, list[AppEntry]] = {
            "system": [], "core": [], "user": [], "thirdparty": [], "keep": []
        }
        self._scanning       = False
        self._action_running = False
        self._active_tab     = "system"
        self._render_cache   = {}   # category -> (compact_state, entries_hash) - skip rebuild if same

        self._build_ui()
        self._start_device_polling()

    # ─── Theme ────────────────────────────────────────────────────────────────

    def _switch_theme(self, name: str):
        self.current_theme_name = name
        self.T = get_theme(name)
        for w in self.winfo_children():
            w.destroy()
        self.configure(fg_color=self.T["bg"])
        self._build_ui()
        self._start_device_polling()
        if self.device_info:
            self._on_device_connected(self.device_info)

    # ─── Main UI builder ──────────────────────────────────────────────────────

    def _build_ui(self):
        T = self.T

        # ── Topbar ───────────────────────────────────────────────────────────
        topbar = ctk.CTkFrame(self, fg_color=T["topbar_bg"], height=52, corner_radius=0)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        left = ctk.CTkFrame(topbar, fg_color="transparent")
        left.pack(side="left", padx=12, pady=6)
        logo_img = _load_logo(32)
        if logo_img:
            ctk.CTkLabel(left, image=logo_img, text="").pack(side="left", padx=(0, 7))
        else:
            ctk.CTkLabel(left, text="⬡", font=("Segoe UI", 22), text_color=T["accent"]).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(left, text=APP_NAME, font=("Segoe UI", 16, "bold"), text_color=T["accent"]).pack(side="left")
        ctk.CTkLabel(left, text=f" {APP_VERSION}", font=("Segoe UI", 10), text_color=T["text_muted"]).pack(side="left", pady=(4, 0))

        right = ctk.CTkFrame(topbar, fg_color="transparent")
        right.pack(side="right", padx=12, pady=6)

        self.status_label = ctk.CTkLabel(right, text="No Device", font=("Segoe UI", 11), text_color=T["text_muted"])
        self.status_label.pack(side="right", padx=(4, 0))
        self.status_dot = ctk.CTkLabel(right, text="●", font=("Segoe UI", 13), text_color="#333333")
        self.status_dot.pack(side="right", padx=(10, 0))


        # ── Device strip ─────────────────────────────────────────────────────
        dev_strip = ctk.CTkFrame(self, fg_color=T["bg_card"], height=40, corner_radius=0)
        dev_strip.pack(fill="x")
        dev_strip.pack_propagate(False)

        self.dev_model_lbl = ctk.CTkLabel(dev_strip, text="No device connected",
                                          font=("Segoe UI", 11, "bold"), text_color=T["text_muted"], anchor="w")
        self.dev_model_lbl.pack(side="left", padx=12)
        self.dev_info_lbl = ctk.CTkLabel(dev_strip, text="Connect via USB · Enable USB Debugging",
                                         font=("Segoe UI", 10), text_color=T["text_dim"], anchor="w")
        self.dev_info_lbl.pack(side="left", padx=4)
        self.bat_lbl = ctk.CTkLabel(dev_strip, text="", font=("Segoe UI", 10), text_color=T["text_muted"])
        self.bat_lbl.pack(side="right", padx=8)
        self.scan_btn = ctk.CTkButton(dev_strip, text="⟳  Scan", font=("Segoe UI", 11, "bold"),
                                      fg_color=T["accent"], text_color=T["btn_primary_text"],
                                      hover_color=T["accent_dim"], width=96, height=28,
                                      command=self._start_scan, state="disabled")
        self.scan_btn.pack(side="right", padx=8, pady=6)

        # ── Tab bar ───────────────────────────────────────────────────────────
        tab_bar = ctk.CTkFrame(self, fg_color=T["bg"], height=36, corner_radius=0)
        tab_bar.pack(fill="x", padx=10, pady=(4, 0))
        tab_bar.pack_propagate(False)

        self._tab_btns = {}
        tabs = [("system","System Apps"),("core","Core Apps"),("user","User Apps"),
                ("thirdparty","3rd Party"),("logs","Log"),("settings","Settings"),("about","About")]
        for key, label in tabs:
            btn = ctk.CTkButton(
                tab_bar, text=label, font=("Segoe UI", 11),
                fg_color=T["accent"] if key == "system" else "transparent",
                text_color=T["btn_primary_text"] if key == "system" else T["text_muted"],
                hover_color=T["bg_hover"], corner_radius=5,
                height=28, width=0,
                command=lambda k=key: self._switch_tab(k)
            )
            btn.pack(side="left", padx=(0, 2))
            self._tab_btns[key] = btn

        # ── Content area — ONE frame that hosts everything ────────────────────
        self.content = ctk.CTkFrame(self, fg_color=T["bg"], corner_radius=0)
        self.content.pack(fill="both", expand=True, padx=10, pady=(4, 0))

        # Package list toolbar (Select All, filter, search)
        self.pkg_toolbar = ctk.CTkFrame(self.content, fg_color=T["bg"], height=34, corner_radius=0)

        self.sel_all_btn = ctk.CTkButton(self.pkg_toolbar, text="✓  Select All",
                                         font=("Segoe UI", 11, "bold"),
                                         fg_color=T["accent"], text_color=T["btn_primary_text"],
                                         hover_color=T["accent_dim"], width=110, height=28,
                                         command=lambda: self._select_all(self._active_tab, True))
        self.sel_all_btn.pack(side="left", padx=(0, 5))
        self.desel_btn = ctk.CTkButton(self.pkg_toolbar, text="✕  Deselect All",
                                       font=("Segoe UI", 11),
                                       fg_color=T["bg_card"], text_color=T["text"],
                                       hover_color=T["bg_hover"], width=110, height=28,
                                       command=lambda: self._select_all(self._active_tab, False))
        self.desel_btn.pack(side="left", padx=(0, 5))

        self.subcat_var = tk.StringVar(value="All")
        self.subcat_menu = ctk.CTkOptionMenu(self.pkg_toolbar, variable=self.subcat_var,
                                             values=["All"], width=130, height=28,
                                             fg_color=T["bg_card"], button_color=T["accent"],
                                             dropdown_fg_color=T["bg_card"], text_color=T["text"],
                                             command=lambda v: self._filter_active_tab())
        self.subcat_menu.pack(side="left", padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._filter_active_tab())
        ctk.CTkEntry(self.pkg_toolbar, placeholder_text="Search...",
                     textvariable=self.search_var, width=180, height=28,
                     fg_color=T["bg_card"], border_color=T["border"],
                     text_color=T["text"]).pack(side="left", padx=(0, 5))
        self.count_lbl = ctk.CTkLabel(self.pkg_toolbar, text="", font=("Segoe UI", 10), text_color=T["text_muted"])
        self.count_lbl.pack(side="left", padx=5)

        # Info strip
        self.pkg_infostrip = ctk.CTkFrame(self.content, fg_color=T["bg_card"], height=28, corner_radius=4)
        self.info_lbl = ctk.CTkLabel(self.pkg_infostrip, text="💾  No device scanned yet",
                                     font=("Segoe UI", 10), text_color=T["accent"], anchor="w")
        self.info_lbl.pack(side="left", padx=10)

        # Scrollable package list
        self.pkg_scroll = ctk.CTkScrollableFrame(self.content, fg_color=T["bg"],
                                                 scrollbar_button_color=T["scrollbar"],
                                                 scrollbar_button_hover_color=T["accent"])

        # Page frame (for Settings, About, Logs — non-package tabs)
        self.page_frame = ctk.CTkFrame(self.content, fg_color=T["bg"], corner_radius=0)

        # ── Status bar ────────────────────────────────────────────────────────
        self.statusbar = ctk.CTkFrame(self, fg_color=T["bg"], height=20, corner_radius=0)
        self.statusbar.pack(fill="x", side="bottom")
        self.statusbar.pack_propagate(False)
        self.status_text = ctk.CTkLabel(self.statusbar, text="Connect your device via USB and enable USB Debugging.",
                                        font=("Segoe UI", 9), text_color=T["text_muted"], anchor="w")
        self.status_text.pack(side="left", padx=10)
        self.status_prog = ctk.CTkProgressBar(self.statusbar, fg_color=T["progress_bg"],
                                              progress_color=T["accent"], height=4, width=160)
        self.status_prog.set(0)
        self.status_prog.pack(side="left", padx=6, pady=7)

        # ── Bottom action bar ─────────────────────────────────────────────────
        bottombar = ctk.CTkFrame(self, fg_color=T["bg_card"], height=58, corner_radius=0,
                                 border_width=1, border_color=T["border"])
        bottombar.pack(fill="x", side="bottom")
        bottombar.pack_propagate(False)

        # Disable Selected — freeze apps (fastest, softest)
        self.disable_btn = ctk.CTkButton(
            bottombar, text="⏸  Disable Selected",
            font=("Segoe UI", 12, "bold"),
            fg_color=T["bg_hover"], text_color=T["warning"],
            hover_color=T["bg_hover"],
            border_width=1, border_color=T["warning"],
            corner_radius=6, height=40,
            command=lambda: self._run_action(self._active_tab, "disable")
        )
        self.disable_btn.pack(side="left", padx=(10, 4), pady=9, fill="x", expand=True)

        # Uninstall Selected — remove from user profile (deeper)
        self.uninstall_btn = ctk.CTkButton(
            bottombar, text="🗑  Uninstall Selected",
            font=("Segoe UI", 12, "bold"),
            fg_color=T["core_red"], text_color="#ffffff",
            hover_color="#cc0000",
            corner_radius=6, height=40,
            command=lambda: self._run_action(self._active_tab, "uninstall")
        )
        self.uninstall_btn.pack(side="left", padx=(0, 4), pady=9, fill="x", expand=True)

        # Re-enable Selected — restore disabled/uninstalled
        self.reenable_btn = ctk.CTkButton(
            bottombar, text="↩  Re-enable Selected",
            font=("Segoe UI", 12, "bold"),
            fg_color=T["accent"], text_color=T["btn_primary_text"],
            hover_color=T["accent_dim"],
            corner_radius=6, height=40,
            command=lambda: self._run_action(self._active_tab, "enable")
        )
        self.reenable_btn.pack(side="left", padx=(0, 4), pady=9, fill="x", expand=True)

        # Log toggle
        self.log_btn = ctk.CTkButton(
            bottombar, text="📋  Log",
            font=("Segoe UI", 11),
            fg_color=T["bg"], text_color=T["text"],
            hover_color=T["bg_hover"], width=72, height=40,
            command=self._toggle_log_panel
        )
        self.log_btn.pack(side="right", padx=(0, 10), pady=9)

        # ── Floating log panel (right side) ───────────────────────────────────
        self.log_panel = ctk.CTkFrame(self, fg_color=T["log_bg"], width=260, corner_radius=0)
        self.log_visible = False
        log_hdr = ctk.CTkFrame(self.log_panel, fg_color=T["bg_card"], height=30, corner_radius=0)
        log_hdr.pack(fill="x")
        log_hdr.pack_propagate(False)
        ctk.CTkLabel(log_hdr, text="LOG", font=("Segoe UI", 9, "bold"), text_color=T["accent"]).pack(side="left", padx=8, pady=5)
        ctk.CTkButton(log_hdr, text="Clear", font=("Segoe UI", 9), fg_color="transparent",
                      text_color=T["text_muted"], hover_color=T["bg_hover"], width=40, height=20,
                      command=self._clear_log).pack(side="right", padx=4)
        ctk.CTkButton(log_hdr, text="Export", font=("Segoe UI", 9), fg_color="transparent",
                      text_color=T["text_muted"], hover_color=T["bg_hover"], width=46, height=20,
                      command=self._export_log).pack(side="right")
        self.log_text = ctk.CTkTextbox(self.log_panel, fg_color=T["log_bg"], text_color=T["text"],
                                       font=("Consolas", 10), corner_radius=0,
                                       scrollbar_button_color=T["scrollbar"])
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

        # Show first tab
        self._show_pkg_ui()
        self._render_app_tab("system")

    # ─── Tab switching ────────────────────────────────────────────────────────

    def _show_pkg_ui(self):
        """Show package list UI (toolbar + infostrip + scroll), hide page frame."""
        self.page_frame.pack_forget()
        self.pkg_toolbar.pack(fill="x", pady=(0, 3))
        self.pkg_infostrip.pack(fill="x", pady=(0, 3))
        self.pkg_scroll.pack(fill="both", expand=True)

    def _show_page_ui(self):
        """Show page frame, hide package list UI."""
        self.pkg_scroll.pack_forget()
        self.pkg_toolbar.pack_forget()
        self.pkg_infostrip.pack_forget()
        # Clear old page content
        for w in self.page_frame.winfo_children():
            w.destroy()
        self.page_frame.pack(fill="both", expand=True)

    def _switch_tab(self, key: str):
        T = self.T
        self._active_tab = key

        # Update tab button styles — just configure, don't rebuild
        for k, btn in self._tab_btns.items():
            if k == key:
                btn.configure(fg_color=T["accent"], text_color=T["btn_primary_text"])
            else:
                btn.configure(fg_color="transparent", text_color=T["text_muted"])

        app_tabs = ("system", "core", "user", "thirdparty")
        if key in app_tabs:
            self._show_pkg_ui()
            self._render_app_tab(key)
        elif key == "logs":
            self._show_page_ui()
            self._build_logs_page()
        elif key == "settings":
            self._show_page_ui()
            self._build_settings_page()
        elif key == "about":
            self._show_page_ui()
            self._build_about_page()


    # ─── Package list rendering ────────────────────────────────────────────────

    def _render_app_tab(self, category: str, entries: list[AppEntry] = None):
        T    = self.T
        comp = True   # always compact — fixed layout

        all_entries = entries or self.app_data.get(category, [])

        # Cache check — skip rebuild if nothing changed
        cache_key = (category, comp, len(all_entries),
                     sum(1 for e in all_entries if e.checked),
                     sum(1 for e in all_entries if e.state != "enabled"))
        if not entries and self._render_cache.get(category) == cache_key:
            return

        # Clear scroll
        for w in self.pkg_scroll.winfo_children():
            w.destroy()

        if not all_entries:
            msg = ("No device scanned yet. Click Scan after connecting."
                   if not self.device_info else "No packages in this category.")
            ctk.CTkLabel(self.pkg_scroll, text=msg,
                         font=("Segoe UI", 12), text_color=T["text_muted"]).pack(pady=40)
            self.count_lbl.configure(text="0 packages")
            self.info_lbl.configure(text="💾  No device scanned yet")
            return

        # Group by subcategory — build flat list of (type, data) to render
        subcats: dict[str, list[AppEntry]] = {}
        for e in all_entries:
            subcats.setdefault(e.subcategory or "Other", []).append(e)

        # Build render queue: (header_title, [entries]) pairs
        render_queue = list(subcats.items())
        total_count  = len(all_entries)

        # Update labels immediately
        self.count_lbl.configure(text=f"{total_count} packages")
        checked = sum(1 for e in all_entries if getattr(e, "checked", False))
        self.info_lbl.configure(text=f"💾  {total_count} packages  ·  {checked} selected")

        # Update subcategory filter
        full_entries = self.app_data.get(category, [])
        subcats_list = sorted(set(e.subcategory for e in full_entries if e.subcategory))
        self.subcat_menu.configure(values=["All"] + subcats_list)

        # Chunked rendering — render one subcategory group per after() call
        # This keeps the UI responsive instead of freezing for 540 rows
        CHUNK = 50   # rows per chunk

        def render_chunk(queue_idx: int, item_idx: int):
            if queue_idx >= len(render_queue):
                # All done — store cache
                if not entries:
                    self._render_cache[category] = cache_key
                return

            subcat, items = render_queue[queue_idx]

            # Build header only at start of this group
            if item_idx == 0:
                hdr = ctk.CTkFrame(self.pkg_scroll, fg_color=T["accent"],
                                   corner_radius=4, height=30)
                hdr.pack(fill="x", pady=(6, 1))
                hdr.pack_propagate(False)
                ctk.CTkLabel(hdr, text=f"⚙  {subcat}", font=("Segoe UI", 10, "bold"),
                             text_color=T["btn_primary_text"], anchor="w").pack(side="left", padx=10)
                ctk.CTkButton(hdr, text="✓", width=24, height=18, corner_radius=3,
                              fg_color=T["accent_dim"], text_color=T["btn_primary_text"],
                              hover_color=T["accent"],
                              command=lambda c=category: self._select_all(c, True)
                              ).pack(side="right", padx=(1, 5))
                ctk.CTkButton(hdr, text="✕", width=24, height=18, corner_radius=3,
                              fg_color=T["accent_dim"], text_color=T["btn_primary_text"],
                              hover_color=T["accent"],
                              command=lambda c=category: self._select_all(c, False)
                              ).pack(side="right", padx=1)

            # Render up to CHUNK rows from current group
            end_idx = min(item_idx + CHUNK, len(items))
            for entry in items[item_idx:end_idx]:
                self._build_package_row(self.pkg_scroll, entry)

            # Schedule next chunk
            if end_idx < len(items):
                # More items in this group
                self.after(15, lambda: render_chunk(queue_idx, end_idx))
            else:
                # Move to next group
                self.after(15, lambda: render_chunk(queue_idx + 1, 0))

        # Start rendering
        render_chunk(0, 0)

    def _filter_active_tab(self):
        cat    = self._active_tab
        if cat not in ("system", "core", "user", "thirdparty"):
            return
        entries = self.app_data.get(cat, [])
        subcat  = self.subcat_var.get()
        query   = self.search_var.get().lower().strip()
        if subcat != "All":
            entries = [e for e in entries if e.subcategory == subcat]
        if query:
            entries = [e for e in entries if query in e.pkg.lower() or query in e.name.lower()]
        self._render_app_tab(cat, entries)

    # ─── Package row ──────────────────────────────────────────────────────────

    def _build_package_row(self, parent, entry: AppEntry):
        T       = self.T
        is_keep = entry.risk == "KEEP"
        is_core = entry.risk == "CORE"
        row_h   = 34

        row = ctk.CTkFrame(parent,
                           fg_color=T["bg_card"] if entry.state == "enabled" else T["disabled_bg"],
                           corner_radius=3, height=row_h)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        # ── Checkbox ─────────────────────────────────────────────────────────
        cb_wrap = ctk.CTkFrame(row, fg_color="transparent", width=30)
        cb_wrap.pack(side="left", padx=(6, 0))
        cb_wrap.pack_propagate(False)
        var = tk.BooleanVar(value=entry.checked)
        ctk.CTkCheckBox(cb_wrap, variable=var, text="",
                        checkbox_width=15, checkbox_height=15,
                        fg_color=T["core_red"] if is_core else T["accent"],
                        hover_color=T["accent_dim"],
                        state="disabled" if is_keep else "normal",
                        command=lambda e=entry, v=var: self._on_check(e, v, is_core)
                        ).pack(expand=True)
        entry._var       = var
        entry._row_frame = row

        # ── RIGHT: state label only ───────────────────────────────────────────
        state_lbl = ctk.CTkLabel(row, text=entry.state.title(),
                                 font=("Segoe UI", 9, "bold"),
                                 text_color=get_state_color(entry.state),
                                 width=72, anchor="e")
        state_lbl.pack(side="right", padx=(2, 8))
        entry._state_lbl = state_lbl

        # ── Risk badge ───────────────────────────────────────────────────────
        risk_color = get_risk_color(entry.risk, self.current_theme_name)
        bw = ctk.CTkFrame(row, fg_color="transparent", width=100)
        bw.pack(side="left", padx=(3, 0))
        bw.pack_propagate(False)
        ctk.CTkLabel(bw, text=get_risk_label(entry.risk), font=("Segoe UI", 9, "bold"),
                     text_color=risk_color, anchor="w").pack(fill="x", expand=True, padx=2)

        # ── Info frame ───────────────────────────────────────────────────────
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=(3, 2))

        name_text = entry.name if entry.in_db else f"{entry.name} *"

        ctk.CTkLabel(info, text=name_text, font=("Segoe UI", 11, "bold"),
                     text_color=T["text_dim"] if is_keep else T["text"],
                     anchor="w").pack(side="left", padx=(0, 8))
        ctk.CTkLabel(info, text=entry.pkg, font=("Consolas", 9),
                     text_color=T["text_dim"], anchor="e").pack(side="right", padx=(0, 4))

    # ─── Non-package pages (built fresh into page_frame) ─────────────────────

    def _build_logs_page(self):
        T = self.T
        p = self.page_frame

        bar = ctk.CTkFrame(p, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 6))
        ctk.CTkButton(bar, text="Export Log", width=100, height=28,
                      fg_color=T["bg_card"], text_color=T["text"],
                      hover_color=T["bg_hover"], command=self._export_log).pack(side="left", padx=(0, 6))
        ctk.CTkButton(bar, text="Clear", width=60, height=28,
                      fg_color=T["bg_card"], text_color=T["text_muted"],
                      hover_color=T["bg_hover"], command=self._clear_log).pack(side="left")

        log_view = ctk.CTkTextbox(p, fg_color=T["log_bg"], text_color=T["text"],
                                  font=("Consolas", 11), corner_radius=6,
                                  scrollbar_button_color=T["scrollbar"])
        log_view.pack(fill="both", expand=True)
        log_view.configure(state="disabled")
        try:
            content = self.log_text.get("1.0", "end")
            log_view.configure(state="normal")
            log_view.insert("1.0", content)
            log_view.see("end")
            log_view.configure(state="disabled")
        except Exception:
            pass

    def _build_settings_page(self):
        T = self.T
        p = self.page_frame

        scroll = ctk.CTkScrollableFrame(p, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        def section(title):
            ctk.CTkLabel(scroll, text=title, font=("Segoe UI", 11, "bold"),
                         text_color=T["accent"]).pack(anchor="w", pady=(10, 2))
            ctk.CTkFrame(scroll, fg_color=T["border"], height=1).pack(fill="x", pady=(0, 7))

        def row(label, widget_fn):
            fr = ctk.CTkFrame(scroll, fg_color="transparent")
            fr.pack(fill="x", pady=3)
            ctk.CTkLabel(fr, text=label, font=("Segoe UI", 10), text_color=T["text"],
                         width=160, anchor="w").pack(side="left")
            widget_fn(fr)

        section("ADB Configuration")
        self.adb_path_var = tk.StringVar(value=self.adb.adb_path)
        def adb_row(fr):
            ctk.CTkEntry(fr, textvariable=self.adb_path_var, width=260,
                         fg_color=T["bg_card"], border_color=T["border"],
                         text_color=T["text"], height=28).pack(side="left", padx=(0,5))
            ctk.CTkButton(fr, text="Browse", width=66, height=28, fg_color=T["bg_card"],
                          text_color=T["text"], command=self._browse_adb).pack(side="left", padx=(0,5))
            ctk.CTkButton(fr, text="Test ADB", width=76, height=28, fg_color=T["accent"],
                          text_color=T["btn_primary_text"], command=self._test_adb).pack(side="left")
        row("ADB executable", adb_row)

        section("Backup")
        self.backup_path_var = tk.StringVar(value=self.debloater.backup_dir)
        def bk_row(fr):
            ctk.CTkEntry(fr, textvariable=self.backup_path_var, width=260,
                         fg_color=T["bg_card"], border_color=T["border"],
                         text_color=T["text"], height=28).pack(side="left", padx=(0,5))
            ctk.CTkButton(fr, text="Browse", width=66, height=28, fg_color=T["bg_card"],
                          text_color=T["text"], command=self._browse_backup).pack(side="left", padx=(0,5))
            ctk.CTkButton(fr, text="Open Folder", width=88, height=28, fg_color=T["bg_card"],
                          text_color=T["text"],
                          command=lambda: os.startfile(self.debloater.backup_dir)
                              if os.path.exists(self.debloater.backup_dir) else None
                          ).pack(side="left")
        row("Backup folder", bk_row)

        section("Appearance")
        def theme_row(fr):
            for name in THEMES:
                t = get_theme(name)
                ctk.CTkButton(fr, text=name, width=76, height=28,
                              fg_color=t["accent"], text_color=t["btn_primary_text"],
                              command=lambda n=name: self._switch_theme(n)).pack(side="left", padx=(0,5))
        row("Theme", theme_row)

        section("Emergency Recovery")
        ctk.CTkButton(scroll, text="⚡  Panic Restore — re-enable all from latest backup",
                      font=("Segoe UI", 10, "bold"), fg_color=T["core_red"],
                      text_color="#ffffff", hover_color="#cc0000", height=34,
                      command=self._panic_restore).pack(anchor="w", pady=6)
        ctk.CTkLabel(scroll, text="Re-enables all packages from the most recent automatic backup.",
                     font=("Segoe UI", 9), text_color=T["text_muted"]).pack(anchor="w")

    def _build_about_page(self):
        T = self.T
        p = self.page_frame

        scroll = ctk.CTkScrollableFrame(p, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # ── Info card: logo + details side by side ───────────────────────────
        card = ctk.CTkFrame(scroll, fg_color=T["bg_card"], corner_radius=8,
                            border_width=1, border_color=T["border"])
        card.pack(fill="x", pady=(0, 5))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(10, 6))
        logo_img = _load_logo(44)
        if logo_img:
            ctk.CTkLabel(hdr, image=logo_img, text="").pack(side="left", padx=(0, 10))
        name_col = ctk.CTkFrame(hdr, fg_color="transparent")
        name_col.pack(side="left", anchor="w")
        ctk.CTkLabel(name_col, text=APP_NAME, font=("Segoe UI", 14, "bold"),
                     text_color=T["accent"], anchor="w").pack(anchor="w")
        ctk.CTkLabel(name_col, text=f"{APP_VERSION}  ·  {APP_BRAND}  ·  Chennai, India",
                     font=("Segoe UI", 9), text_color=T["text_muted"]).pack(anchor="w")
        ctk.CTkLabel(name_col, text="Works with Samsung Galaxy Devices",
                     font=("Segoe UI", 9), text_color=T["text_dim"]).pack(anchor="w")

        ctk.CTkFrame(card, fg_color=T["border"], height=1).pack(fill="x", padx=14, pady=(0, 4))

        info_grid = ctk.CTkFrame(card, fg_color="transparent")
        info_grid.pack(fill="x", padx=14, pady=(0, 8))
        for label, value in [
            ("Author", APP_AUTHOR), ("License", APP_LICENSE),
            ("Platform", "Windows 10 / 11"), ("Version", APP_VERSION),
        ]:
            r = ctk.CTkFrame(info_grid, fg_color="transparent")
            r.pack(fill="x", pady=1)
            ctk.CTkLabel(r, text=label, font=("Segoe UI", 9), text_color=T["text_muted"],
                         width=65, anchor="w").pack(side="left")
            ctk.CTkLabel(r, text=value, font=("Segoe UI", 9, "bold"),
                         text_color=T["text"], anchor="w").pack(side="left")

        # GitHub + version in one strip
        strip = ctk.CTkFrame(scroll, fg_color=T["bg_card"], corner_radius=6,
                             border_width=1, border_color=T["border"])
        strip.pack(fill="x", pady=(0, 5))
        ctk.CTkButton(strip, text=f"🔗  GitHub — {APP_GITHUB}", font=("Segoe UI", 9),
                      fg_color="transparent", text_color=T["accent"],
                      hover_color=T["bg_hover"], height=28, anchor="w",
                      command=lambda: webbrowser.open(APP_GITHUB)).pack(fill="x", padx=8)
        ctk.CTkLabel(strip, text=f"☑  Latest version ({APP_VERSION})",
                     font=("Segoe UI", 9), text_color=T["text_muted"],
                     anchor="w").pack(fill="x", padx=12, pady=(0, 6))

        # ── Donate card: buttons side by side ────────────────────────────────
        don_card = ctk.CTkFrame(scroll, fg_color=T["bg_card"], corner_radius=8,
                                border_width=1, border_color=T["border"])
        don_card.pack(fill="x", pady=(0, 5))

        don_hdr = ctk.CTkFrame(don_card, fg_color="transparent")
        don_hdr.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(don_hdr, text="💙  Support DebloatKit",
                     font=("Segoe UI", 10, "bold"), text_color=T["text"]).pack(side="left")
        ctk.CTkLabel(don_hdr, text="Free forever — support if it helped!",
                     font=("Segoe UI", 8), text_color=T["text_muted"]).pack(side="right")

        don_btns = ctk.CTkFrame(don_card, fg_color="transparent")
        don_btns.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkButton(don_btns, text="💙  PayPal ($)",
                      font=("Segoe UI", 10, "bold"), fg_color="#003087",
                      text_color="#FFFFFF", hover_color="#001f5b", height=30,
                      command=lambda: webbrowser.open("https://paypal.me/yash92duster")
                      ).pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkButton(don_btns, text="🟦  Razorpay (₹)",
                      font=("Segoe UI", 10, "bold"), fg_color=T["accent"],
                      text_color=T["btn_primary_text"], hover_color=T["accent_dim"], height=30,
                      command=lambda: webbrowser.open("https://rzp.io/rzp/nsogoeD")
                      ).pack(side="left", fill="x", expand=True)

        # ── Credits ───────────────────────────────────────────────────────────
        cred = ctk.CTkFrame(scroll, fg_color=T["bg_card"], corner_radius=8,
                            border_width=1, border_color=T["border"])
        cred.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(cred, text="Credits", font=("Segoe UI", 9, "bold"),
                     text_color=T["accent"]).pack(anchor="w", padx=12, pady=(6, 3))
        for cname, cdesc in [
            ("XDA Community", "Package safety ratings from XDA forums and Samsung debloat threads."),
            ("Google Research", "AOSP ADB docs, pm command reference, Android developer documentation."),
        ]:
            r = ctk.CTkFrame(cred, fg_color="transparent")
            r.pack(fill="x", padx=12, pady=(0, 4))
            ctk.CTkLabel(r, text=f"· {cname}", font=("Segoe UI", 9, "bold"),
                         text_color=T["text"], anchor="w").pack(anchor="w")
            ctk.CTkLabel(r, text=cdesc, font=("Segoe UI", 8), text_color=T["text_muted"],
                         anchor="w", wraplength=500, justify="left").pack(anchor="w")
        ctk.CTkFrame(cred, fg_color="transparent", height=4).pack()

        # ── USB Debugging guide ───────────────────────────────────────────────
        usb_card = ctk.CTkFrame(scroll, fg_color=T["bg_card"], corner_radius=8,
                                border_width=1, border_color=T["border"])
        usb_card.pack(fill="x", pady=(0, 5))

        usb_hdr = ctk.CTkFrame(usb_card, fg_color="transparent")
        usb_hdr.pack(fill="x", padx=12, pady=(8, 4))
        ctk.CTkLabel(usb_hdr, text="📱  How to Use DebloatKit",
                     font=("Segoe UI", 10, "bold"), text_color=T["accent"]).pack(side="left")

        steps_enable = [
            ("Enable USB Debugging", [
                "Settings → About Phone → Software Information",
                "Tap Build Number 7 times → 'Developer mode enabled'",
                "Settings → Developer Options → USB Debugging → ON",
                "Connect phone to PC via USB",
                "Tap 'Allow' on phone when prompted",
                "Click Scan in DebloatKit",
            ]),
            ("After Debloating — Disable USB Debugging", [
                "Settings → Developer Options → USB Debugging → OFF",
                "Optional: Developer Options → OFF to hide the menu",
                "Disconnect USB cable",
            ]),
        ]

        for section_title, steps in steps_enable:
            ctk.CTkLabel(usb_card, text=section_title,
                         font=("Segoe UI", 9, "bold"),
                         text_color=T["text"], anchor="w").pack(anchor="w", padx=12, pady=(4, 2))
            for i, step in enumerate(steps, 1):
                row = ctk.CTkFrame(usb_card, fg_color=T["bg"], corner_radius=4)
                row.pack(fill="x", padx=12, pady=1)
                ctk.CTkLabel(row, text=str(i), font=("Segoe UI", 9, "bold"),
                             text_color=T["accent"], width=18, anchor="center").pack(side="left", padx=(6, 4), pady=4)
                ctk.CTkLabel(row, text=step, font=("Segoe UI", 9),
                             text_color=T["text_muted"], anchor="w").pack(side="left", padx=(0, 6), pady=4)

        ctk.CTkLabel(usb_card,
                     text="⚠  Always disable USB Debugging after use for security.",
                     font=("Segoe UI", 8, "bold"), text_color=T["warning"],
                     anchor="w").pack(anchor="w", padx=12, pady=(4, 8))

        # ── Disclaimer one line ───────────────────────────────────────────────
        ctk.CTkLabel(scroll,
                     text="Not affiliated with Samsung Electronics Co., Ltd.  ·  MIT License  ·  Free to use, modify and distribute.",
                     font=("Segoe UI", 8), text_color=T["text_dim"],
                     justify="center").pack(pady=(2, 8))

    # ─── Selection & filtering ────────────────────────────────────────────────

    def _on_check(self, entry: AppEntry, var: tk.BooleanVar, is_core: bool):
        if is_core and var.get():
            self._show_core_warning(entry, var)
        else:
            entry.checked = var.get()

    def _show_core_warning(self, entry: AppEntry, var: tk.BooleanVar):
        T = self.T
        win = ctk.CTkToplevel(self)
        win.title("Core System App")
        win.geometry("500x290")
        win.configure(fg_color=T["bg"])
        win.grab_set()
        win.resizable(False, False)
        ctk.CTkLabel(win, text="⛔  Core System App",
                     font=("Segoe UI", 14, "bold"), text_color=T["core_red"]).pack(pady=(18, 3))
        ctk.CTkLabel(win, text=f"{entry.name}", font=("Segoe UI", 12, "bold"),
                     text_color=T["text"]).pack()
        ctk.CTkLabel(win, text=entry.pkg, font=("Consolas", 9),
                     text_color=T["text_muted"]).pack(pady=(0, 7))
        mf = ctk.CTkFrame(win, fg_color="#1a0505", corner_radius=7,
                          border_width=1, border_color=T["core_red"])
        mf.pack(fill="x", padx=18, pady=3)
        ctk.CTkLabel(mf,
                     text=f"{entry.description}\n\n"
                          "⚠ Disabling may affect device stability.\n"
                          "✓ Reversible — re-enable anytime while device is connected.",
                     font=("Segoe UI", 10), text_color=T["text"],
                     wraplength=420, justify="left").pack(padx=10, pady=8)
        br = ctk.CTkFrame(win, fg_color="transparent")
        br.pack(pady=12)
        ctk.CTkButton(br, text="Cancel", width=110, fg_color=T["bg_hover"],
                      text_color=T["text"],
                      command=lambda: [var.set(False), setattr(entry, "checked", False), win.destroy()]
                      ).pack(side="left", padx=7)
        ctk.CTkButton(br, text="I understand, proceed", width=170, fg_color=T["core_red"],
                      text_color="#ffffff",
                      command=lambda: [setattr(entry, "checked", True), win.destroy()]
                      ).pack(side="left", padx=7)

    def _select_all(self, category: str, state: bool):
        for e in self.app_data.get(category, []):
            if e.risk not in ("KEEP",) and (not state or e.risk != "CORE"):
                e.checked = state
                if hasattr(e, "_var"):
                    e._var.set(state)

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
            messagebox.showinfo("Nothing Selected", "Check at least one package first.")
            return

        action_labels = {
            "disable":   "Disable",
            "uninstall": "Uninstall",
            "enable":    "Re-enable",
        }
        verb = action_labels.get(action, action)

        action_descs = {
            "disable":   "Freeze selected apps (reversible — re-enable anytime).",
            "uninstall": "Remove from user profile (reversible — APK stays on device).",
            "enable":    "Restore all selected disabled/uninstalled apps.",
        }
        desc = action_descs.get(action, "")

        if not messagebox.askyesno(
            f"Confirm — {verb} {len(selected)} app(s)",
            f"{verb} {len(selected)} selected package(s)?\n\n{desc}"
        ):
            return

        self._action_running = True

        # Disable all 3 action buttons while running
        for btn in (self.disable_btn, self.uninstall_btn, self.reenable_btn):
            try:
                btn.configure(state="disabled")
            except Exception:
                pass

        self.status_prog.set(0)
        all_entries = [e for cat in self.app_data.values() for e in cat]

        def progress_cb(val, msg):
            self.after(0, lambda: self.status_prog.set(val))
            self.after(0, lambda: self.status_text.configure(text=msg))

        def result_cb(entry: AppEntry, result):
            def upd():
                try:
                    if hasattr(entry, "_state_lbl") and entry._state_lbl.winfo_exists():
                        entry._state_lbl.configure(text=entry.state.title(),
                                                   text_color=get_state_color(entry.state))
                    if hasattr(entry, "_row_frame") and entry._row_frame.winfo_exists():
                        color = self.T["disabled_bg"] if entry.state in ("disabled","uninstalled") else self.T["bg_card"]
                        entry._row_frame.configure(fg_color=color)
                except Exception:
                    pass
            self.after(0, upd)

        def run():
            if action == "disable":
                results = self.debloater.disable_packages(selected, all_entries, progress_cb, result_cb)
            elif action == "uninstall":
                results = self.debloater.uninstall_packages(selected, all_entries, progress_cb, result_cb)
            else:
                results = self.debloater.restore_packages(selected, progress_cb, result_cb)

            summary = self.debloater.get_summary(results)

            def done():
                try:
                    for btn in (self.disable_btn, self.uninstall_btn, self.reenable_btn):
                        btn.configure(state="normal")
                    self._show_summary(summary, verb)
                    self.status_text.configure(
                        text=f"{verb} complete — {summary['success']} succeeded · {summary['failed']} failed"
                    )
                    # Re-render tab so per-row buttons update correctly
                    self._render_cache.clear()
                    if self._active_tab in ("system","core","user","thirdparty"):
                        self._render_app_tab(self._active_tab)
                except Exception:
                    pass

            self.after(0, done)
            self._action_running = False

            if action in ("disable", "uninstall"):
                if any(e.pkg == "com.sec.android.diagmonagent" for e in selected):
                    self.after(500, self._offer_soundalive_fix)

        threading.Thread(target=run, daemon=True).start()

    def _show_summary(self, summary: dict, action: str):
        T = self.T
        win = ctk.CTkToplevel(self)
        win.title("Done")
        win.geometry("340x190")
        win.configure(fg_color=T["bg"])
        win.grab_set()
        ctk.CTkLabel(win, text="✓  Complete", font=("Segoe UI", 14, "bold"),
                     text_color=T["success"]).pack(pady=(16, 7))
        info = ctk.CTkFrame(win, fg_color=T["bg_card"], corner_radius=7)
        info.pack(fill="x", padx=22, pady=3)
        def row(label, value, color=None):
            fr = ctk.CTkFrame(info, fg_color="transparent")
            fr.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(fr, text=label, font=("Segoe UI", 10), text_color=T["text_muted"]).pack(side="left")
            ctk.CTkLabel(fr, text=str(value), font=("Segoe UI", 10, "bold"),
                         text_color=color or T["text"]).pack(side="right")
        row("Action", action.title())
        row("Succeeded", summary["success"], T["success"])
        if summary["failed"] > 0:
            row("Failed", summary["failed"], T["error"])
        row("Backup", "Saved automatically", T["accent"])
        ctk.CTkButton(win, text="Close", fg_color=T["accent"],
                      text_color=T["btn_primary_text"], width=90,
                      command=win.destroy).pack(pady=12)

    def _offer_soundalive_fix(self):
        if messagebox.askyesno("SoundAlive Fix",
                               "Diagnostic Monitor was removed.\nRun SoundAlive flush? (Recommended)"):
            self.debloater.soundalive_fix()

    # ─── Log ──────────────────────────────────────────────────────────────────

    def _toggle_log_panel(self):
        if self.log_visible:
            self.log_panel.place_forget()
            self.log_visible = False
            self.log_btn.configure(fg_color=self.T["bg_card"])
        else:
            # Overlay on right side using place
            self.log_panel.place(relx=1.0, rely=0.0, relheight=0.85, anchor="ne", x=-2, y=56)
            self.log_panel.lift()
            self.log_visible = True
            self.log_btn.configure(fg_color=self.T["accent"])

    def _log(self, message: str, level: str = "info"):
        T    = self.T
        cmap = {"info": T["log_info"], "success": T["log_success"],
                "warning": T["log_warning"], "error": T["log_error"]}
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n"
        def upd():
            try:
                if hasattr(self, "log_text") and self.log_text.winfo_exists():
                    self.log_text.configure(state="normal")
                    self.log_text.insert("end", line)
                    self.log_text.see("end")
                    self.log_text.configure(state="disabled")
            except Exception:
                pass
        self.after(0, upd)

    def _clear_log(self):
        try:
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", "end")
            self.log_text.configure(state="disabled")
        except Exception:
            pass

    def _export_log(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt",
               filetypes=[("Text","*.txt")],
               initialfile=f"DebloatKit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.log_text.get("1.0", "end"))
                self._log(f"Log exported: {path}", "success")
            except Exception as e:
                self._log(f"Export failed: {e}", "error")

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
        def upd():
            try:
                self.status_dot.configure(text_color=colors.get(status, "#333333"))
                self.status_label.configure(text=labels.get(status, status))
                # Only show USB guide once per unauthorized session — not on every poll
                if status == "unauthorized" and not getattr(self, "_usb_guide_shown", False):
                    self._usb_guide_shown = True
                    self.after(300, self._show_usb_guide)
                elif status != "unauthorized":
                    self._usb_guide_shown = False
            except Exception:
                pass
        self.after(0, upd)

    def _on_device_connected(self, info: DeviceInfo):
        self.device_info = info
        def upd():
            try:
                self.dev_model_lbl.configure(text=f"{info.brand} {info.model}",
                                             text_color=self.T["text"])
                self.dev_info_lbl.configure(
                    text=f"Android {info.android_version}  ·  One UI {info.oneui_version or '?'}  ·  API {info.api_level}  ·  {info.get_era_label()}",
                    text_color=self.T["text_muted"])
                bat_clr = self.T["error"] if info.battery_level < 20 else self.T["text_muted"]
                self.bat_lbl.configure(text=f"🔋 {info.battery_level}%", text_color=bat_clr)
                self.scan_btn.configure(state="normal")
                self.status_text.configure(text=f"Device ready — {info.brand} {info.model}")
            except Exception:
                pass
        self.after(0, upd)

    def _on_device_disconnected(self):
        self.device_info = None
        # Clear app data so tabs show "no device" message
        self.app_data = {"system": [], "core": [], "user": [], "thirdparty": [], "keep": []}
        def upd():
            try:
                self.dev_model_lbl.configure(text="No device connected", text_color=self.T["text_muted"])
                self.dev_info_lbl.configure(text="Connect via USB · Enable USB Debugging",
                                            text_color=self.T["text_dim"])
                self.bat_lbl.configure(text="")
                self.scan_btn.configure(state="disabled", text="⟳  Scan")
                self.status_text.configure(text="Device disconnected.")
                self._usb_guide_shown = False
                # Refresh current tab to show empty state
                if self._active_tab in ("system", "core", "user", "thirdparty"):
                    for w in self.pkg_scroll.winfo_children():
                        w.destroy()
                    ctk.CTkLabel(
                        self.pkg_scroll,
                        text="Device disconnected. Connect your device and click Scan.",
                        font=("Segoe UI", 12), text_color=self.T["text_muted"]
                    ).pack(pady=40)
                    self.count_lbl.configure(text="")
                    self.info_lbl.configure(text="💾  No device connected")
            except Exception:
                pass
        self.after(0, upd)

    def _show_usb_guide(self):
        # Don't open if already open
        if getattr(self, "_usb_guide_win", None) and self._usb_guide_win.winfo_exists():
            return
        T = self.T
        win = ctk.CTkToplevel(self)
        win.title("Enable USB Debugging")
        win.geometry("480x360")
        win.configure(fg_color=T["bg"])
        win.resizable(False, False)
        # Do NOT grab_set — lets user keep using the app
        win.lift()
        self._usb_guide_win = win

        ctk.CTkLabel(win, text="Enable USB Debugging",
                     font=("Segoe UI", 14, "bold"), text_color=T["accent"]).pack(pady=(14, 8))
        for i, step in enumerate([
            "Open Settings on your Galaxy device",
            "Go to About Phone → Software Information",
            "Tap Build Number 7 times to unlock Developer Options",
            "Go back to Settings → Developer Options",
            "Enable USB Debugging",
            "Connect via USB — tap Allow on your phone",
            "DebloatKit detects your device automatically",
        ], 1):
            r = ctk.CTkFrame(win, fg_color=T["bg_card"], corner_radius=5)
            r.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(r, text=str(i), font=("Segoe UI", 10, "bold"),
                         text_color=T["accent"], width=22).pack(side="left", padx=9, pady=5)
            ctk.CTkLabel(r, text=step, font=("Segoe UI", 10),
                         text_color=T["text"], anchor="w").pack(side="left", padx=4)
        ctk.CTkButton(win, text="Got it", fg_color=T["accent"],
                      text_color=T["btn_primary_text"], width=110,
                      command=win.destroy).pack(pady=10)

    def _start_scan(self):
        if self._scanning:
            return
        if not self.device_info:
            messagebox.showerror("No Device", "Connect your device first.")
            return
        self._scanning = True
        self.scan_btn.configure(state="disabled", text="Scanning...")
        self.status_text.configure(text="Scanning device packages...")
        self.status_prog.set(0)

        def progress_cb(val, msg):
            self.after(0, lambda: self.status_prog.set(val))
            self.after(0, lambda: self.status_text.configure(text=msg))

        def run():
            data = self.scanner.scan(self.device_info, progress_callback=progress_cb)
            self.app_data = data
            def done():
                try:
                    self.scan_btn.configure(state="normal", text="⟳  Re-Scan")
                    self._scanning = False
                    self._render_cache.clear()   # force re-render after scan
                    self._render_app_tab(self._active_tab)
                    total = sum(len(v) for v in data.values())
                    self.status_text.configure(text=f"Scan complete — {total} packages found")
                except Exception:
                    pass
            self.after(0, done)

        threading.Thread(target=run, daemon=True).start()

    # ─── Settings helpers ─────────────────────────────────────────────────────

    def _browse_adb(self):
        path = filedialog.askopenfilename(filetypes=[("ADB","adb.exe"),("All","*.*")])
        if path:
            self.adb_path_var.set(path)
            self.adb.adb_path = path

    def _test_adb(self):
        self.adb.adb_path = self.adb_path_var.get()
        # First check: can the exe run at all?
        ok_exe, _ = self.adb.run(["version"], timeout=5)
        if not ok_exe:
            messagebox.showerror("ADB Not Found",
                                 f"ADB executable not found at:\n{self.adb_path_var.get()}\n\n"
                                 "Download Platform Tools and set the correct path.")
            return
        # Second check: is a device actually connected?
        ok_dev, out = self.adb.run(["devices"], timeout=5)
        lines = [l for l in out.splitlines()[1:] if l.strip() and "\t" in l]
        if lines:
            device_line = lines[0]
            messagebox.showinfo("ADB Working",
                                f"ADB found and device detected!\n\n{device_line.strip()}")
        else:
            messagebox.showinfo("ADB Found — No Device",
                                "ADB executable is working correctly.\n\n"
                                "No device detected. Connect your Galaxy device\n"
                                "and enable USB Debugging.")

    def _browse_backup(self):
        path = filedialog.askdirectory()
        if path:
            self.backup_path_var.set(path)
            self.debloater.backup_dir = path

    def _panic_restore(self):
        bp = self.debloater.get_latest_backup_path()
        if not bp:
            messagebox.showinfo("Panic Restore", "No backups found.")
            return
        if not self.device_info:
            messagebox.showerror("No Device", "Device must be connected.")
            return
        if messagebox.askyesno("Panic Restore",
                               f"Re-enable ALL from:\n{os.path.basename(bp)}\n\nProceed?"):
            threading.Thread(target=self.debloater.panic_restore, args=(bp,), daemon=True).start()

    def on_close(self):
        self.adb.stop_polling()
        self.destroy()


def main():
    app = DebloatKit()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()


if __name__ == "__main__":
    main()
