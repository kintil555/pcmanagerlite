# 🖥️ PC Manager Lite

A lightweight, modern PC management utility for Windows — built with Python & CustomTkinter.

![PC Manager Lite](.github/screenshot.png)

## ✨ Features

| Feature | Description |
|---------|-------------|
| ⚡ **PC Boost** | Free RAM & clear temp files in one click |
| 🗑️ **Deep Cleanup** | Browser cache, DNS, Prefetch, Recycle Bin, Recent Files |
| 🔄 **Process Manager** | View, sort & terminate running processes |
| 🚀 **Startup Manager** | Enable/disable Windows startup programs |
| ❤️ **Health Check** | Full CPU, RAM, Disk, Startup & permissions analysis |
| 🔔 **System Tray** | Minimize to tray, boost from tray menu |
| 🎨 **Modern Dark UI** | Clean dark theme with customtkinter |

## 📥 Download

Go to [Releases](../../releases) and download:
- `PCManagerLite_Setup_vX.X.X.exe` — Full installer (recommended)
- `PCManagerLite.exe` — Portable, no install needed

## 🛠️ Build from Source

### Requirements
- Python 3.11+
- Windows 10/11

### Steps

```bash
# Clone
git clone https://github.com/yourusername/pcmanager-lite
cd pcmanager-lite

# Install dependencies
pip install -r requirements.txt

# Run directly
python src/main.py

# Build EXE
pyinstaller PCManagerLite.spec --clean --noconfirm

# Build installer (requires Inno Setup 6 installed)
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\installer.iss
```

## 🚀 GitHub Actions (Auto Build)

Pushing a version tag triggers an automatic build:

```bash
git tag v1.0.0
git push origin v1.0.0
```

This will:
1. Build `PCManagerLite.exe` with PyInstaller
2. Package it into an Inno Setup installer
3. Create a GitHub Release with both files attached

## ⚠️ Permissions

Some features (RAM trimming, process termination, Prefetch cleanup) require **Administrator** privileges. The app will request elevation via UAC on startup.

## 📁 Project Structure

```
pcmanager-lite/
├── src/
│   ├── main.py          # Entry point
│   ├── app.py           # Main UI & application class
│   └── system_utils.py  # System operations (cleanup, processes, etc.)
├── assets/
│   ├── icon.ico         # App icon
│   └── icon.png         # Tray icon
├── installer/
│   └── installer.iss    # Inno Setup script
├── .github/
│   └── workflows/
│       └── build.yml    # GitHub Actions CI/CD
├── PCManagerLite.spec   # PyInstaller config
├── file_version_info.txt
├── requirements.txt
└── README.md
```

## 📄 License

MIT License — free to use, modify and distribute.
