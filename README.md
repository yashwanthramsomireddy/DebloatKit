<div align="center">

# ⬡ DebloatKit
### Works with Samsung Galaxy Devices
**Safely disable & uninstall bloatware via ADB — no root required**

![Version](https://img.shields.io/badge/version-1.0-00e676?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-00e676?style=flat-square)
![Python](https://img.shields.io/badge/python-3.11%2B-00e676?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-00e676?style=flat-square)
![ADB](https://img.shields.io/badge/ADB-no%20root-00e676?style=flat-square)

**By [Yashwanth Ram Somireddy](https://github.com/yashwanthramsomireddy) · TeamExyKings · Chennai, India**

</div>

---

## What is DebloatKit?

DebloatKit is a free, open-source Windows desktop app that lets you safely remove pre-installed bloatware from Samsung Galaxy devices using Android's standard ADB debugging interface — no root required, no APKs deleted, everything reversible.

It works with Galaxy devices from legacy TouchWiz (S5, S6, S7) all the way through modern One UI 9 (S26 Ultra, Z Fold 8 Ultra).

---

## Screenshots

> *Connect your device → Scan → Select → Debloat*

---

## Features

- **110+ curated packages** — Samsung, Google, Facebook, Microsoft, carrier bloat
- **4 categorized tabs** — System Apps, Core Apps, User Apps, 3rd Party
- **Risk badges** — Safe / Recommended / Caution / Core / Locked / Keep
- **Disable or Uninstall** — both fully reversible via `--user 0`
- **Per-row Re-enable** — restore any app instantly while device is connected
- **Core Apps confirmation** — ⛔ individual warning dialog before touching system-critical apps
- **Auto silent backup** — JSON snapshot saved before every action
- **Panic Restore** — one click re-enables everything from last backup
- **Dry Run mode** — preview all changes with zero actual impact
- **Live device detection** — polls every 3 seconds, shows model, Android version, One UI version, battery
- **USB Debugging guide** — built-in step-by-step walkthrough
- **SoundAlive fix** — post-debloat audio engine flush for diagmonagent removal
- **4 themes** — Green (default), Blue, Purple, White
- **Full ADB log** — timestamped, color-coded, exportable

---

## Device Compatibility

| Era | Devices | Android | One UI |
|-----|---------|---------|--------|
| Legacy TouchWiz | Galaxy S5, S6, S7, S8, S9 | 5.0 – 8.1 | TouchWiz / Grace UX |
| Mid One UI | Galaxy S10 – S23, Note 10/20, Z Fold 1–5 | 9 – 13 | One UI 1.x – 5.x |
| Modern One UI | Galaxy S24 – S26 Ultra, Z Fold 6–8 Ultra | 14 – 16 | One UI 6.x – 9 |

---

## Prerequisites

### 1. Python 3.11+
Download from https://python.org

### 2. ADB Platform Tools
Download from Google:
```
https://dl.google.com/android/repository/platform-tools-latest-windows.zip
```
Extract the zip and either:
- Add the extracted folder to your Windows PATH, **or**
- Set the `adb.exe` path in DebloatKit → Settings

### 3. USB Debugging on your Galaxy device
See the [Enable USB Debugging](#enable-usb-debugging) section below.

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/yashwanthramsomireddy/DebloatKit.git
cd DebloatKit

# 2. Install dependencies
pip install customtkinter

# 3. Run
python DebloatKit.py
```

---

## Build as .exe (optional)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name DebloatKit --icon assets/icon.ico DebloatKit.py
```

The `.exe` will be in the `dist/` folder.

---

## Enable USB Debugging

1. On your Galaxy device, open **Settings**
2. Go to **About Phone → Software Information**
3. Tap **Build Number** 7 times rapidly → "Developer mode enabled"
4. Go back to **Settings → Developer Options**
5. Enable **USB Debugging**
6. Connect your device to PC via USB
7. On your phone, tap **Allow** when prompted
8. DebloatKit detects your device automatically

---

## How It Works

All debloat operations use Android's standard package manager with `--user 0` flag.
**Nothing is permanently deleted.** The APK stays on the system partition.

```bash
# Disable (freeze app — reversible)
adb shell pm disable-user --user 0 <package>

# Uninstall for current user only — APK intact (reversible)
adb shell pm uninstall -k --user 0 <package>

# Restore / Re-enable
adb shell pm install-existing --user 0 <package>
adb shell pm enable --user 0 <package>
```

Security-locked packages on One UI 6+ (marked 🔒) use an alternate path:
```bash
adb shell pm uninstall --user 0 <package>
adb shell cmd package install-existing --user 0 <package>
```

---

## Safety Model

| Feature | Description |
|---------|-------------|
| `--user 0` only | Never touches system partition |
| Auto backup | JSON snapshot saved before every debloat action |
| Panic Restore | One click re-enables all from last backup |
| Per-row re-enable | Restore any individual app instantly |
| Dry Run | Preview mode — zero actual changes |
| Core confirmation | ⛔ dialog required for system-critical packages |
| Factory reset fallback | Full reinstall of all packages if needed |

---

## Project Structure

```
DebloatKit/
├── DebloatKit.py          ← Main app entry point
├── core/
│   ├── adb_manager.py     ← ADB bridge, device polling, execution paths
│   ├── app_scanner.py     ← Live device scan + package DB lookup
│   └── debloater.py       ← Disable/uninstall/restore/backup engine
├── ui/
│   └── themes.py          ← Green/Blue/Purple/White color tokens
├── data/
│   └── packages.json      ← 110+ package database with risk ratings
├── backups/               ← Auto-created, stores timestamped JSON backups
└── README.md
```

---

## Package Database

The `data/packages.json` contains 110+ packages across:

| Category | Count | Examples |
|----------|-------|---------|
| System (Samsung) | 66 | Bixby, AR Zone, Gaming Hub, Pay, diagnostics |
| Core (confirmation required) | 7 | Knox, Secure Folder, Emergency Mode, SwiftKey |
| User (Google) | 13 | YouTube, Maps, Photos, Meet |
| 3rd Party | 19 | Facebook suite, Microsoft Office, LinkedIn, Netflix |
| Keep (non-removable) | 5 | Google Play Services, Files UI, Phone dialer |

Risk ratings sourced from XDA Developers community research and the Universal Android Debloater project.

---

## Contributing

Pull requests welcome. To add packages:

1. Edit `data/packages.json`
2. Follow the existing schema — include `pkg`, `name`, `category`, `subcategory`, `risk`, `path`, `description`, `eras`
3. Test on a real device before submitting

---

## Support Development

DebloatKit is free and always will be. If it saved you time:

- ☕ [Buy Me a Coffee](https://buymeacoffee.com/yashwanthramsomireddy)
- UPI: `yashwanthramsomireddy@okaxis`
- ⭐ Star this repo

---

## Disclaimer

DebloatKit is an independent open-source tool not affiliated with, endorsed by, or connected to Samsung Electronics Co., Ltd. Samsung and Galaxy are trademarks of Samsung Electronics. This tool uses Android's standard ADB debugging interface.

Credits: XDA Developers community · @Vordx · Universal Android Debloater project

---

## License

MIT License — Free to use, modify, and distribute.
See [LICENSE](LICENSE) for full terms.
