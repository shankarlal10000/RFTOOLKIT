#!/usr/bin/env python3
"""
RFToolkit Setup Script

This script validates platform compatibility, checks required
dependencies, and prepares the local environment for running
RFToolkit modules.

Intended for educational and research usage with HackRF devices.
"""

import os
import sys
import subprocess
from pathlib import Path


# ============================================================
# PLATFORM CHECK
# ============================================================

def platform_check():
    """Verify supported operating system."""

    print("Checking platform compatibility...")

    if sys.platform.startswith("linux"):
        print("[OK] Linux platform detected.")
        return True

    elif sys.platform == "darwin":
        print("[ERROR] macOS is not officially supported due to limited SDR driver support.")
        return False

    elif sys.platform == "win32":
        print("[ERROR] Windows is not supported for direct SDR hardware interaction.")
        print("Please use WSL or a Linux virtual machine.")
        return False

    else:
        print("[ERROR] Unsupported platform detected.")
        return False


# ============================================================
# DEPENDENCY CHECK
# ============================================================

def check_dependencies():
    """Check required system tools and SDR dependencies."""

    print("\nChecking system dependencies...\n")

    required_tools = {
        "git": "git",
        "make": "make",
        "gcc": "gcc",
        "cmake": "cmake"
    }

    all_found = True

    # ------------------------
    # HackRF Tools Check
    # ------------------------

    print("Checking HackRF utilities...")

    hackrf_found = False

    try:
        subprocess.run(["hackrf_info"], capture_output=True, check=True)
        print("[OK] HackRF utilities detected.")
        hackrf_found = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    if not hackrf_found:
        print("[ERROR] HackRF utilities not found.")
        print("Install using: sudo apt install hackrf")
        all_found = False

    # ------------------------
    # Basic Build Tools
    # ------------------------

    print("\nChecking build tools...")

    for tool_name, tool_cmd in required_tools.items():
        try:
            subprocess.run([tool_cmd, "--version"], capture_output=True, check=True)
            print(f"[OK] {tool_name} detected.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"[ERROR] {tool_name} not found.")
            all_found = False

    # ------------------------
    # GNSS Research Dependencies
    # ------------------------

    print("\nChecking GNSS research dependencies...")

    gnss_deps = ["bison", "flex"]

    for dep in gnss_deps:
        try:
            subprocess.run([dep, "--version"], capture_output=True, check=True)
            print(f"[OK] {dep} detected.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"[INFO] {dep} not installed (required for GNSS simulation modules).")

    # ------------------------
    # ADS-B Research Dependencies
    # ------------------------

    print("\nChecking ADS-B monitoring dependencies...")

    adsb_deps = ["librtlsdr-dev", "pkg-config"]

    for dep in adsb_deps:
        try:
            result = subprocess.run(["dpkg", "-l", dep], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[OK] {dep} detected.")
            else:
                print(f"[INFO] {dep} not installed (required for ADS-B research modules).")
        except Exception:
            print(f"[INFO] Unable to verify status of {dep}.")

    # ------------------------
    # Digital Voice Research Dependencies
    # ------------------------

    print("\nChecking digital voice decoding dependencies...")

    dsd_deps = ["dsdcc", "libdsdcc1t64"]

    for dep in dsd_deps:
        try:
            result = subprocess.run(["dpkg", "-l", dep], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[OK] {dep} detected.")
            else:
                print(f"[INFO] {dep} not installed (required for digital voice research).")
        except Exception:
            print(f"[INFO] Unable to verify status of {dep}.")

    # Check dsdccx utility
    print("\nChecking for dsdccx utility...")

    try:
        result = subprocess.run(["which", "dsdccx"], capture_output=True, text=True)

        if result.returncode == 0:
            print("[OK] dsdccx detected in PATH.")
        else:
            print("[INFO] dsdccx not detected. It may be installed later if required.")

    except Exception:
        print("[INFO] Unable to verify dsdccx availability.")

    return all_found


# ============================================================
# INSTALLATION ROUTINE
# ============================================================

def install_rf_toolkit():
    """Prepare local directories and configure toolkit."""

    print("\nPreparing RFToolkit environment...")

    home_dir = Path.home()
    toolkit_dir = home_dir / ".rf_toolkit"
    toolkit_dir.mkdir(exist_ok=True)

    # Protocol module directories
    protocols_dir = toolkit_dir / "protocols"
    protocols_dir.mkdir(exist_ok=True)

    (protocols_dir / "dsd").mkdir(exist_ok=True)

    # Validate main script presence
    main_script = Path("rftoolkit.py")

    if main_script.exists():
        main_script.chmod(0o755)
        print("[OK] Main script configured.")
    else:
        print("[ERROR] rftoolkit.py not found in project directory.")
        return False

    print("\nEnvironment setup completed.")
    print("You can now launch RFToolkit using:")
    print("  python3 rftoolkit.py")
    print("  or")
    print("  ./rftoolkit.py")

    return True


# ============================================================
# MAIN ENTRY
# ============================================================

if __name__ == "__main__":

    print("RFToolkit Setup")
    print("================")

    if not platform_check():
        print("\nUnsupported platform.")
        sys.exit(1)

    if check_dependencies():

        if install_rf_toolkit():

            print("\nSetup completed successfully.")
            print("\nAdditional notes:")
            print("- GNSS simulation modules may require additional setup from the GNSS menu.")
            print("- ADS-B monitoring dependencies can be configured through Protocol modules.")
            print("- Digital speech decoding components may be installed when first used.")

        else:
            print("\nSetup failed.")
            sys.exit(1)

    else:
        print("\nSome required dependencies are missing.")
        print("\nSuggested installation:")
        print("sudo apt install hackrf gcc git make cmake")
        print("Optional modules may require:")
        print("  bison flex")
        print("  librtlsdr-dev pkg-config")
        print("  dsdcc libdsdcc1t64")
        sys.exit(1)
