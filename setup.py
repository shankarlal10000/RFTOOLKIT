#!/usr/bin/env python3
"""
Setup script for RFToolkit
Please launch before using anything else in the framework
"""

import os
import sys
import subprocess
from pathlib import Path

def platform_check():
    """Check if we're on a supported platform"""
    print("Checking platform...")
    
    if sys.platform == "win32":
        print("[ERROR] Windows is not supported. Use WSL or a Linux VM.")
        print("This framework requires direct hardware access to HackRF.")
        return False
    elif sys.platform == "darwin":
        print("[ERROR] macOS is not officially supported.")
        return False
    elif sys.platform == "linux":
        print("[OK] Linux detected - supported platform")
        return True
    else:
        print("[ERROR] Unknown platform detected")
        return False

def check_dependencies():
    """Check for all required dependencies"""
    required_tools = {
        'git': 'git',
        'make': 'make', 
        'gcc': 'gcc',
        'cmake': 'cmake'
    }
    
    print("Checking dependencies...")
    all_found = True
    
    # Check HackRF
    print("Checking for HackRF...")
    hackrf_found = False
    
    try:
        result = subprocess.run(['dpkg', '-l', 'hackrf'], capture_output=True, text=True)
        if result.returncode == 0 and 'hackrf' in result.stdout:
            print("[OK] hackrf package installed")
            hackrf_found = True
    except:
        pass
    
    if not hackrf_found:
        try:
            result = subprocess.run(['which', 'hackrf_info'], capture_output=True, text=True)
            if result.returncode == 0:
                print("[OK] hackrf tools found in PATH")
                hackrf_found = True
        except:
            pass
    
    if not hackrf_found:
        try:
            result = subprocess.run(['hackrf_info', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("[OK] hackrf_info works")
                hackrf_found = True
        except:
            pass
    
    if not hackrf_found:
        print("[ERROR] HackRF not found! This is required for the framework.")
        print("Install it with: sudo apt install hackrf")
        all_found = False
    else:
        print("[OK] HackRF detected")
    
    # Check basic tools
    for tool_name, tool_cmd in required_tools.items():
        try:
            subprocess.run([tool_cmd, '--version'], capture_output=True, check=True)
            print(f"[OK] {tool_name} found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"[ERROR] {tool_name} not found")
            all_found = False

    # Check GPS dependencies
    print("Checking for GPS simulator dependencies...")
    gps_deps = ['bison', 'flex']
    for dep in gps_deps:
        try:
            subprocess.run([dep, '--version'], capture_output=True, check=True)
            print(f"[OK] {dep} found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"[WARNING] {dep} not found (needed for GPS spoofing)")

    # Check ADS-B dependencies
    print("Checking for ADS-B monitoring dependencies...")
    adsb_deps = ['librtlsdr-dev', 'pkg-config']
    for dep in adsb_deps:
        try:
            result = subprocess.run(['dpkg', '-l', dep], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[OK] {dep} found")
            else:
                print(f"[INFO] {dep} not installed (needed for ADS-B monitoring)")
        except:
            print(f"[INFO] {dep} status unknown")

    # Check DSD dependencies
    print("Checking for DSD (Digital Speech Decoder) dependencies...")
    dsd_deps = ['dsdcc', 'libdsdcc1t64']
    
    for dep in dsd_deps:
        try:
            result = subprocess.run(['dpkg', '-l', dep], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[OK] {dep} found")
            else:
                print(f"[INFO] {dep} not installed (needed for DSD)")
        except:
            print(f"[INFO] {dep} status unknown")
    
    # Check if dsdccx is available
    print("Checking for dsdccx...")
    try:
        result = subprocess.run(['which', 'dsdccx'], capture_output=True, text=True)
        if result.returncode == 0:
            print("[OK] dsdccx found in PATH")
        else:
            # Check common locations
            dsd_paths = [
                '/usr/bin/dsdccx',
                '/usr/local/bin/dsdccx',
            ]
            dsd_found = False
            for path in dsd_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    print(f"[OK] dsdccx found at {path}")
                    dsd_found = True
                    break
            
            if not dsd_found:
                print("[INFO] dsdccx not found (will be installed when needed)")
    except:
        print("[INFO] dsdccx status unknown")
    
    return all_found

def install_rf_toolkit():
    """Create directories and set up the toolkit"""
    home_dir = Path.home()
    toolkit_dir = home_dir / ".rf_toolkit"
    toolkit_dir.mkdir(exist_ok=True)
    
    # Create protocol-specific directories
    protocols_dir = toolkit_dir / "protocols"
    protocols_dir.mkdir(exist_ok=True)
    
    dsd_dir = protocols_dir / "dsd"
    dsd_dir.mkdir(exist_ok=True)
    
    # Validate main script
    main_script = Path("rftoolkit.py")
    if main_script.exists():
        main_script.chmod(0o755)
        print("[OK] Main script configured")
    else:
        print("[ERROR] Main script not found!")
        return False
    
    print("\nInstallation completed!")
    print("You can now run: python3 rftoolkit.py")
    print("Or: ./rftoolkit.py")
    return True

if __name__ == "__main__":
    print("RF Toolkit Setup")
    print("================")
    
    if not platform_check():
        print("\nUnsupported platform detected!")
        sys.exit(1)
    
    if check_dependencies():
        if install_rf_toolkit():
            print("\nSetup completed successfully!")
            print("\nAdditional setup notes:")
            print("- GPS Spoofing: Run GPS setup from the GPS Spoofing menu")
            print("- ADS-B: Run ADS-B setup from the Protocols menu") 
            print("- DSD: Run DSD setup from the Protocols menu (via the dsd.py module)") # Updated DSD note
        else:
            print("\nSetup failed!")
            sys.exit(1)
    else:
        print("\nPlease install missing dependencies first!")
        print("Basic dependencies: sudo apt install hackrf gcc git make cmake")
        print("For GPS spoofing also install: bison flex")
        print("For ADS-B monitoring also install: librtlsdr-dev pkg-config")
        print("For DSD digital voice decoding also install: dsdcc libdsdcc1t64")
        print("Note: readsb and dsd can be installed using setup options in Protocols tab")
        sys.exit(1)
