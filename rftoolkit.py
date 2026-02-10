#!/usr/bin/env python3
"""
RFToolkit - HackRF SDR Research Framework

Open-source educational and research toolkit designed to simplify
software-defined radio experimentation using HackRF devices.

This framework provides modular RF experimentation workflows
focused on signal analysis, protocol research, and controlled
RF laboratory experimentation.

Author: Shankar
License: GPLv3
"""

import os
import sys
import time
from pathlib import Path


class RFToolkit:
    def __init__(self):
        self.clear_screen()
        self.author = "Srajan Sonkesriya"
        self.project_name = "RFToolkit"
        self.version = "0.6.1"

        # Base configuration directory
        self.base_dir = Path.home() / ".rf_toolkit"
        self.base_dir.mkdir(exist_ok=True)

    def clear_screen(self):
        os.system("clear" if os.name == "posix" else "cls")

    def display_logo(self):
        logo = f"""
==================================================
                {self.project_name}
        SDR Research & Experimentation Toolkit
                    Version {self.version}
==================================================
        """
        print(logo)

    def display_menu(self):
        print(f"Maintainer: {self.author}")
        print("\n" + "=" * 50)
        print("                MAIN MENU")
        print("=" * 50)

        print("1. RF Signal Capture & Replay")
        print("2. GNSS Signal Simulation")
        print("3. RF Interference Simulation")
        print("4. Protocol Research Tools")
        print("5. Experimental Scripts & Samples")
        print("6. Exit")

        print("=" * 50)

    def run(self):
        while True:
            self.clear_screen()
            self.display_logo()
            self.display_menu()

            try:
                choice = input("\nEnter your choice (1-6): ").strip()

                if choice == "1":
                    self.rf_replay_menu()

                elif choice == "2":
                    self.gnss_simulation_menu()

                elif choice == "3":
                    self.rf_interference_menu()

                elif choice == "4":
                    self.protocols_menu()

                elif choice == "5":
                    self.special_scripts_menu()

                elif choice == "6":
                    print("\nThank you for using RFToolkit.")
                    sys.exit(0)

                else:
                    print("\nInvalid selection. Please try again.")
                    input("Press Enter to continue...")

            except KeyboardInterrupt:
                print("\n\nOperation cancelled by user.")
                sys.exit(0)

            except Exception as e:
                print(f"\nError: {e}")
                input("Press Enter to continue...")

    # ================= MODULE ROUTERS ================= #

    def rf_replay_menu(self):
        """
        RF signal capture and replay workflows.
        Intended for controlled RF experimentation and protocol testing.
        """
        from modules.rf_replay import RFReplay

        RFReplay().run()

    def gnss_simulation_menu(self):
        """
        GNSS signal simulation module for navigation system research
        and controlled vulnerability testing.
        """
        from modules.gps_spoof import GPSSpoof

        GPSSpoof().run()

    def rf_interference_menu(self):
        """
        RF interference simulation module used for studying
        communication robustness and spectrum coexistence challenges.
        """
        from modules.rf_jammer import RFJammer

        RFJammer().run()

    def protocols_menu(self):
        """
        Protocol research hub containing signal decoding
        and wireless protocol experimentation modules.
        """
        from modules.protocols_hub import Protocols

        Protocols().run()

    def special_scripts_menu(self):
        """
        Experimental workflows and community-contributed scripts.
        """
        from modules.special_scripts import SpecialScripts

        SpecialScripts().run()


def main():

    # Root privilege warning
    if os.geteuid() != 0:
        print("Note: Some SDR operations may require elevated privileges.")
        time.sleep(1)

    toolkit = RFToolkit()
    toolkit.run()


if __name__ == "__main__":
    main()
