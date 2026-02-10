import os
from pathlib import Path


class Protocols:
    """
    Protocol Research Hub

    This module provides access to RF protocol analysis tools
    used for educational and research experimentation.
    """

    def __init__(self):
        self.base_dir = Path.home() / ".rf_toolkit" / "protocols"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ============================================================
    # MAIN MENU
    # ============================================================

    def run(self):
        while True:
            os.system("clear")

            print("========================================")
            print("        PROTOCOL RESEARCH MODULES       ")
            print("========================================")
            print("1. ADS-B Aircraft Signal Monitoring")
            print("2. Digital Speech Protocol Analysis")
            print("3. Back to Main Menu")
            print("\nAdditional protocol modules may be added in future releases.")

            choice = input("\nEnter choice (1-3): ").strip()

            if choice == "1":
                self.adsb_menu()

            elif choice == "2":
                self.dsd_menu()

            elif choice == "3":
                return

            else:
                print("Invalid selection.")
                input("Press Enter to continue...")

    # ============================================================
    # ADS-B MODULE
    # ============================================================

    def adsb_menu(self):
        """
        ADS-B Monitoring Module

        Used for studying aircraft broadcast transmissions
        and aviation communication protocols.
        """

        try:
            from .protocols.adsb import ADSB

            ADSB().run()

        except ImportError as e:
            print(f"ADS-B module loading error: {e}")
            input("Press Enter to continue...")

    # ============================================================
    # DSD MODULE
    # ============================================================

    def dsd_menu(self):
        """
        Digital Speech Decoder Module

        Used for analyzing digital voice communication
        protocols such as DMR and related formats.
        """

        try:
            from .protocols.dsd import DSD

            DSD().run()

        except ImportError as e:
            print(f"DSD module loading error: {e}")
            input("Press Enter to continue...")
