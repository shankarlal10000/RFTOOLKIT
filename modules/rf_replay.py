import os
import time
import subprocess
from pathlib import Path


class RFReplay:
    """
    RF Signal Capture and Replay Module

    This module enables controlled recording and replay of RF signals
    for educational and research experimentation using HackRF hardware.
    """

    def __init__(self):
        self.base_dir = Path.home() / ".rf_toolkit" / "recordings"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # ============================================================
    # MAIN MENU
    # ============================================================

    def run(self):
        while True:
            os.system("clear")

            print("======================================")
            print("      RF SIGNAL CAPTURE & REPLAY      ")
            print("======================================")
            print("1. Record RF Signal")
            print("2. Replay Recorded Signal")
            print("3. List Recordings")
            print("4. Back to Main Menu")

            choice = input("\nEnter choice (1-4): ").strip()

            if choice == "1":
                self.record_signal()

            elif choice == "2":
                self.replay_signal()

            elif choice == "3":
                self.list_recordings()

            elif choice == "4":
                return

            else:
                print("Invalid selection.")
                input("Press Enter to continue...")

    # ============================================================
    # RECORD SIGNAL
    # ============================================================

    def record_signal(self):
        """Capture RF samples using HackRF."""

        try:
            freq = input("Enter frequency in MHz (example: 433.92): ").strip()

            if not self._valid_frequency(freq):
                print("Invalid frequency format.")
                input("Press Enter to continue...")
                return

            filename = input("Enter filename (without extension): ").strip()
            if not filename:
                filename = f"recording_{int(time.time())}"

            filepath = self.base_dir / f"{filename}.iq"

            print(f"\nRecording RF signal at {freq} MHz")
            print("Press Ctrl+C to stop recording.")

            cmd = [
                "hackrf_transfer",
                "-r", str(filepath),
                "-f", str(float(freq) * 1e6),
                "-s", "2000000",
                "-g", "20",
                "-l", "32"
            ]

            process = subprocess.Popen(cmd)

            try:
                process.wait()

            except KeyboardInterrupt:
                process.terminate()
                print("\nRecording stopped.")

        except Exception as e:
            print(f"Recording error: {e}")

        input("Press Enter to continue...")

    # ============================================================
    # REPLAY SIGNAL
    # ============================================================

    def replay_signal(self):
        """Replay previously captured RF recordings."""

        recordings = list(self.base_dir.glob("*.iq"))

        if not recordings:
            print("No recordings available.")
            input("Press Enter to continue...")
            return

        print("\nAvailable recordings:")
        for i, rec in enumerate(recordings):
            print(f"{i + 1}. {rec.name}")

        try:
            choice = int(input("\nSelect recording to replay: ")) - 1

            if not (0 <= choice < len(recordings)):
                print("Invalid selection.")
                input("Press Enter to continue...")
                return

            freq = input("Enter replay frequency in MHz: ").strip()

            if not self._valid_frequency(freq):
                print("Invalid frequency format.")
                input("Press Enter to continue...")
                return

            gain = input("Enter TX gain (0-47, default 20): ").strip() or "20"

            repeat = input("Repeat transmission? (y/n, default n): ").strip().lower() or "n"

            print(f"\nReplaying {recordings[choice].name} at {freq} MHz")

            cmd = [
                "hackrf_transfer",
                "-t", str(recordings[choice]),
                "-f", str(float(freq) * 1e6),
                "-s", "2000000",
                "-x", gain
            ]

            if repeat == "y":
                cmd.append("-R")
                print("Continuous repeat mode enabled. Press Ctrl+C to stop.")
            else:
                print("Single transmission mode.")

            process = subprocess.Popen(cmd)

            try:
                process.wait()

            except KeyboardInterrupt:
                if repeat == "y":
                    print("\nStopping transmission...")
                    process.terminate()

                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()

        except (ValueError, KeyboardInterrupt):
            print("Operation cancelled.")

        input("Press Enter to continue...")

    # ============================================================
    # LIST RECORDINGS
    # ============================================================

    def list_recordings(self):
        """Display available RF recording files."""

        recordings = list(self.base_dir.glob("*.iq"))

        if not recordings:
            print("No recordings found.")

        else:
            print("\nRecorded RF sample files:")
            for rec in recordings:
                size_mb = rec.stat().st_size / (1024 * 1024)
                print(f"  {rec.name} ({size_mb:.2f} MB)")

        input("\nPress Enter to continue...")

    # ============================================================
    # HELPERS
    # ============================================================

    def _valid_frequency(self, freq):
        """Validate frequency input."""
        try:
            float(freq)
            return True
        except ValueError:
            return False
