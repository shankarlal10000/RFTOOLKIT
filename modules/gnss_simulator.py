import os
import subprocess
from pathlib import Path
import time
import datetime
import shutil
import math


class GNSSSimulator:
    """
    GNSS Signal Simulation & Navigation Research Module

    This module integrates gps-sdr-sim to generate GNSS signal
    simulation data for controlled laboratory testing and
    navigation receiver research.

    Intended strictly for educational and research environments.
    """

    def __init__(self):

        self.gps_sim_dir = Path.home() / ".rf_toolkit" / "gps_sdr_sim"
        self.motion_dir = self.gps_sim_dir / "motion_files"

        self.gps_sim_dir.mkdir(parents=True, exist_ok=True)
        self.motion_dir.mkdir(exist_ok=True)

    # ============================================================
    # MAIN MENU
    # ============================================================

    def run(self):

        while True:
            os.system("clear")

            print("========================================")
            print("     GNSS SIGNAL SIMULATION MODULE      ")
            print("========================================")
            print("1. Setup / Update gps-sdr-sim")
            print("2. Ephemeris File Manager")
            print("3. Configure & Generate Simulation")
            print("4. Transmit Simulation Signal")
            print("5. Back to Main Menu")

            choice = input("\nEnter choice (1-5): ").strip()

            if choice == "1":
                self.setup_gps_sdr_sim()

            elif choice == "2":
                self.ephemeris_menu()

            elif choice == "3":
                self.generate_signal_menu()

            elif choice == "4":
                self.transmit_menu()

            elif choice == "5":
                return

            else:
                print("Invalid selection.")
                input("Press Enter to continue...")

    # ============================================================
    # SETUP gps-sdr-sim
    # ============================================================

    def setup_gps_sdr_sim(self):

        print("\n--- gps-sdr-sim Setup ---")

        if (self.gps_sim_dir / ".git").exists():

            print("Repository detected. Pulling updates...")

            try:
                subprocess.run(["git", "pull"], cwd=self.gps_sim_dir, check=True)
            except Exception as e:
                print(f"[WARN] Git update failed: {e}")

        elif any(self.gps_sim_dir.iterdir()):

            print(f"[WARN] Directory {self.gps_sim_dir} exists but is not a git repository.")
            ans = input("Reinitialize repository? (y/n): ").lower()

            if ans == "y":
                shutil.rmtree(self.gps_sim_dir)
                self.gps_sim_dir.mkdir()
                self._clone_repo()

        else:
            self._clone_repo()

        self.motion_dir.mkdir(exist_ok=True)

        print("\nCompiling gps-sdr-sim...")

        try:
            cmd = [
                "gcc",
                "gpssim.c",
                "-lm",
                "-O3",
                "-o",
                "gps-sdr-sim",
                "-DUSER_MOTION_SIZE=4000"
            ]

            subprocess.run(cmd, cwd=self.gps_sim_dir, check=True)

            print("Compilation completed.")

        except subprocess.CalledProcessError:
            print("Compilation failed. Ensure build tools are installed.")

        input("Press Enter to continue...")

    def _clone_repo(self):
        print("Cloning gps-sdr-sim repository...")

        subprocess.run(
            ["git", "clone", "https://github.com/osqzss/gps-sdr-sim.git", str(self.gps_sim_dir)],
            check=True
        )

    # ============================================================
    # EPHEMERIS HANDLING
    # ============================================================

    def ephemeris_menu(self):

        print("\n--- Ephemeris File Manager ---")
        print("gps-sdr-sim requires a GPS RINEX navigation file (.n).")

        files = list(self.gps_sim_dir.glob("brdc*"))
        valid_file = None

        for f in files:

            if f.suffix == ".gz":
                print(f"Extracting {f.name}...")
                subprocess.run(["gunzip", "-k", "-f", str(f)], check=True)
                f = f.with_suffix("")

            if f.suffix.endswith("n"):
                valid_file = f
                print(f"[OK] {f.name}")

        if valid_file:
            self.ephemeris_file = valid_file
            print(f"\nSelected ephemeris: {valid_file.name}")

        else:
            print("\nNo valid GPS ephemeris file found.")
            print("Download from NASA CDDIS GNSS archive.")

        input("Press Enter to continue...")

    # ============================================================
    # SIGNAL GENERATION
    # ============================================================

    def generate_signal_menu(self):

        if not hasattr(self, "ephemeris_file"):
            print("Ephemeris file not selected.")
            input("Press Enter...")
            return

        while True:

            os.system("clear")
            print(f"--- Simulation Using {self.ephemeris_file.name} ---")
            print("1. Static Location Simulation")
            print("2. Circular Motion Simulation")
            print("3. Back")

            choice = input("Choice: ").strip()

            if choice == "1":
                self._gen_static()
                break

            elif choice == "2":
                self._gen_circle()
                break

            elif choice == "3":
                return

    # ============================================================
    # TIME ALIGNMENT
    # ============================================================

    def _get_time_args(self):

        filename = self.ephemeris_file.name

        try:
            day_of_year = int(filename[4:7])
            year = 2000 + int(filename[9:11])

            date = datetime.datetime(year, 1, 1) + datetime.timedelta(day_of_year - 1)
            time_str = date.strftime("%Y/%m/%d,01:00:00")

            return ["-t", time_str]

        except Exception:
            return []

    # ============================================================
    # STATIC SIMULATION
    # ============================================================

    def _gen_static(self):

        lat = input("Latitude: ").strip()
        lon = input("Longitude: ").strip()
        alt = input("Altitude (meters, default 100): ").strip() or "100"

        cmd = [
            "./gps-sdr-sim",
            "-e",
            self.ephemeris_file.name,
            "-b",
            "8",
            "-l",
            f"{lat},{lon},{alt}"
        ]

        cmd += self._get_time_args()
        self._run_gen_cmd(cmd)

    # ============================================================
    # CIRCULAR TRAJECTORY
    # ============================================================

    def _gen_circle(self):

        lat0 = float(input("Center Latitude: "))
        lon0 = float(input("Center Longitude: "))

        radius = float(input("Radius meters (default 50): ") or 50)
        speed = float(input("Speed m/s (default 10): ") or 10)
        duration = int(input("Duration seconds (default 300): ") or 300)

        csv_path = self.motion_dir / "circle_llh.csv"

        print("Generating motion trajectory...")

        with open(csv_path, "w") as f:

            steps = duration * 10

            for i in range(steps):

                t = i / 10
                angle = (speed * t / radius)

                dx = radius * math.cos(angle)
                dy = radius * math.sin(angle)

                dlat = dy / 111111.0
                dlon = dx / (111111.0 * math.cos(math.radians(lat0)))

                f.write(f"{lat0 + dlat},{lon0 + dlon},100.0\n")

        cmd = [
            "./gps-sdr-sim",
            "-e",
            self.ephemeris_file.name,
            "-b",
            "8",
            "-x",
            str(csv_path),
            "-d",
            str(duration)
        ]

        cmd += self._get_time_args()
        self._run_gen_cmd(cmd)

    # ============================================================
    # COMMAND EXECUTION
    # ============================================================

    def _run_gen_cmd(self, cmd):

        print(f"\nExecuting: {' '.join(cmd)}")

        try:
            subprocess.run(cmd, cwd=self.gps_sim_dir, check=True)

            bin_path = self.gps_sim_dir / "gpssim.bin"

            if bin_path.exists():
                print("Simulation binary generated successfully.")

        except subprocess.CalledProcessError:
            print("Simulation generation failed.")

        input("Press Enter to continue...")

    # ============================================================
    # TRANSMISSION
    # ============================================================

    def transmit_menu(self):

        bin_file = self.gps_sim_dir / "gpssim.bin"

        if not bin_file.exists():
            print("Simulation binary not found.")
            input("Press Enter...")
            return

        print("\nChecking HackRF device...")

        try:
            subprocess.run(["hackrf_info"], capture_output=True, check=True)
            print("HackRF detected.")
        except Exception:
            print("HackRF not detected.")
            input("Press Enter...")
            return

        gain = input("TX Gain (0-47, default 25): ").strip() or "25"

        cmd = [
            "hackrf_transfer",
            "-t",
            "gpssim.bin",
            "-f",
            "1575420000",
            "-s",
            "2600000",
            "-a",
            "1",
            "-x",
            gain,
            "-R"
        ]

        print("Starting simulation transmission. Press Ctrl+C to stop.")

        try:
            subprocess.run(cmd, cwd=self.gps_sim_dir)
        except KeyboardInterrupt:
            print("\nTransmission stopped.")

        input("Press Enter to continue...")
