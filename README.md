# NetSuite Windows GUI

A comprehensive network administration toolkit for Windows with a graphical interface. NetSuite provides network diagnostics, scanning, and monitoring tools in an easy-to-use GUI application.

![NetSuite GUI](https://img.shields.io/badge/version-1.0.0-blue) ![Python](https://img.shields.io/badge/python-3.8+-green) ![Platform](https://img.shields.io/badge/platform-windows-lightgrey)

## ⚠️ Important: No Pre-built Executables Yet

**This project currently requires building from source on Windows.** Pre-built `.exe` files are not yet available in releases.

**To use NetSuite:**
1. Install Python 3.8+ on Windows
2. Clone this repository
3. Either run directly with `python netsuite_gui.py` OR build an executable using PyInstaller (see [BUILD.md](BUILD.md))

**Why no executables?** This project is built on a Linux development environment. To create Windows `.exe` files, someone needs to build it on a Windows machine using PyInstaller. If you'd like to contribute pre-built executables, please see [BUILD.md](BUILD.md) for instructions!

---

## Features

### Core Network Tools
- **DNS Lookup** - Query DNS records (A, AAAA, MX, NS, TXT, CNAME, SOA)
- **Ping** - Continuous and count-based ping with statistics
- **Port Scanner** - Scan for open ports with service detection
- **Traceroute** - Trace network paths to destinations
- **Network Info** - Display network interfaces and configuration

### Information & Lookup
- **WHOIS** - Domain and IP whois lookups
- **IP Geolocation** - Get geographical information for IP addresses
- **HTTP Headers** - Inspect HTTP response headers
- **SSL/TLS Checker** - Verify SSL certificates

### Utilities
- **Subnet Calculator** - Calculate network details from CIDR
- **Network Discovery** - Scan local network for active devices
- **Wake-on-LAN** - Send magic packets to wake remote devices
- **Bandwidth Monitor** - Monitor network interface bandwidth
- **Connectivity Test** - Comprehensive internet connectivity testing

## Installation

### Method 1: Run from Source (Recommended for Development)

1. **Install Python 3.8+**
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"

2. **Clone or Download**
   ```bash
   git clone https://github.com/kaiksa/netsuite-windows.git
   cd netsuite-windows
   ```

3. **Run**
   ```bash
   python netsuite_gui.py
   ```

### Method 2: Create Executable with PyInstaller

1. **Install PyInstaller**
   ```bash
   pip install pyinstaller
   ```

2. **Build Executable**
   ```bash
   pyinstaller --onefile --windowed --name="NetSuite" netsuite_gui.py
   ```

3. **Run**
   - The executable will be in `dist/NetSuite.exe`

### Method 3: Download Pre-built Executable

Coming soon to the [Releases](https://github.com/kaiksa/netsuite-windows/releases) page.

## Usage

### Quick Start

1. Launch NetSuite GUI
2. Select a tool from the sidebar
3. Enter the target (IP, domain, etc.)
4. Click the tool's button (Ping, Scan, Lookup, etc.)
5. View results in the output area

### Tool-Specific Usage

#### DNS Lookup
- Enter a domain name
- Select record type (A, AAAA, MX, etc.)
- Click "Lookup" or "Query All Records"

#### Ping
- Enter host or IP address
- Set count or enable continuous mode
- Click "Ping" to start

#### Port Scanner
- Enter target IP address
- Choose scan type (common ports, range, single)
- Adjust timeout if needed
- Click "Scan"

#### Traceroute
- Enter destination host/IP
- Set max hops (default: 30)
- Enable/disable hostname resolution
- Click "Trace"

#### Network Discovery
- Click "Auto-Detect" to find your local network
- Or manually enter CIDR range (e.g., 192.168.1.0/24)
- Click "Scan"

#### Wake-on-LAN
- Enter target MAC address (XX:XX:XX:XX:XX:XX)
- Set broadcast IP (default: 255.255.255.255)
- Click "Send Magic Packet"

## Screenshots

### Main Window
```
┌─────────────────────────────────────────────────────────────┐
│ NetSuite - Network Administration Toolkit                  │
├────────────┬────────────────────────────────────────────────┤
│            │                                                │
│ Network    │  ┌──────────────────────────────────────────┐ │
│ Tools      │  │ DNS Lookup                               │ │
│            │  │ Domain: [example.com          ]         │ │
│ □ DNS Lookup│  │ Record Type: [A ▼]                     │ │
│ □ Ping     │  │ [Lookup] [Query All Records]            │ │
│ □ Port     │  └──────────────────────────────────────────┘ │
│ □ Scan     │                                                │
│ □ Trace    │  ┌──────────────────────────────────────────┐ │
│ ...        │  │ Output                                   │ │
│            │  │ ======================================== │ │
│            │  │ DNS Lookup: example.com (A)              │ │
│            │  │ 93.184.216.34                            │ │
│            │  │                                          │ │
│            │  └──────────────────────────────────────────┘ │
│            │                                                │
├────────────┴────────────────────────────────────────────────┤
│ Ready                                       [Progress Bar]   │
└─────────────────────────────────────────────────────────────┘
```

## Requirements

- Windows 7/8/10/11
- Python 3.8 or higher (if running from source)
- Administrator privileges (recommended for some tools)

## Configuration

NetSuite stores configuration in:
- **Config File**: `%APPDATA%\NetSuite\config.ini`
- **Logs**: `%APPDATA%\NetSuite\logs\netsuite.log`

## Troubleshooting

### "Command not found" errors
- Some tools use Windows built-in commands (ping, tracert, nslookup, netstat, arp)
- These should be available on all Windows installations
- If missing, check Windows Firewall or antivirus settings

### Port Scanner shows no results
- Windows Firewall may be blocking scans
- Try scanning with a longer timeout
- Some networks block ICMP/TCP scans

### Network Discovery not finding devices
- Ensure you're on the same network segment
- Try pinging devices first to populate ARP cache
- Some devices may not respond to discovery probes

### Running as Administrator
- Right-click → "Run as administrator"
- Required for some network operations
- Helps with firewall restrictions

## Building from Source

### Development Setup
```bash
# Clone repository
git clone https://github.com/kaiksa/netsuite-windows.git
cd netsuite-windows

# Run directly
python netsuite_gui.py
```

### Creating Executable
```bash
# Install PyInstaller
pip install pyinstaller

# Build
pyinstaller --onefile --windowed --name="NetSuite" netsuite_gui.py

# Or use the build script
python setup.py
```

## Project Structure
```
netsuite-windows/
├── netsuite_gui.py          # Main application
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── setup.py                # Build script
├── tools/                  # Tool modules
│   ├── __init__.py
│   ├── base_tool.py       # Base class for all tools
│   ├── dns_lookup.py
│   ├── ping_tool.py
│   ├── port_scanner.py
│   ├── traceroute.py
│   ├── network_info.py
│   ├── whois_tool.py
│   ├── connectivity_test.py
│   ├── ip_geolocation.py
│   ├── subnet_calculator.py
│   ├── network_discovery.py
│   ├── ssl_checker.py
│   ├── http_headers.py
│   ├── wol_tool.py
│   └── bandwidth_monitor.py
└── utils/                  # Utility modules
    ├── __init__.py
    ├── config_manager.py
    └── logger.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Author

Kai - [GitHub](https://github.com/kaiksa)

## Acknowledgments

- Built with Python and tkinter
- Uses Windows built-in networking commands
- Icons and design inspired by modern network tools

## Changelog

### Version 1.0.0 (2024)
- Initial release
- 15 network tools
- Windows GUI with tabbed interface
- Configuration management
- Logging support
- Export functionality
