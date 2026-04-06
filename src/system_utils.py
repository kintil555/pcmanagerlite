"""
system_utils.py - System information and cleanup utilities
"""

import os
import sys
import shutil
import tempfile
import subprocess
import winreg
import psutil
import ctypes
from pathlib import Path
from datetime import datetime


def is_admin() -> bool:
    """Check if running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def get_system_info() -> dict:
    """Gather comprehensive system information."""
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('C:\\')
    cpu_freq = psutil.cpu_freq()

    return {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "cpu_count": psutil.cpu_count(logical=True),
        "cpu_freq": cpu_freq.current if cpu_freq else 0,
        "mem_total": mem.total,
        "mem_used": mem.used,
        "mem_percent": mem.percent,
        "mem_available": mem.available,
        "disk_total": disk.total,
        "disk_used": disk.used,
        "disk_percent": disk.percent,
        "disk_free": disk.free,
    }


def format_bytes(size_bytes: int) -> str:
    """Format bytes into human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024**2):.1f} MB"
    else:
        return f"{size_bytes / (1024**3):.2f} GB"


# ── BOOST ────────────────────────────────────────────────────────────────────

def get_temp_size() -> int:
    """Calculate total size of temp files."""
    total = 0
    temp_dirs = [
        tempfile.gettempdir(),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
        os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Temp'),
    ]
    for d in temp_dirs:
        if os.path.isdir(d):
            for dirpath, _, filenames in os.walk(d):
                for f in filenames:
                    try:
                        fp = os.path.join(dirpath, f)
                        total += os.path.getsize(fp)
                    except (OSError, PermissionError):
                        pass
    return total


def boost_pc() -> dict:
    """
    Perform quick boost:
    - Empty temp folders
    - Trim working sets (Windows API)
    """
    freed = 0
    errors = []

    # Clear temp directories
    temp_dirs = [
        tempfile.gettempdir(),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
        os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Temp'),
    ]

    for d in temp_dirs:
        if not os.path.isdir(d):
            continue
        for item in os.listdir(d):
            item_path = os.path.join(d, item)
            try:
                size = 0
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    size = os.path.getsize(item_path)
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    size = sum(
                        os.path.getsize(os.path.join(dp, f))
                        for dp, _, fs in os.walk(item_path)
                        for f in fs
                        if not os.path.islink(os.path.join(dp, f))
                    )
                    shutil.rmtree(item_path, ignore_errors=True)
                freed += size
            except (PermissionError, OSError):
                pass

    # Trim working sets (requires admin on some systems)
    try:
        if is_admin():
            for proc in psutil.process_iter(['pid']):
                try:
                    handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, proc.info['pid'])
                    if handle:
                        ctypes.windll.psapi.EmptyWorkingSet(handle)
                        ctypes.windll.kernel32.CloseHandle(handle)
                except Exception:
                    pass
    except Exception as e:
        errors.append(str(e))

    return {"freed": freed, "errors": errors}


# ── DEEP CLEANUP ─────────────────────────────────────────────────────────────

CLEANUP_TARGETS = {
    "Windows Temp": [
        os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Temp'),
    ],
    "User Temp": [
        tempfile.gettempdir(),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
    ],
    "Prefetch": [
        os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Prefetch'),
    ],
    "Thumbnail Cache": [
        os.path.join(os.environ.get('LOCALAPPDATA', ''), r'Microsoft\Windows\Explorer'),
    ],
    "Recent Files": [
        os.path.join(os.environ.get('APPDATA', ''), r'Microsoft\Windows\Recent'),
    ],
    "Recycle Bin": [],   # handled separately
    "DNS Cache": [],     # handled via cmd
    "Browser Cache": [
        os.path.join(os.environ.get('LOCALAPPDATA', ''),
                     r'Google\Chrome\User Data\Default\Cache'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''),
                     r'Microsoft\Edge\User Data\Default\Cache'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''),
                     r'BraveSoftware\Brave-Browser\User Data\Default\Cache'),
    ],
}


def scan_cleanup() -> dict:
    """Scan what can be cleaned, return sizes per category."""
    results = {}
    for category, paths in CLEANUP_TARGETS.items():
        total = 0
        if category == "Recycle Bin":
            try:
                import ctypes
                size_info = ctypes.c_int64(0)
                item_count = ctypes.c_int64(0)
                ctypes.windll.shell32.SHQueryRecycleBinW(None,
                    ctypes.byref(size_info), ctypes.byref(item_count))
                total = size_info.value
            except Exception:
                total = 0
        elif category == "DNS Cache":
            total = 0  # DNS cache doesn't have a measurable size
        else:
            for p in paths:
                if os.path.isdir(p):
                    for dp, _, files in os.walk(p):
                        for f in files:
                            try:
                                total += os.path.getsize(os.path.join(dp, f))
                            except (OSError, PermissionError):
                                pass
        results[category] = total
    return results


