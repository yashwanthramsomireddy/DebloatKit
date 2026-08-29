# ⬡ DebloatKit v1.0 — Complete Project Plan
> **Works with Samsung Galaxy Devices**
> Samsung Galaxy Debloater for Windows · TeamExyKings · MIT License

---

## 📋 Project Identity

| Field | Value |
|---|---|
| **App Name** | DebloatKit |
| **Version** | v1.0 |
| **Subtitle** | Works with Samsung Galaxy Devices |
| **Author** | Yashwanth Ram Somireddy |
| **Brand** | TeamExyKings |
| **Location** | Chennai, India |
| **License** | MIT — Free & Open Source |
| **Platform** | Windows 10 / 11 |
| **Language** | Python 3.11+ |
| **UI Framework** | CustomTkinter 6.0+ |
| **ADB** | subprocess — no root, `--user 0` only |
| **GitHub** | https://github.com/yashwanthramsomireddy/DebloatKit |
| **Started** | 2026-08-28 |
| **Status** | Active — v1.0 Released |

---

## 🛠️ Tech Stack

| Component | Technology | Version | Purpose |
|---|---|---|---|
| UI Framework | CustomTkinter | 6.0+ | Dark-theme desktop GUI |
| Language | Python | 3.11+ | Core application logic |
| ADB Bridge | subprocess | stdlib | Execute ADB shell commands |
| Package DB | JSON | custom | 110+ packages, risk ratings |
| Backup Engine | json (stdlib) | stdlib | Timestamped backup/restore |
| Threading | threading | stdlib | Non-blocking ADB operations |
| Distribution | PyInstaller | 6.x | Single `.exe` for Windows |
| Version Control | Git + GitHub | latest | Source control and releases |

---

## 🗂️ Project Structure

```
DebloatKit/
├── DebloatKit.py              ← Main entry point — full UI, all 7 tabs
├── core/
│   ├── adb_manager.py         ← ADB bridge — polling, Path A/B/C
│   ├── app_scanner.py         ← Live device scan + DB cross-reference
│   └── debloater.py           ← Disable/uninstall/restore/backup engine
├── ui/
│   └── themes.py              ← Green/Blue/Purple/White token system
├── data/
│   └── packages.json          ← 110+ packages, risk ratings, eras
├── backups/                   ← Auto-created — timestamped JSON backups
├── README.md
├── CHANGELOG.md
├── LICENSE
└── requirements.txt
```

---

## 📱 Device Compatibility

| Era | Devices | Android | One UI | API |
|---|---|---|---|---|
| 1 — Legacy TouchWiz | Galaxy S5, S6, S7, S8, S9 | 5.0–8.1 | TouchWiz / Grace UX | 21–27 |
| 2 — Mid One UI | S10–S23, Note 10/20, Z Fold 1–5 | 9–13 | One UI 1.x–5.x | 28–33 |
| 3 — Modern One UI | S24–S26 Ultra, Z Fold 6–8 Ultra | 14–16 | One UI 6.x–9 | 34–36 |

Auto-detected at runtime via `adb shell getprop ro.build.version.sdk`

---

## 📦 Package Database

| Category | Count | Risk Levels | Notes |
|---|---|---|---|
| System Apps | 66 | SAFE / CAUTION / RECOMMENDED | Samsung, Google, carrier |
| Core Apps | 7 | CORE / LOCKED | Confirmation dialog required |
| User Apps | 13 | SAFE | Google Play preloads |
| 3rd Party | 19 | SAFE / RECOMMENDED | Facebook, Microsoft, OEM |
| Keep | 5 | KEEP | Non-removable, grayed out |
| **TOTAL** | **110** | | Across 3 device eras |

### Risk Level Reference

| Badge | Color | Meaning | UI Behavior |
|---|---|---|---|
| `SAFE` | 🟢 Green | No system impact | Checkbox enabled |
| `RECOMMENDED` | 🟢 Bright | Known tracker/background service | Highlighted |
| `CAUTION` | 🟡 Amber | May affect features | Warning tooltip |
| `CORE` | 🔴 Red | System-critical | Per-app confirm dialog |
| `LOCKED` 🔒 | 🔴 Red | SecurityException pkg (One UI 6+) | Path B confirm |
| `KEEP` | ⬛ Gray | Never removable | Grayed out, non-selectable |

---

## 🔌 ADB Execution Paths

### Path A — Standard (All Eras)
```bash
# Disable (freeze app — fully reversible)
adb shell pm disable-user --user 0 <package>

# Uninstall from user profile only — APK stays on /system
adb shell pm uninstall -k --user 0 <package>

# Restore
adb shell pm enable --user 0 <package>
adb shell pm install-existing <package>
```

