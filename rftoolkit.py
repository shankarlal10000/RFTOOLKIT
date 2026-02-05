#!/usr/bin/env python3
"""
HackRF SDR Toolkit Framework
College RF Project - Educational Use Only
Made by JustADood

"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path
import argparse

class RFToolkit:
    def __init__(self):
        self.clear_screen()
        self.author = "JustADood"
        self.version = "0.6.1"
        self.base_dir = Path.home() / ".rf_toolkit"
        self.base_dir.mkdir(exist_ok=True)
        
    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def display_logo(self):
        logo = """
==================================================
         RF SDR TOOLKIT FRAMEWORK
           Educational Use Only
             College Project
==================================================
        """
        print(logo)
# Main menu, now with proper look(i think)
# Edit - still sucks, needs coloring or some bullshit
    def display_menu(self):
        print(f"Author: {self.author}")
        print(f"Version: {self.version}")
        print("\n" + "="*50)
        print("           MAIN MENU")
        print("="*50)
        print("1. RF Replay Attack")
        print("2. GPS Spoofing")
        print("3. RF Jamming")
        print("4. Protocols (ADS-B(BETA), etc.)")  # NEW OPTION, WOOOOOOOOOOOOOOOOOOO, yeah baby
        print("5. RF Samples/Scripts (Portapack/FZ) (Not ready yet)")
        print("6. Exit")  # Updated from 5 to 6
        print("="*50)
    
    def run(self):
        while True:
            self.clear_screen()
            self.display_logo()
            self.display_menu()
            
            try:
                choice = input("\nEnter your choice (1-6): ").strip()  # Updated to 6
                
                if choice == '1':
                    self.rf_replay_menu()
                elif choice == '2':
                    self.gps_spoof_menu()
                elif choice == '3':
                    self.rf_jamming_menu()
                elif choice == '4':
                    self.protocols_menu()
                elif choice == '5':
                    self.special_scripts_menu()
                elif choice == '6':
                    print("\nThank you for using RFToolkit!")
                    sys.exit(0)
                else:
                    print("\nInvalid choice! Please try again.")
                    input("Press Enter to continue...")
                    
            except KeyboardInterrupt:
                print("\n\nOperation cancelled by user.")
                sys.exit(0)
            except Exception as e:
                print(f"\nError: {e}")
                input("Press Enter to continue...")
# Functions of modules
    def rf_replay_menu(self):
        from modules.rf_replay import RFReplay
        replay = RFReplay()
        replay.run()

    def gps_spoof_menu(self):
        from modules.gps_spoof import GPSSpoof
        gps = GPSSpoof()
        gps.run()

    def rf_jamming_menu(self):
        from modules.rf_jammer import RFJammer
        jammer = RFJammer()
        jammer.run()

    def protocols_menu(self):
        from modules.protocols_hub import Protocols
        protocols = Protocols()
        protocols.run()

    def special_scripts_menu(self):
        from modules.special_scripts import SpecialScripts
        scripts = SpecialScripts()
        scripts.run()

def main():
# Check if root is available
    if os.geteuid() != 0:
        print("Warning: Some features may require root privileges")
# sleep needed, because framework may be ran on a potato(i hate poor people)
        time.sleep(1)
    
    toolkit = RFToolkit()
    toolkit.run()

if __name__ == "__main__":
    main()
