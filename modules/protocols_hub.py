import os
from pathlib import Path

class Protocols:
    def __init__(self):
        self.base_dir = Path.home() / ".rf_toolkit" / "protocols"
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    #menu
    def run(self):
        while True:
            os.system('clear')
            print("========================================")
            print("             PROTOCOLS")
            print("========================================")
            print("1. ADS-B Aircraft Monitoring(BETA! Untested in environments with actual planes flying)")
            print("2. DSD - Digital Speech Decoder")  # NEW OPTION - WOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO yeah
            print("3. Back to Main Menu")
            print("More stuff will be added later")
            
            choice = input("\nEnter choice (1-3): ").strip()  # Updated to 3
            
            if choice == '1':
                self.adsb_menu()
            elif choice == '2':  # NEW - DSD
                self.dsd_menu()
            elif choice == '3':  # Updated from 2 to 3
                return
            else:
                print("Invalid choice!")
                input("Press Enter to continue...")
    
    #ADS-B protocol scanner module
    def adsb_menu(self):
        #finally figured out that python is stupid and tries to import a FOLDER, if it has the same name as the file
        from .protocols.adsb import ADSB
        adsb = ADSB()
        adsb.run()

    # digital speech decoder
    def dsd_menu(self):
        """DSD - Digital Speech Decoder for digital voice protocols"""
        from .protocols.dsd import DSD
        dsd = DSD()
        dsd.run()