def deep_cleanup(categories: list) -> dict:
    """Perform deep cleanup for selected categories."""
    freed = 0
    cleaned = []
    errors = []

    for category in categories:
        cat_freed = 0
        if category not in CLEANUP_TARGETS:
            continue

        if category == "Recycle Bin":
            try:
                ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x0007)
                cat_freed = 1  # mark as done
                cleaned.append(category)
            except Exception as e:
                errors.append(f"Recycle Bin: {e}")
            continue

        if category == "DNS Cache":
            try:
                subprocess.run("ipconfig /flushdns", shell=True,
                               capture_output=True, timeout=10)
                cleaned.append(category)
            except Exception as e:
                errors.append(f"DNS Cache: {e}")
            continue

        paths = CLEANUP_TARGETS[category]
        for path in paths:
            if not os.path.isdir(path):
                continue
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        size = os.path.getsize(item_path)
                        os.remove(item_path)
                        cat_freed += size
                    elif os.path.isdir(item_path):
                        size = sum(
                            os.path.getsize(os.path.join(dp, f))
                            for dp, _, fs in os.walk(item_path)
                            for f in fs
                        )
                        shutil.rmtree(item_path, ignore_errors=True)
                        cat_freed += size
                except (PermissionError, OSError):
                    pass

        if cat_freed > 0:
            cleaned.append(category)
        freed += cat_freed

    return {"freed": freed, "cleaned": cleaned, "errors": errors}


# ── STARTUP ITEMS ─────────────────────────────────────────────────────────────

