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
| **ADB** | subprocess — `--user 0` only, no root |
| **GitHub** | https://github.com/yashwanthramsomireddy/DebloatKit |
| **PayPal** | https://paypal.me/yash92duster |
| **Razorpay** | https://rzp.io/rzp/nsogoeD |
| **Started** | 2026-08-28 |
| **Status** | Active — v1.0 Released |

---

## 🛠️ Tech Stack

| Component | Technology | Version | Purpose | Notes |
|---|---|---|---|---|
| UI Framework | CustomTkinter | 6.0+ | Dark-theme desktop GUI | Built on tkinter |
| Language | Python | 3.11+ | Core application logic | Type hints, threading |
| ADB Bridge | subprocess | stdlib | Execute ADB shell commands | No root, --user 0 only |
| Package DB | JSON | custom | 110+ packages, risk ratings | Editable without code |
| Backup Engine | json (stdlib) | stdlib | Timestamped backup/restore | Stored in /backups/ |
| Threading | threading | stdlib | Non-blocking ADB operations | Daemon threads |
| Distribution | PyInstaller | 6.x | Single .exe for Windows | --onefile --windowed |
| Installer | Inno Setup | 6.x | Windows setup .exe | License agreement included |

---

## 🗂️ File Structure

```
DebloatKit/
├── DebloatKit.py              ← Main entry — 7 tabs, chunked rendering
├── core/
│   ├── adb_manager.py         ← ADB bridge — batch props, Path A/B/C, smart restore
│   ├── app_scanner.py         ← Single-call scan + DB cross-reference
│   └── debloater.py           ← Disable/uninstall/restore/backup engine
├── ui/
│   └── themes.py              ← Green/Blue/Purple/White color tokens
├── data/
│   └── packages.json          ← 110+ packages, risk, eras, paths
├── assets/
│   ├── icon.ico               ← App icon (16–256px)
│   ├── debloatkit_logo.png    ← Hex-D logo (256px)
│   └── installer_*.bmp        ← Inno Setup wizard bitmaps
├── backups/                   ← Auto-created timestamped JSON backups
├── LICENSE                    ← MIT License text
├── LICENSE.rtf                ← RTF license for Inno Setup
├── DebloatKit_Installer.iss   ← Inno Setup script
├── build.bat                  ← One-click exe builder
├── build_installer.bat        ← One-click installer builder
├── README.md
└── CHANGELOG.md
```

---

## 📱 Device Compatibility

| Era | Devices | Android | One UI | API |
|---|---|---|---|---|
| 1 — Legacy TouchWiz | Galaxy S5, S6, S7, S8, S9 | 5.0–8.1 | TouchWiz / Grace UX | 21–27 |
| 2 — Mid One UI | S10–S23, Note 10/20, Z Fold 1–5 | 9–13 | One UI 1.x–5.x | 28–33 |
| 3 — Modern One UI | S24–S26 Ultra, Z Fold 6–8 Ultra | 14–16 | One UI 6.x–9 | 34–36 |

---

## 📦 Package Database

| Category | Count | Risk Levels | Path | Notes |
|---|---|---|---|---|
| System Apps | 66 | SAFE / CAUTION / RECOMMENDED | A | Samsung, Google, carrier |
| Core Apps | 7 | CORE / LOCKED | A/B | Confirmation dialog required |
| User Apps | 13 | SAFE | A | Google Play preloads |
| 3rd Party | 19 | SAFE / RECOMMENDED | A | Facebook, Microsoft, OEM |
| Keep | 5 | KEEP | NONE | Non-removable, grayed out |
| **TOTAL** | **110** | | | 3 device eras (API 21–36) |

### Risk Levels

| Badge | Color | Behavior |
|---|---|---|
| `SAFE` | 🟢 Green | Checkbox enabled, pre-unchecked |
| `RECOMMENDED` | 🟢 Bright | Known tracker — highlighted |
| `CAUTION` | 🟡 Amber | May affect features — tooltip |
| `CORE` | 🔴 Red | Per-app confirm dialog required |
| `LOCKED` 🔒 | 🔴 Red | Path B — separate confirm |
| `KEEP` | ⬛ Gray | Non-selectable, tooltip why |

---

## 🔌 ADB Execution Paths

### Path A — Standard
```bash
pm disable-user --user 0 <package>     # freeze
pm uninstall -k --user 0 <package>     # remove (APK stays)
pm enable --user 0 <package>           # restore disabled
pm install-existing --user 0 <package> # restore uninstalled
```

### Path B — Security Locked (One UI 6+)
```bash
pm uninstall --user 0 <package>                    # break security lock
cmd package install-existing --user 0 <package>    # restore
```

### Path C — SoundAlive Fix
```bash
am force-stop com.sec.android.app.soundalive
pm clear com.sec.android.app.soundalive
```

