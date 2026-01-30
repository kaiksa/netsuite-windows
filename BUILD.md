# Building NetSuite Windows Executable

## Prerequisites

You need **Windows** and **Python 3.8+** installed to build the executable.

## Method 1: Using PyInstaller (Recommended)

### Step 1: Install PyInstaller
```cmd
pip install pyinstaller
```

### Step 2: Build the executable
```cmd
cd netsuite-windows
pyinstaller --onefile --windowed --name NetSuite --icon=assets/icon.ico netsuite_gui.py
```

Or use the provided setup script:
```cmd
python setup.py
```

### Step 3: Find your executable
The compiled executable will be in: `dist/NetSuite.exe`

### Step 4: Run it
Double-click `NetSuite.exe` to launch the application!

---

## Method 2: Using the setup script

```cmd
cd netsuite-windows
python setup.py
```

This will:
1. Install PyInstaller if not present
2. Build the executable
3. Create a single-file `NetSuite.exe` in `dist/`

---

## Method 3: Run from Source (No Build)

If you have Python installed, you can just run:

```cmd
cd netsuite-windows
python main.py
```

Or:
```cmd
python netsuite_gui.py
```

---

## Build Options

### Single-file executable (default)
```cmd
pyinstaller --onefile --windowed --name NetSuite netsuite_gui.py
```
- Creates one `.exe` file
- Slower startup (unpacks to temp)
- Easier to distribute

### One-folder executable
```cmd
pyinstaller --onedir --windowed --name NetSuite netsuite_gui.py
```
- Creates folder with `.exe` + dependencies
- Faster startup
- Harder to distribute (must send entire folder)

### With console (for debugging)
```cmd
pyinstaller --onefile --name NetSuite netsuite_gui.py
```
Remove `--windowed` to see console output for debugging.

---

## Troubleshooting

### "PyInstaller not found"
```cmd
pip install pyinstaller
```

### "Python not in PATH"
Add Python to your Windows PATH or use full path:
```cmd
C:\Python311\python.exe setup.py
```

### Antivirus flagging the executable
This is a false positive. PyInstaller executables are often flagged because:
- They unpack to temp directories
- They access the network

**Solution:** Add an exception in your antivirus.

### Windows Defender SmartScreen
When first running, Windows may show a warning.
**Click "More info" → "Run anyway"**

---

## Creating a Distribution Package

Once built, create a zip file to distribute:

```cmd
cd dist
zip NetSuite-v1.0.0-Windows.zip NetSuite.exe
```

Or use 7-Zip/WinRAR to create:
- `NetSuite-v1.0.0-Windows.zip`
- Include `NetSuite.exe` and `README.md`

---

## System Requirements

**Minimum:**
- Windows 7 or later
- 100 MB free disk space
- Network connection (for tools to work)

**Recommended:**
- Windows 10 or 11
- 200 MB free disk space
- Administrator access (for some tools)

---

## Auto-update Feature (Future)

Future versions will include auto-update capability:
```cmd
NetSuite.exe --check-updates
NetSuite.exe --update
```

For now, download new releases from GitHub.
