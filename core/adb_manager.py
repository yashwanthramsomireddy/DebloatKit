"""
DebloatKit v1.0 — ADB Manager
Handles device detection, connection polling, and device info retrieval.
Author: Yashwanth Ram Somireddy | TeamExyKings | MIT License
"""

import subprocess
import threading
import time
from typing import Optional, Callable


class DeviceInfo:
    def __init__(self):
        self.serial: str = ""
        self.model: str = ""
        self.brand: str = ""
        self.android_version: str = ""
        self.oneui_version: str = ""
        self.api_level: str = ""
        self.sdk_version: str = ""
        self.battery_level: int = 100
        self.is_rooted: bool = False
        self.era: int = 0  # 1=Legacy, 2=Mid OneUI, 3=Modern

    def get_era_label(self) -> str:
        era_map = {
            1: "Legacy TouchWiz (S5–S9)",
            2: "One UI 1.x–5.x (S10–S23)",
            3: "Modern One UI 6.x–9 (S24–S26 Ultra)"
        }
        return era_map.get(self.era, "Unknown Era")


class ADBManager:
    def __init__(self, adb_path: str = "adb", log_callback: Optional[Callable] = None):
        self.adb_path = adb_path
        self.log_callback = log_callback
        self.device_info: Optional[DeviceInfo] = None
        self._polling = False
        self._poll_thread: Optional[threading.Thread] = None
        self._status_callback: Optional[Callable] = None
        self._connected_callback: Optional[Callable] = None
        self._disconnected_callback: Optional[Callable] = None
        self._last_status = "no_device"

    def log(self, message: str, level: str = "info"):
        if self.log_callback:
            self.log_callback(message, level)

    def run(self, args: list, timeout: int = 10) -> tuple[bool, str]:
        """Run an adb command. Returns (success, output)."""
        try:
            cmd = [self.adb_path] + args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            output = result.stdout.strip()
            error = result.stderr.strip()
            if result.returncode == 0:
                return True, output
            else:
                return False, error or output
        except subprocess.TimeoutExpired:
            return False, "ADB command timed out"
        except FileNotFoundError:
            return False, f"ADB not found at '{self.adb_path}'. Please install ADB and set path in Settings."
        except Exception as e:
            return False, str(e)

    def run_shell(self, cmd: str, timeout: int = 15) -> tuple[bool, str]:
        """Run adb shell command."""
        return self.run(["-s", self.device_info.serial, "shell", cmd], timeout=timeout)

    def get_connected_devices(self) -> list[dict]:
        """Returns list of connected devices with serial and status."""
        ok, output = self.run(["devices"])
        if not ok:
            return []
        devices = []
        for line in output.splitlines()[1:]:
            if "\t" in line:
                serial, status = line.split("\t", 1)
                devices.append({"serial": serial.strip(), "status": status.strip()})
        return devices

    def get_device_status(self) -> str:
        """Returns: no_device | unauthorized | ready"""
        devices = self.get_connected_devices()
        if not devices:
            return "no_device"
        for d in devices:
            if d["status"] == "unauthorized":
                return "unauthorized"
            if d["status"] == "device":
                return "ready"
        return "no_device"

    def get_prop(self, prop: str) -> str:
        ok, val = self.run(["-s", self.device_info.serial, "shell", f"getprop {prop}"])
        return val.strip() if ok else ""

    def detect_device(self) -> Optional[DeviceInfo]:
        """Full device info detection."""
        devices = self.get_connected_devices()
        ready = [d for d in devices if d["status"] == "device"]
        if not ready:
            return None

        info = DeviceInfo()
        info.serial = ready[0]["serial"]
        self.device_info = info

        # Get device properties
        info.model = self.get_prop("ro.product.model") or "Unknown Model"
        info.brand = self.get_prop("ro.product.brand") or "Samsung"
        info.android_version = self.get_prop("ro.build.version.release") or "?"
        info.api_level = self.get_prop("ro.build.version.sdk") or "0"
        info.oneui_version = self.get_prop("ro.build.version.oneui") or ""

        # Determine era from API level
        try:
            api = int(info.api_level)
            if api <= 26:
                info.era = 1
            elif api <= 33:
                info.era = 2
            else:
                info.era = 3
        except ValueError:
            info.era = 2

        # Battery level
        ok, bat = self.run_shell("dumpsys battery | grep level")
        if ok and "level:" in bat:
            try:
                info.battery_level = int(bat.split("level:")[-1].strip())
            except Exception:
                info.battery_level = 100

        # Root check
        ok, whoami = self.run_shell("whoami")
        info.is_rooted = ok and "root" in whoami.lower()

        self.log(f"Device detected: {info.brand} {info.model} | Android {info.android_version} | API {info.api_level} | Era {info.era}", "success")
        if info.battery_level < 20:
            self.log(f"⚠ Battery at {info.battery_level}% — charge before debloating to avoid interruption.", "warning")
        if info.is_rooted:
            self.log("⚠ Root detected — debloat operations still use --user 0 (safe method).", "warning")

        return info

    def start_polling(self, on_status_change: Callable, on_connected: Callable, on_disconnected: Callable, interval: int = 3):
        """Poll for device connection changes every `interval` seconds."""
        self._status_callback = on_status_change
        self._connected_callback = on_connected
        self._disconnected_callback = on_disconnected
        self._polling = True
        self._poll_thread = threading.Thread(target=self._poll_loop, args=(interval,), daemon=True)
        self._poll_thread.start()

    def stop_polling(self):
        self._polling = False

    def _poll_loop(self, interval: int):
        while self._polling:
            status = self.get_device_status()
            if status != self._last_status:
                self._last_status = status
                if self._status_callback:
                    self._status_callback(status)
                if status == "ready" and self._connected_callback:
                    info = self.detect_device()
                    if info:
                        self._connected_callback(info)
                elif status == "no_device" and self._disconnected_callback:
                    self.device_info = None
                    self._disconnected_callback()
            time.sleep(interval)

    def list_packages(self, flags: str = "") -> list[str]:
        """List packages with optional flags (-s, -3, -d, -e)."""
        ok, output = self.run_shell(f"pm list packages {flags}")
        if not ok:
            return []
        pkgs = []
        for line in output.splitlines():
            if line.startswith("package:"):
                pkgs.append(line.replace("package:", "").strip())
        return pkgs

    def get_package_state(self, pkg: str) -> str:
        """Returns 'enabled', 'disabled', or 'uninstalled'."""
        ok, out = self.run_shell(f"pm list packages -s -d | grep '{pkg}'")
        if ok and pkg in out:
            return "disabled"
        ok2, out2 = self.run_shell(f"pm list packages | grep '{pkg}'")
        if ok2 and pkg in out2:
            return "enabled"
        return "uninstalled"

    def disable_package(self, pkg: str) -> tuple[bool, str]:
        """Path A: pm disable-user --user 0"""
        self.log(f"[PATH A] Disabling {pkg}...", "info")
        ok, out = self.run_shell(f"pm disable-user --user 0 {pkg}")
        if ok and ("disabled" in out.lower() or out == ""):
            self.log(f"✓ Disabled: {pkg}", "success")
            return True, "disabled"
        # Check for SecurityException → suggest Path B
        if "SecurityException" in out or "Exception" in out:
            self.log(f"⚠ SecurityException for {pkg} — try Uninstall instead (Path B)", "warning")
            return False, "security_exception"
        self.log(f"✗ Failed to disable {pkg}: {out}", "error")
        return False, out

    def enable_package(self, pkg: str) -> tuple[bool, str]:
        """Re-enable a disabled package."""
        self.log(f"Re-enabling {pkg}...", "info")
        ok, out = self.run_shell(f"pm enable --user 0 {pkg}")
        if ok:
            self.log(f"✓ Re-enabled: {pkg}", "success")
            return True, "enabled"
        self.log(f"✗ Failed to re-enable {pkg}: {out}", "error")
        return False, out

    def uninstall_package(self, pkg: str) -> tuple[bool, str]:
        """Path A: pm uninstall -k --user 0 (keeps data, keeps APK on system)"""
        self.log(f"[PATH A] Uninstalling {pkg} for user 0...", "info")
        ok, out = self.run_shell(f"pm uninstall -k --user 0 {pkg}")
        if ok and "success" in out.lower():
            self.log(f"✓ Uninstalled (reversible): {pkg}", "success")
            return True, "uninstalled"
        self.log(f"✗ Failed to uninstall {pkg}: {out}", "error")
        return False, out

    def uninstall_package_path_b(self, pkg: str) -> tuple[bool, str]:
        """Path B: pm uninstall --user 0 (for security-locked packages)"""
        self.log(f"[PATH B] Force-uninstalling security-locked {pkg}...", "warning")
        ok, out = self.run_shell(f"pm uninstall --user 0 {pkg}")
        if ok and "success" in out.lower():
            self.log(f"✓ Path B uninstalled: {pkg}", "success")
            return True, "uninstalled"
        self.log(f"✗ Path B failed for {pkg}: {out}", "error")
        return False, out

    def reinstall_package(self, pkg: str) -> tuple[bool, str]:
        """Restore/reinstall a previously uninstalled --user 0 package."""
        self.log(f"Restoring {pkg}...", "info")
        ok, out = self.run_shell(f"cmd package install-existing --user 0 {pkg}")
        if ok and ("installed" in out.lower() or out == ""):
            self.log(f"✓ Restored: {pkg}", "success")
            return True, "enabled"
        # Fallback
        ok2, out2 = self.run_shell(f"pm install-existing {pkg}")
        if ok2:
            self.log(f"✓ Restored (fallback): {pkg}", "success")
            return True, "enabled"
        self.log(f"✗ Failed to restore {pkg}: {out}", "error")
        return False, out

    def soundalive_fix(self) -> bool:
        """Path C: SoundAlive audio engine flush."""
        self.log("Running SoundAlive fix...", "info")
        self.run_shell("am force-stop com.sec.android.app.soundalive")
        self.run_shell("pm clear com.sec.android.app.soundalive")
        self.log("SoundAlive flushed. Reboot recommended.", "warning")
        return True

    def is_adb_available(self) -> bool:
        ok, _ = self.run(["version"])
        return ok