---

## 🖥️ Tabs

| # | Tab | Contents |
|---|---|---|
| 1 | **System Apps** | Samsung/Google/carrier · all unchecked · era-filtered |
| 2 | **Core Apps** | ⛔ all unchecked · per-app confirmation |
| 3 | **User Apps** | Google Play preloads |
| 4 | **3rd Party** | Facebook, Microsoft, OEM-injected |
| 5 | **Log** | Timestamped ADB log · floating overlay · export |
| 6 | **Settings** | ADB path, backup, themes, Panic Restore |
| 7 | **About** | Logo, info, USB guide, PayPal, Razorpay, credits |

**Bottom bar:**
```
[ ⏸ Disable Selected ]  [ 🗑 Uninstall Selected ]  [ ↩ Re-enable Selected ]  [ 📋 Log ]
```

---

## 🛡️ Safety System

| Feature | Description |
|---|---|
| `--user 0` only | Never touches system partition |
| Auto silent backup | JSON snapshot before every action |
| Panic Restore | One click re-enables all from last backup |
| Core confirmation | ⛔ individual dialog per critical app |
| License agreement | MIT + disclaimer at install time |
| Factory reset | Ultimate fallback — restores all |

---

## 📱 USB Debugging Guide (in About tab)

**Enable before use:**
1. Settings → About Phone → Software Information
2. Tap Build Number 7 times
3. Developer Options → USB Debugging → ON
4. Connect USB → tap Allow on phone
5. Click Scan in DebloatKit

**Disable after use:**
1. Developer Options → USB Debugging → OFF
2. Developer Options → OFF (hides menu)
3. Disconnect cable

> ⚠️ Always disable USB Debugging after use for security.

---

## ✅ Feature Tracker

| ID | Feature | Status | Version | Priority |
|---|---|---|---|---|
| F-001 | 7-Tab Layout | ✅ Done | v1.0 | P1 |
| F-002 | Live Device Polling (4s) | ✅ Done | v1.0 | P1 |
| F-003 | Device Info Strip | ✅ Done | v1.0 | P1 |
| F-004 | USB Debugging Guide | ✅ Done | v1.0 | P1 |
| F-005 | Package DB (110+ packages) | ✅ Done | v1.0 | P1 |
| F-006 | Single-call Device Scan | ✅ Done | v1.0 | P1 |
| F-007 | Risk Badges (6 levels) | ✅ Done | v1.0 | P1 |
| F-008 | Subcategory Green Headers | ✅ Done | v1.0 | P1 |
| F-009 | Select All / Deselect All | ✅ Done | v1.0 | P1 |
| F-010 | Disable Selected (Path A) | ✅ Done | v1.0 | P1 |
| F-011 | Uninstall Selected (Path A) | ✅ Done | v1.0 | P1 |
| F-012 | Re-enable (Smart Restore) | ✅ Done | v1.0 | P1 |
| F-013 | Path B Security Bypass | ✅ Done | v1.0 | P1 |
| F-014 | SoundAlive Fix Hook | ✅ Done | v1.0 | P2 |
| F-015 | Core Apps Tab | ✅ Done | v1.0 | P1 |
| F-016 | Core Confirmation Dialog | ✅ Done | v1.0 | P1 |
| F-017 | Auto Silent Backup | ✅ Done | v1.0 | P1 |
| F-018 | Panic Restore | ✅ Done | v1.0 | P1 |
| F-019 | Battery Warning (<20%) | ✅ Done | v1.0 | P2 |
| F-020 | Root Detection Advisory | ✅ Done | v1.0 | P3 |
| F-021 | 4 Themes | ✅ Done | v1.0 | P2 |
| F-022 | Full Log Tab + Export | ✅ Done | v1.0 | P1 |
| F-023 | Floating Log Panel | ✅ Done | v1.0 | P2 |
| F-024 | Post-Action Summary Card | ✅ Done | v1.0 | P2 |
| F-025 | Search + Subcategory Filter | ✅ Done | v1.0 | P2 |
| F-026 | About Tab + Donate | ✅ Done | v1.0 | P2 |
| F-027 | USB Guide in About Tab | ✅ Done | v1.0 | P2 |
| F-028 | ADB Path + Test (proper) | ✅ Done | v1.0 | P2 |
| F-029 | Backup Folder Override | ✅ Done | v1.0 | P3 |
| F-030 | Starts Maximized | ✅ Done | v1.0 | P2 |
| F-031 | License Agreement Installer | ✅ Done | v1.0 | P1 |
| F-032 | Chunked Rendering (50/15ms) | ✅ Done | v1.0 | P1 |
| F-033 | Package Size Display | 🔵 Planned | v1.1 | P2 |
| F-034 | Export as Shell Script | 🔵 Planned | v1.1 | P2 |
| F-035 | Wireless ADB | 🔵 Planned | v1.2 | P2 |
| F-036 | Multi-device Support | 🔵 Planned | v1.2 | P3 |
| F-037 | Custom Package List Import | 🔵 Planned | v1.2 | P2 |
| F-038 | 1-Click Presets | 🔵 Planned | v1.2 | P1 |
| F-039 | DB Auto-Update from GitHub | 🔵 Planned | v2.0 | P3 |
| F-040 | Installer Upgrade (in-place) | 🔵 Planned | v2.0 | P2 |

