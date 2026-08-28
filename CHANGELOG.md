# Changelog — DebloatKit

All notable changes to DebloatKit will be documented here.
Format: [Semantic Versioning](https://semver.org) — `MAJOR.MINOR.PATCH`

---

## [1.0] — 2026-08-28

> **Initial public release**
> Works with Samsung Galaxy devices — Android 5.0 (TouchWiz) through Android 16 (One UI 9)

### Added

#### Core Engine
- ADB device detection via `adb devices` — polls every 3 seconds
- Automatic device era detection from API level (Legacy / Mid One UI / Modern One UI)
- Device info display — model, brand, Android version, One UI version, battery level
- Battery warning when level below 20% before debloating
- Root detection with advisory message

#### Package Database
- 110+ curated packages with risk ratings across 3 device eras
- Risk tiers: SAFE · RECOMMENDED · CAUTION · CORE · LOCKED · KEEP
- Categories: System Apps · Core Apps · User Apps · 3rd Party · Keep
- Sources: personal debloat list, XDA Developers community research, Universal Android Debloater project

#### Debloat Operations
- **Path A** — `pm disable-user --user 0` for standard packages
- **Path A** — `pm uninstall -k --user 0` for user-profile removal (keeps APK)
- **Path B** — `pm uninstall --user 0` + `cmd package install-existing` for security-locked packages (One UI 6+)
- **Path C** — SoundAlive audio engine flush for post-diagmonagent removal
- Auto SecurityException detection with Path B fallback suggestion

#### Safety Features
- Auto silent backup before every debloat/uninstall action → timestamped JSON in `backups/`
- Panic Restore — re-enable all packages from most recent backup in one click
- Per-row Re-enable button — restore any individual app instantly
- Dry Run mode — full preview with zero actual device changes
- Core Apps confirmation dialog — individual ⛔ warning per system-critical package

#### User Interface
- 7-tab layout: System Apps · Core Apps · User Apps · 3rd Party · Logs · Settings · About
- PurgeKit design language — `#0a0a0a` pitch black, `#00e676` green accent
- Compact / Spacious mode toggle in topbar
- Risk badges with color coding per row
- Package state indicators — Enabled / Disabled / Uninstalled (live updates)
- Subcategory grouping with collapsible headers
- Per-tab search and subcategory filter
- Select All / Deselect All per tab
- Disable Selected / Uninstall Selected action buttons per tab
- Post-action summary card — succeeded / failed / backup path
- USB Debugging step-by-step guide (auto-shown on Unauthorized device)
- 4 themes — Green (default), Blue, Purple, White
- Persistent log strip at bottom of every tab
- Full log tab with export to .txt
- SoundAlive fix prompt after diagmonagent removal
- About tab with donate section (Buy Me a Coffee, UPI)
- Legal disclaimer on About tab

#### Settings
- ADB executable path override with Browse + Test ADB
- Backup folder path override
- Open Backup Folder shortcut
- Theme switcher
- Panic Restore shortcut

---

## Planned — Future Versions

### [1.1] — Planned
- [ ] Package size display via `dumpsys package`
- [ ] Search across all tabs simultaneously
- [ ] Export selected package list as `.txt` / shell script
- [ ] Dark/Light auto-detect from Windows system theme
- [ ] App icon (`assets/icon.ico`)

### [1.2] — Planned
- [ ] Wireless ADB support (Android 11+ — no USB needed)
- [ ] Multiple device support — switch between connected devices
- [ ] Custom package list import — paste your own `.txt` list
- [ ] One-click presets — Minimal Clean · Bixby Nuke · Privacy Mode · Deep Clean

### [2.0] — Planned
- [ ] Galaxy Store package integration for wearables awareness
- [ ] Per-device backup profiles
- [ ] Auto-update for package database from GitHub
- [ ] Installer / setup `.exe`
