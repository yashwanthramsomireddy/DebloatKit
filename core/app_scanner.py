"""
DebloatKit v1.0 — App Scanner
Scans installed packages and cross-references with the master package database.
Author: Yashwanth Ram Somireddy | TeamExyKings | MIT License
"""

import json
import os
from typing import Optional, Callable
from core.adb_manager import ADBManager, DeviceInfo


class AppEntry:
    def __init__(self):
        self.pkg: str = ""
        self.name: str = ""
        self.category: str = "system"   # system | core | user | thirdparty | keep
        self.subcategory: str = ""
        self.risk: str = "SAFE"         # SAFE | RECOMMENDED | CAUTION | CORE | LOCKED | KEEP
        self.path: str = "A"            # A | B | NONE
        self.description: str = ""
        self.state: str = "enabled"     # enabled | disabled | uninstalled
        self.in_db: bool = False        # known package or unknown
        self.checked: bool = False      # checkbox state

    def to_dict(self) -> dict:
        return {
            "pkg": self.pkg,
            "name": self.name,
            "category": self.category,
            "subcategory": self.subcategory,
            "risk": self.risk,
            "path": self.path,
            "description": self.description,
            "state": self.state
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AppEntry":
        e = cls()
        e.pkg = d.get("pkg", "")
        e.name = d.get("name", e.pkg)
        e.category = d.get("category", "system")
        e.subcategory = d.get("subcategory", "")
        e.risk = d.get("risk", "SAFE")
        e.path = d.get("path", "A")
        e.description = d.get("description", "")
        e.state = d.get("state", "enabled")
        return e


class AppScanner:
    def __init__(self, adb: ADBManager, db_path: str = None, log_callback: Optional[Callable] = None):
        self.adb = adb
        self.log_callback = log_callback
        self.db_path = db_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "packages.json"
        )
        self._db: list[dict] = []
        self._db_index: dict[str, dict] = {}
        self._load_db()

    def log(self, msg: str, level: str = "info"):
        if self.log_callback:
            self.log_callback(msg, level)

    def _load_db(self):
        """Load and index the package database."""
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                raw = f.read()
            # Strip JS-style comments for our annotated JSON
            import re
            raw = re.sub(r"//.*", "", raw)
            data = json.loads(raw)
            self._db = data.get("packages", [])
            self._db_index = {p["pkg"]: p for p in self._db}
            self.log(f"Package DB loaded: {len(self._db)} packages", "info")
        except Exception as e:
            self.log(f"Failed to load package DB: {e}", "error")
            self._db = []
            self._db_index = {}

    def _make_entry(self, pkg: str, db_record: Optional[dict], state: str) -> AppEntry:
        e = AppEntry()
        e.pkg = pkg
        e.state = state
        e.checked = False

        if db_record:
            e.name = db_record.get("name", pkg)
            e.category = db_record.get("category", "system")
            e.subcategory = db_record.get("subcategory", "")
            e.risk = db_record.get("risk", "SAFE")
            e.path = db_record.get("path", "A")
            e.description = db_record.get("description", "")
            e.in_db = True
        else:
            # Unknown package — safe default, categorize by prefix
            e.name = pkg.split(".")[-1].replace("_", " ").title()
            e.in_db = False
            e.risk = "SAFE"
            e.path = "A"
            e.description = "Unknown package — not in DebloatKit database"
            if "google" in pkg:
                e.category = "user"
                e.subcategory = "Google (Unknown)"
            elif "samsung" in pkg or "sec." in pkg:
                e.category = "system"
                e.subcategory = "Samsung (Unknown)"
            elif "facebook" in pkg:
                e.category = "thirdparty"
                e.subcategory = "Facebook"
            elif "microsoft" in pkg:
                e.category = "thirdparty"
                e.subcategory = "Microsoft"
            else:
                e.category = "system"
                e.subcategory = "Other"

        return e

    def scan(self, device_info: DeviceInfo, progress_callback: Optional[Callable] = None) -> dict[str, list[AppEntry]]:
        """
        Full device scan. Returns dict with keys:
        system, core, user, thirdparty, keep
        """
        self.log("Starting device scan...", "info")
        result = {"system": [], "core": [], "user": [], "thirdparty": [], "keep": []}

        if progress_callback:
            progress_callback(0.05, "Scanning system packages...")

        system_pkgs = set(self.adb.list_packages("-s"))
        self.log(f"Found {len(system_pkgs)} system packages", "info")

        if progress_callback:
            progress_callback(0.25, "Scanning user packages...")

        user_pkgs = set(self.adb.list_packages("-3"))
        self.log(f"Found {len(user_pkgs)} user/3rd-party packages", "info")

        if progress_callback:
            progress_callback(0.45, "Scanning disabled packages...")

        disabled_pkgs = set(self.adb.list_packages("-s -d"))
        self.log(f"Found {len(disabled_pkgs)} disabled packages", "info")

        if progress_callback:
            progress_callback(0.60, "Cross-referencing database...")

        all_pkgs = system_pkgs | user_pkgs
        era = device_info.era

        for pkg in all_pkgs:
            db_rec = self._db_index.get(pkg)

            # Filter by era if in DB
            if db_rec:
                eras = db_rec.get("eras", [1, 2, 3])
                if era not in eras:
                    continue  # Skip packages not relevant to this device era

            state = "disabled" if pkg in disabled_pkgs else "enabled"
            entry = self._make_entry(pkg, db_rec, state)

            # Override category for KEEP packages
            if entry.risk == "KEEP":
                result["keep"].append(entry)
            else:
                result[entry.category].append(entry)

        # Sort each category alphabetically by name
        for cat in result:
            result[cat].sort(key=lambda x: x.name.lower())

        if progress_callback:
            progress_callback(1.0, "Scan complete")

        counts = {k: len(v) for k, v in result.items()}
        self.log(
            f"Scan complete — System: {counts['system']} | Core: {counts['core']} | "
            f"User: {counts['user']} | 3rd Party: {counts['thirdparty']} | Keep: {counts['keep']}",
            "success"
        )

        return result

    def get_db_entry(self, pkg: str) -> Optional[dict]:
        return self._db_index.get(pkg)

    def reload_db(self):
        self._load_db()