---

## 🐛 Issue Tracker

| ID | Title | Type | Severity | Status |
|---|---|---|---|---|
| I-001 | packages.json comments break json.loads | Bug | Medium | ✅ Fixed |
| I-002 | USB guide fires on every poll cycle | Bug | High | ✅ Fixed |
| I-003 | USB guide grab_set blocks main window | Bug | High | ✅ Fixed |
| I-004 | SecurityException not caught on disable | Bug | High | ✅ Fixed |
| I-005 | Re-enable used wrong ADB command | Bug | High | ✅ Fixed |
| I-006 | Tab switching lag — 540 pkg freeze | Bug | Critical | ✅ Fixed |
| I-007 | Scrollbar frozen during render | Bug | High | ✅ Fixed |
| I-008 | Scan took 30+ seconds (4 ADB calls) | Bug | High | ✅ Fixed |
| I-009 | Settings page overlaps package list | Bug | High | ✅ Fixed |
| I-010 | ADB Test says OK without device | Bug | Medium | ✅ Fixed |
| I-011 | Error 740 on exe launch | Bug | Critical | ✅ Fixed |
| I-012 | ISS ifdef FileExists() parse error | Bug | High | ✅ Fixed |
| I-013 | Compact toggle did nothing | Bug | High | ✅ Fixed |
| I-014 | Theme rebuild caused app crash | Bug | Medium | ✅ Fixed |
| I-015 | Disconnect didn't clear tab state | Bug | Medium | ✅ Fixed |
| I-016 | No license agreement in installer | Enhancement | Medium | ✅ Fixed |
| I-017 | About page phantom empty widget | Bug | Low | ✅ Fixed |
| I-018 | installer/ folder still in zip | Bug | Low | ✅ Fixed |
| I-019 | Subcategory filter resets on scan | Enhancement | Low | 🟡 Open |
| I-020 | Battery parse fails on some ROMs | Bug | Low | 🟡 Open |
| I-021 | No multi-device support | Enhancement | Medium | 🔵 Planned v1.2 |

---

## 🐙 GitHub

| Field | Value |
|---|---|
| **Repo** | `DebloatKit` |
| **URL** | https://github.com/yashwanthramsomireddy/DebloatKit |
| **Description** | ADB debloater for Samsung Galaxy devices. Disable & uninstall bloatware safely without root. Works with One UI 5 through One UI 9. |
| **License** | MIT |
| **Topics** | `android` `debloater` `samsung` `galaxy` `oneui` `adb` `bloatware` `python` `customtkinter` `windows` `toolkit` `teamexykings` |

```bash
git init && git add .
git commit -m "feat: initial release v1.0"
git branch -M main
git remote add origin https://github.com/yashwanthramsomireddy/DebloatKit.git
git push -u origin main && git tag v1.0 && git push origin v1.0
```

---

## 💰 Donations

| Platform | Link | Currency | Status |
|---|---|---|---|
| **PayPal** | https://paypal.me/yash92duster | USD | ✅ Active |
| **Razorpay** | https://rzp.io/rzp/nsogoeD | INR | ✅ Active |
| **GitHub Sponsors** | github.com/sponsors/yashwanthramsomireddy | USD | 🔵 Planned (after 100 ⭐) |

---

## 🗓️ Roadmap

### v1.1
- [ ] Package size display via `dumpsys package`
- [ ] Export selected as `.sh` shell script

### v1.2
- [ ] Wireless ADB (Android 11+)
- [ ] Multi-device selector dropdown
- [ ] Custom `.txt` package list import
- [ ] 1-Click presets — Minimal Clean · Bixby Nuke · Privacy Mode

### v2.0
- [ ] Windows installer upgrade (in-place)
- [ ] DB auto-update from GitHub
- [ ] Per-device backup profiles

---

## ⚖️ Legal

> DebloatKit is an independent open-source tool not affiliated with, endorsed by, or connected to Samsung Electronics Co., Ltd. Samsung and Galaxy are trademarks of Samsung Electronics. This tool uses Android's standard ADB debugging interface.
>
> **Credits:** XDA Community (package safety data) · Google Research (AOSP ADB documentation)

---

*DebloatKit v1.0 · TeamExyKings · Yashwanth Ram Somireddy · Chennai, India · MIT License · 2026-08-29*