STARTUP_REG_KEYS = [
    (winreg.HKEY_CURRENT_USER,
     r"Software\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE,
     r"Software\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE,
     r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
]

STARTUP_FOLDER_USER = os.path.join(
    os.environ.get('APPDATA', ''),
    r"Microsoft\Windows\Start Menu\Programs\Startup"
)
STARTUP_FOLDER_ALL = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp"


def get_startup_items() -> list:
    """Get all startup items from registry and startup folders."""
    items = []

    # Registry
    for hive, key_path in STARTUP_REG_KEYS:
        hive_name = "HKCU" if hive == winreg.HKEY_CURRENT_USER else "HKLM"
        try:
            key = winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    items.append({
                        "name": name,
                        "path": value,
                        "type": "registry",
                        "source": f"{hive_name}\\{key_path}",
                        "enabled": True,
                    })
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except (OSError, PermissionError):
            pass

    # Startup folders
    for folder in [STARTUP_FOLDER_USER, STARTUP_FOLDER_ALL]:
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                if f.endswith('.lnk') or f.endswith('.exe'):
                    items.append({
                        "name": f.replace('.lnk', '').replace('.exe', ''),
                        "path": os.path.join(folder, f),
                        "type": "folder",
                        "source": folder,
                        "enabled": True,
                    })

    return items


def disable_startup_item(item: dict) -> bool:
    """Disable a startup item (move to disabled registry key or rename)."""
    try:
        if item["type"] == "registry":
            hive = winreg.HKEY_CURRENT_USER if "HKCU" in item["source"] else winreg.HKEY_LOCAL_MACHINE
            src_path = item["source"].split("\\", 1)[1]
            dst_path = src_path.replace("\\Run", "\\Run\\Disabled")

            # Read value
            src_key = winreg.OpenKey(hive, src_path, 0, winreg.KEY_READ)
            value = winreg.QueryValueEx(src_key, item["name"])[0]
            winreg.CloseKey(src_key)

            # Write to disabled key
            dst_key = winreg.CreateKey(hive, dst_path)
            winreg.SetValueEx(dst_key, item["name"], 0, winreg.REG_SZ, value)
            winreg.CloseKey(dst_key)

            # Delete from enabled key
            del_key = winreg.OpenKey(hive, src_path, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(del_key, item["name"])
            winreg.CloseKey(del_key)
            return True
    except Exception:
        pass
    return False


def enable_startup_item(item: dict) -> bool:
    """Re-enable a disabled startup item."""
    try:
        if item["type"] == "registry":
            hive = winreg.HKEY_CURRENT_USER if "HKCU" in item["source"] else winreg.HKEY_LOCAL_MACHINE
            src_path = item["source"].split("\\", 1)[1]
            disabled_path = src_path.replace("\\Run", "\\Run\\Disabled")

            disabled_key = winreg.OpenKey(hive, disabled_path, 0, winreg.KEY_READ)
            value = winreg.QueryValueEx(disabled_key, item["name"])[0]
            winreg.CloseKey(disabled_key)

            run_key = winreg.OpenKey(hive, src_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(run_key, item["name"], 0, winreg.REG_SZ, value)
            winreg.CloseKey(run_key)

            del_key = winreg.OpenKey(hive, disabled_path, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(del_key, item["name"])
            winreg.CloseKey(del_key)
            return True
    except Exception:
        pass
    return False


# ── PROCESS MANAGEMENT ────────────────────────────────────────────────────────

def get_processes(sort_by: str = "memory") -> list:
    """Get list of running processes sorted by CPU or memory."""
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'status', 'memory_info', 'cpu_percent']):
        try:
            info = p.info
            mem = info['memory_info'].rss if info['memory_info'] else 0
            procs.append({
                "pid": info['pid'],
                "name": info['name'],
                "status": info['status'],
                "memory": mem,
                "cpu": info['cpu_percent'] or 0.0,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if sort_by == "memory":
        procs.sort(key=lambda x: x['memory'], reverse=True)
    elif sort_by == "cpu":
        procs.sort(key=lambda x: x['cpu'], reverse=True)
    elif sort_by == "name":
        procs.sort(key=lambda x: x['name'].lower())

    return procs


def kill_process(pid: int) -> bool:
    """Terminate a process by PID."""
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        proc.wait(timeout=3)
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
        try:
            psutil.Process(pid).kill()
            return True
        except Exception:
            return False


# ── HEALTH CHECK ──────────────────────────────────────────────────────────────

def run_health_check() -> list:
    """Run comprehensive health check and return list of findings."""
    findings = []

    # 1. RAM usage
    mem = psutil.virtual_memory()
    if mem.percent > 85:
        findings.append({
            "category": "Memory",
            "status": "warning",
            "message": f"High RAM usage: {mem.percent:.0f}% used",
            "action": "Consider closing unused applications",
        })
    else:
        findings.append({
            "category": "Memory",
            "status": "ok",
            "message": f"RAM usage normal: {mem.percent:.0f}%",
            "action": None,
        })

    # 2. Disk space
    try:
        disk = psutil.disk_usage('C:\\')
        if disk.percent > 90:
            findings.append({
                "category": "Disk (C:)",
                "status": "critical",
                "message": f"Disk almost full: {disk.percent:.0f}% used",
                "action": "Run Deep Cleanup to free space",
            })
        elif disk.percent > 75:
            findings.append({
                "category": "Disk (C:)",
                "status": "warning",
                "message": f"Disk usage: {disk.percent:.0f}%",
                "action": "Consider cleanup soon",
            })
        else:
            findings.append({
                "category": "Disk (C:)",
                "status": "ok",
                "message": f"Disk space healthy: {disk.percent:.0f}% used",
                "action": None,
            })
    except Exception:
        pass

    # 3. Temp files
    temp_size = get_temp_size()
    if temp_size > 500 * 1024 * 1024:  # 500 MB
        findings.append({
            "category": "Temp Files",
            "status": "warning",
            "message": f"Large temp files: {format_bytes(temp_size)}",
            "action": "Run Boost to clean temp files",
        })
    else:
        findings.append({
            "category": "Temp Files",
            "status": "ok",
            "message": f"Temp files: {format_bytes(temp_size)}",
            "action": None,
        })

    # 4. CPU usage
    cpu = psutil.cpu_percent(interval=1)
    if cpu > 90:
        findings.append({
            "category": "CPU",
            "status": "warning",
            "message": f"High CPU usage: {cpu:.0f}%",
            "action": "Check Process Manager for heavy processes",
        })
    else:
        findings.append({
            "category": "CPU",
            "status": "ok",
            "message": f"CPU usage normal: {cpu:.0f}%",
            "action": None,
        })

    # 5. Too many startup items
    try:
        startup_items = get_startup_items()
        if len(startup_items) > 15:
            findings.append({
                "category": "Startup",
                "status": "warning",
                "message": f"{len(startup_items)} startup items detected",
                "action": "Disable unnecessary startup apps",
            })
        else:
            findings.append({
                "category": "Startup",
                "status": "ok",
                "message": f"Startup items: {len(startup_items)}",
                "action": None,
            })
    except Exception:
        pass

    # 6. Admin privileges
    if not is_admin():
        findings.append({
            "category": "Permissions",
            "status": "warning",
            "message": "Not running as Administrator",
            "action": "Run as Administrator for full functionality",
        })
    else:
        findings.append({
            "category": "Permissions",
            "status": "ok",
            "message": "Running with Administrator privileges",
            "action": None,
        })

    return findings
