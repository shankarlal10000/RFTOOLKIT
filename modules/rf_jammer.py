import os
import subprocess
import signal
import time
import random
import sys
from pathlib import Path
import threading


class RFInterferenceSimulator:
    """
    RF Interference Simulation Module

    This module simulates RF spectrum congestion and interference
    scenarios for educational and laboratory research purposes.

    Intended for controlled testing environments only.
    """

    def __init__(self):
        self.transmit_process = None
        self.stop_flag = False
        self.temp_dir = self._get_temp_dir()

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    # ============================================================
    # TEMP DIRECTORY HANDLING
    # ============================================================

    def _get_temp_dir(self):
        temp_dirs = [
            "/tmp",
            str(Path.home() / ".rf_toolkit" / "temp"),
            "/var/tmp"
        ]

        for directory in temp_dirs:
            try:
                path = Path(directory)
                path.mkdir(parents=True, exist_ok=True)

                test_file = path / "write_test"
                test_file.write_text("test")
                test_file.unlink()

                return directory
            except Exception:
                continue

        return "/tmp"

    # ============================================================
    # SIGNAL HANDLING
    # ============================================================

    def _signal_handler(self, signum, frame):
        print("\nTermination requested.")
        self.stop_transmission()
        sys.exit(0)

    # ============================================================
    # MAIN MENU
    # ============================================================

    def run(self):
        while True:
            os.system("clear")

            print("========================================")
            print("     RF INTERFERENCE SIMULATION LAB     ")
            print("========================================")
            print("1. Continuous Interference Simulation")
            print("2. Frequency Sweep Interference")
            print("3. Random Channel Congestion Simulation")
            print("4. Stop Active Simulation")
            print("5. Back to Main Menu")

            choice = input("\nEnter choice (1-5): ").strip()

            if choice == "1":
                self.continuous_simulation()

            elif choice == "2":
                self.sweep_simulation()

            elif choice == "3":
                self.random_simulation()

            elif choice == "4":
                self.stop_transmission()

            elif choice == "5":
                self.stop_transmission()
                return

            else:
                print("Invalid selection.")
                input("Press Enter to continue...")

    # ============================================================
    # NOISE GENERATION
    # ============================================================

    def _generate_noise_file(self, size_mb=10):
        noise_file = Path(self.temp_dir) / "interference_noise.bin"

        print(f"Generating {size_mb} MB test noise file...")

        cmd = [
            "dd",
            "if=/dev/urandom",
            f"of={noise_file}",
            "bs=1M",
            f"count={size_mb}"
        ]

        result = subprocess.run(cmd, capture_output=True)

        if result.returncode == 0 and noise_file.exists():
            return str(noise_file)

        print("Noise generation failed.")
        return None

    # ============================================================
    # TRANSMISSION START
    # ============================================================

    def _start_transmission(self, freq_mhz, bandwidth_mhz=20, duration=None):

        try:
            noise_file = self._generate_noise_file()
            if not noise_file:
                return False

            cmd = [
                "hackrf_transfer",
                "-t", noise_file,
                "-f", str(float(freq_mhz) * 1e6),
                "-s", "20000000",
                "-b", str(float(bandwidth_mhz) * 1e6),
                "-x", "40",
                "-a", "1",
                "-R"
            ]

            if duration:
                samples = int(float(duration) * 20000000)
                cmd.extend(["-n", str(samples)])

            self.transmit_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            time.sleep(0.5)

            return self.transmit_process.poll() is None

        except Exception as e:
            print(f"Transmission error: {e}")
            return False

    # ============================================================
    # CONTINUOUS INTERFERENCE
    # ============================================================

    def continuous_simulation(self):
        try:
            freq = input("Enter frequency in MHz: ").strip()
            bandwidth = input("Bandwidth MHz (default 20): ").strip() or "20"

            print("\nStarting continuous interference simulation.")
            print("Press Ctrl+C to stop.")

            self.stop_transmission()

            if self._start_transmission(freq, bandwidth):
                print("Simulation active.")
            else:
                print("Failed to start simulation.")

        except Exception as e:
            print(f"Simulation error: {e}")

        input("Press Enter to continue...")

    # ============================================================
    # SWEEP INTERFERENCE
    # ============================================================

    def sweep_simulation(self):
        try:
            start_freq = float(input("Start frequency MHz: "))
            end_freq = float(input("End frequency MHz: "))
            bandwidth = float(input("Bandwidth MHz (default 20): ") or "20")
            dwell = float(input("Dwell time seconds (default 2): ") or "2")

            self.stop_transmission()
            self.stop_flag = False

            thread = threading.Thread(
                target=self._sweep_worker,
                args=(start_freq, end_freq, bandwidth, dwell)
            )
            thread.daemon = True
            thread.start()

            print("Sweep simulation running.")

        except Exception as e:
            print(f"Sweep configuration error: {e}")

        input("Press Enter to continue...")

    def _sweep_worker(self, start, end, bandwidth, dwell):

        freq = start

        while not self.stop_flag:
            if self._start_transmission(freq, bandwidth, dwell):
                time.sleep(dwell)

            freq += bandwidth
            if freq > end:
                freq = start

    # ============================================================
    # RANDOM SIMULATION
    # ============================================================

    def random_simulation(self):
        try:
            start = float(input("Start frequency MHz: "))
            end = float(input("End frequency MHz: "))
            bandwidth = float(input("Bandwidth MHz (default 20): ") or "20")
            min_d = float(input("Min dwell seconds: ") or "1")
            max_d = float(input("Max dwell seconds: ") or "5")

            self.stop_transmission()
            self.stop_flag = False

            thread = threading.Thread(
                target=self._random_worker,
                args=(start, end, bandwidth, min_d, max_d)
            )
            thread.daemon = True
            thread.start()

            print("Random interference simulation running.")

        except Exception as e:
            print(f"Configuration error: {e}")

        input("Press Enter to continue...")

    def _random_worker(self, start, end, bandwidth, min_d, max_d):

        freqs = []
        current = start

        while current <= end:
            freqs.append(current)
            current += bandwidth

        while not self.stop_flag:
            freq = random.choice(freqs)
            dwell = random.uniform(min_d, max_d)

            if self._start_transmission(freq, bandwidth, dwell):
                time.sleep(dwell)

    # ============================================================
    # STOP TRANSMISSION
    # ============================================================

    def stop_transmission(self):

        self.stop_flag = True

        if self.transmit_process:
            self.transmit_process.terminate()

            try:
                self.transmit_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.transmit_process.kill()

            self.transmit_process = None

        subprocess.run(
            ["pkill", "-f", "hackrf_transfer"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        try:
            noise_file = Path(self.temp_dir) / "interference_noise.bin"
            if noise_file.exists():
                noise_file.unlink()
        except Exception:
            pass

        print("Simulation stopped.")
        time.sleep(1)

    def __del__(self):
        self.stop_transmission()