### Path B — Security Locked (One UI 6+)
For Knox, SwiftKey, Family Link — packages that throw `SecurityException` on standard disable:
```bash
# Force uninstall — breaks security lock
adb shell pm uninstall --user 0 <package>

# Restore — re-link APK to user 0 profile
adb shell cmd package install-existing --user 0 <package>
```

### Path C — SoundAlive Fix (Post-Debloat Hook)
Triggered after removing `com.sec.android.diagmonagent`:
```bash
adb shell am force-stop com.sec.android.app.soundalive
adb shell pm clear com.sec.android.app.soundalive
# Reboot recommended
```

---

## 🖥️ UI Tabs

| # | Tab | Contents |
|---|---|---|
| 1 | **System Apps** | Samsung/Google/carrier system apps · All unchecked by default |
| 2 | **Core Apps** | Critical system components · ⛔ per-app confirmation · All unchecked |
| 3 | **User Apps** | Google Play preloads and sideloaded apps |
| 4 | **3rd Party** | Facebook, Microsoft, OEM-injected bloat |
| 5 | **Logs** | Full timestamped ADB log · color-coded · export to .txt |
| 6 | **Settings** | ADB path, backup folder, themes, Panic Restore |
| 7 | **About** | Author card, donate, legal disclaimer |

**Bottom action bar on tabs 1–4:**
```
[ Select All ]  [ Deselect All ]  ────────────────  [ Disable Selected ]  [ Uninstall Selected ]
```

---

## 🛡️ Safety System

| Feature | Description |
|---|---|
| `--user 0` only | Never touches system partition — APK always intact |
| Auto silent backup | JSON snapshot before every action → `/backups/` |
| Panic Restore | One click re-enables all from latest backup |
| Per-row Re-enable | Restore any individual app instantly |
| Dry Run mode | Full preview — zero actual device changes |
| Core confirmation | ⛔ individual dialog per system-critical app |
| Factory reset | Ultimate fallback — restores all packages |

---

## ✅ Feature Tracker

| ID | Feature | Status | Version | Priority |
|---|---|---|---|---|
| F-001 | 7-Tab Layout | ✅ Done | v1.0 | P1 |
| F-002 | Live Device Polling (3s) | ✅ Done | v1.0 | P1 |
| F-003 | Device Info Strip | ✅ Done | v1.0 | P1 |
| F-004 | USB Debugging Guide | ✅ Done | v1.0 | P1 |
| F-005 | Package DB (110+ packages) | ✅ Done | v1.0 | P1 |
| F-006 | Live Device Scan | ✅ Done | v1.0 | P1 |
| F-007 | Risk Badges (6 levels) | ✅ Done | v1.0 | P1 |
| F-008 | Subcategory Grouping | ✅ Done | v1.0 | P1 |
| F-009 | Compact/Spacious Toggle | ✅ Done | v1.0 | P2 |
| F-010 | Select All / Deselect All | ✅ Done | v1.0 | P1 |
| F-011 | Disable Selected (Path A) | ✅ Done | v1.0 | P1 |
| F-012 | Uninstall Selected (Path A) | ✅ Done | v1.0 | P1 |
| F-013 | Path B Security Bypass | ✅ Done | v1.0 | P1 |
| F-014 | Path C SoundAlive Fix | ✅ Done | v1.0 | P2 |
| F-015 | Core Apps Tab | ✅ Done | v1.0 | P1 |
| F-016 | Core Confirmation Dialog | ✅ Done | v1.0 | P1 |
| F-017 | Per-Row Re-enable Button | ✅ Done | v1.0 | P1 |
| F-018 | Auto Silent Backup | ✅ Done | v1.0 | P1 |
| F-019 | Panic Restore | ✅ Done | v1.0 | P1 |
| F-020 | Dry Run Mode | ✅ Done | v1.0 | P1 |
| F-021 | Battery Warning (<20%) | ✅ Done | v1.0 | P2 |
| F-022 | Root Detection Advisory | ✅ Done | v1.0 | P3 |
| F-023 | 4 Themes | ✅ Done | v1.0 | P2 |
| F-024 | Full Log Tab + Export | ✅ Done | v1.0 | P1 |
| F-025 | Persistent Log Strip | ✅ Done | v1.0 | P2 |
| F-026 | Post-Action Summary Card | ✅ Done | v1.0 | P2 |
| F-027 | Search + Subcategory Filter | ✅ Done | v1.0 | P2 |
| F-028 | About Tab + Donate | ✅ Done | v1.0 | P2 |
| F-029 | ADB Path Override | ✅ Done | v1.0 | P2 |
| F-030 | Backup Folder Override | ✅ Done | v1.0 | P3 |
| F-031 | Package Size Display | 🔵 Planned | v1.1 | P2 |
| F-032 | Export as Shell Script | 🔵 Planned | v1.1 | P2 |
| F-033 | Wireless ADB Support | 🔵 Planned | v1.2 | P2 |
| F-034 | Multi-device Support | 🔵 Planned | v1.2 | P3 |
| F-035 | Custom Package List Import | 🔵 Planned | v1.2 | P2 |
| F-036 | 1-Click Presets | 🔵 Planned | v1.2 | P1 |
| F-037 | DB Auto-Update from GitHub | 🔵 Planned | v2.0 | P3 |
| F-038 | Windows Installer (.exe) | 🔵 Planned | v2.0 | P2 |

---

## 🐛 Issue Tracker

| ID | Title | Type | Severity | Status |
|---|---|---|---|---|
| I-001 | packages.json comments break json.loads | Bug | Medium | ✅ Fixed |
| I-002 | Re-enable button stays after restore | Bug | Low | ✅ Fixed |
| I-003 | SecurityException not caught on Path A | Bug | High | ✅ Fixed |
| I-004 | Scan runs on wrong era packages | Bug | Medium | ✅ Fixed |
| I-005 | Progress bar visible after action completes | Bug | Low | ✅ Fixed |
| I-006 | ADB not found gives cryptic error | Enhancement | Low | ✅ Fixed |
| I-007 | Core confirmation fires on deselect | Bug | Medium | ✅ Fixed |
| I-008 | Theme rebuild loses scan data | Bug | High | 🟡 Open |
| I-009 | Subcategory filter resets on re-scan | Enhancement | Low | 🟡 Open |
| I-010 | Battery parse fails on some ROMs | Bug | Low | 🟡 Open |
| I-011 | ADB daemon not started automatically | Enhancement | Medium | 🟡 Open |
| I-012 | Log strip fills too fast on bulk action | Enhancement | Low | 🟡 Open |
| I-013 | White theme log panel illegible | Bug | Medium | 🟡 Open |
| I-014 | Package size not shown | Enhancement | Low | 🔵 Planned v1.1 |
| I-015 | No multi-device support | Enhancement | Medium | 🔵 Planned v1.2 |

---

## 🐙 GitHub Setup

### Repository Details
| Field | Value |
|---|---|
| **Repo Name** | `DebloatKit` |
| **URL** | https://github.com/yashwanthramsomireddy/DebloatKit |
| **Visibility** | Public |
| **License** | MIT |
| **Description** | ADB debloater for Samsung Galaxy devices. Disable & uninstall bloatware safely without root. Works with One UI 5 through One UI 9. |

### Topics
```
android debloater samsung galaxy oneui adb bloatware python customtkinter windows toolkit teamexykings
```

### First Push
```bash
git init && git add .
git commit -m "feat: initial release v1.0"
git branch -M main
git remote add origin https://github.com/yashwanthramsomireddy/DebloatKit.git
git push -u origin main
git tag v1.0 && git push origin v1.0
```

### Release v1.0 Title
```
DebloatKit v1.0 — Initial Release
```

---

## 💰 Donation Channels

| Platform | Link / ID | Type | Status |
|---|---|---|---|
| Buy Me a Coffee | https://buymeacoffee.com/yashwanthramsomireddy | One-time / Monthly | ✅ Active |
| UPI / GPay | yashwanthramsomireddy@okaxis | One-time | ✅ Active |
| GitHub Sponsors | github.com/sponsors/yashwanthramsomireddy | Monthly | 🔵 Planned (after 100 ⭐) |
| PayPal | — | One-time | 🔵 Planned |

---

## 🗓️ Roadmap

### v1.1 — Upcoming
- [ ] Package size display via `dumpsys package`
- [ ] Export selected packages as `.sh` shell script
- [ ] App icon (`assets/icon.ico`)
- [ ] Windows system theme auto-detect

### v1.2 — Planned
- [ ] Wireless ADB support (Android 11+)
- [ ] Multiple device support — device selector dropdown
- [ ] Custom package list import — paste your own `.txt`
- [ ] 1-Click presets — Minimal Clean · Bixby Nuke · Privacy Mode · Deep Clean

### v2.0 — Future
- [ ] Windows installer with bundled ADB
- [ ] Package database auto-update from GitHub
- [ ] Per-device backup profiles

---

## ⚖️ Legal & Disclaimer

> DebloatKit is an independent open-source tool not affiliated with, endorsed by, or connected to Samsung Electronics Co., Ltd. Samsung and Galaxy are trademarks of Samsung Electronics. This tool uses Android's standard ADB debugging interface.
>
> Usage of "Samsung Galaxy" as a device descriptor is protected under Nominative Fair Use doctrine.
>
> **Credits:** XDA Developers community · @Vordx · Universal Android Debloater project

---

*DebloatKit v1.0 · TeamExyKings · Yashwanth Ram Somireddy · Chennai, India · MIT License · 2026-08-28*
