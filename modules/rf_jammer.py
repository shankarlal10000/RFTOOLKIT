import os
import subprocess
import signal
import time
import random
import sys
from pathlib import Path

class RFJammer:
    def __init__(self):
        self.jamming_process = None
        self.stop_jamming_flag = False
        self.temp_dir = self.get_temp_dir()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def get_temp_dir(self):
        """Get writable temporary directory"""
        temp_dirs = [
            '/tmp',
            str(Path.home() / '.rf_toolkit' / 'temp'),
            '/var/tmp'
        ]
        
        for temp_dir in temp_dirs:
            try:
                Path(temp_dir).mkdir(parents=True, exist_ok=True)
                # Test write
                test_file = Path(temp_dir) / 'write_test'
                test_file.write_text('test')
                test_file.unlink()
                print(f"Using temporary directory: {temp_dir}")
                return temp_dir
            except Exception:
                continue
        
        print("Warning: No writable temp directory found!")
        return '/tmp'
    
    def signal_handler(self, signum, frame):
        """Handle termination signals"""
        print("\nScript terminated")
        self.stop_jamming()
        sys.exit(0)
    
    def run(self):
        while True:
            os.system('clear')
            print("========================================")
            print("             RF JAMMING")
            print("========================================")
            print("1. Constant Jammer (Single Frequency)")
            print("2. Sweeping Jammer (Frequency Hopping)")
            print("3. Random Channel Hopping Jammer")
            print("4. Stop Current Jamming")
            print("5. Back to Main Menu")
            
            choice = input("\nEnter choice (1-5): ").strip()
            
            if choice == '1':
                self.constant_jammer()
            elif choice == '2':
                self.sweeping_jammer()
            elif choice == '3':
                self.random_hopping_jammer()
            elif choice == '4':
                self.stop_jamming()
            elif choice == '5':
                self.stop_jamming()
                return
            else:
                print("Invalid choice!")
                input("Press Enter to continue...")
    
    def generate_noise_file(self, size_mb=10):
        """Generate a noise file with random data"""
        noise_file = Path(self.temp_dir) / "jamming_noise.bin"
        size_bytes = size_mb * 1024 * 1024
        
        print(f"Generating {size_mb}MB noise file...")
        cmd = ['dd', 'if=/dev/urandom', f'of={noise_file}', f'bs=1M', f'count={size_mb}']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and noise_file.exists():
            print("Noise file generated successfully!")
            return str(noise_file)
        else:
            print("Failed to generate noise file!")
            return None
    
    def start_jamming_at_frequency(self, freq_mhz, bandwidth_mhz=28, duration=None):
        """Start jamming at a specific frequency"""
        try:
            noise_file = self.generate_noise_file()
            if not noise_file:
                return False
            
            cmd = [
                'hackrf_transfer', '-t', noise_file,
                '-f', f"{float(freq_mhz)*1e6}",
                '-s', '20000000',  # 20 MHz sample rate
                '-b', f"{float(bandwidth_mhz)*1e6}",
                '-x', '47',  # Max TX gain
                '-a', '1',   # Enable amplifier
                '-R'         # Repeat
            ]
            
            if duration:
                # Calculate number of samples for duration
                samples = int(float(duration) * 20000000)  # sample_rate * duration
                cmd.extend(['-n', str(samples)])
            
            print(f"Jamming at {freq_mhz} MHz with {bandwidth_mhz} MHz bandwidth")
            
            self.jamming_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Check if process started successfully
            time.sleep(0.5)
            if self.jamming_process.poll() is not None:
                return False
            
            return True
            
        except Exception as e:
            print(f"Jamming error: {e}")
            return False
    
    def constant_jammer(self):
        """Constant jammer - jams a single frequency continuously"""
        try:
            freq = input("Enter target frequency in MHz: ").strip()
            if not freq.replace('.', '').isdigit():
                print("Invalid frequency!")
                return
            
            bandwidth = input("Enter bandwidth in MHz (default 28, max 28): ").strip() or "28"
            
            # Validate bandwidth
            bw_float = float(bandwidth)
            if bw_float > 28:
                print(f"Warning: Maximum bandwidth is 28 MHz (reducing to 28 MHz)")
                bandwidth = "28"
            
            print(f"\nStarting constant jamming on {freq} MHz...")
            print(f"Bandwidth: {bandwidth} MHz (MAXIMUM)")
            print("Press Ctrl+C or option 4 to stop jamming")
            
            self.stop_jamming()
            
            if self.start_jamming_at_frequency(freq, bandwidth):
                print("Constant jamming started successfully!")
                print("HackRF LED should be active - transmitting noise")
            else:
                print("Failed to start constant jamming!")
            
        except Exception as e:
            print(f"Constant jamming error: {e}")
        
        input("Press Enter to continue...")
    
    def sweeping_jammer(self):
        """Sweeping jammer - hops through frequency bands"""
        try:
            print("Sweeping Jammer Configuration")
            print("=============================")
            
            start_freq = input("Enter start frequency in MHz (default 2400): ").strip() or "2400"
            end_freq = input("Enter end frequency in MHz (default 2500): ").strip() or "2500"
            bandwidth = input("Enter bandwidth per hop in MHz (default 28, max 28): ").strip() or "28"
            dwell_time = input("Enter dwell time per frequency in seconds (default 2): ").strip() or "2"
            
            start_f = float(start_freq)
            end_f = float(end_freq)
            dwell = float(dwell_time)
            bw = float(bandwidth)
            
            if start_f >= end_f:
                print("Error: Start frequency must be less than end frequency!")
                return
            
            if bw > 28:
                print("Warning: Reducing bandwidth to 28 MHz maximum")
                bw = 28
            
            # Calculate number of hops
            step = bw  # Step by bandwidth to avoid gaps
            num_hops = int((end_f - start_f) / step)
            
            print(f"\nSweeping Jammer Starting...")
            print(f"Frequency range: {start_f} - {end_f} MHz")
            print(f"Bandwidth per hop: {bw} MHz (MAXIMUM)")
            print(f"Dwell time: {dwell} seconds")
            print(f"Number of hops: {num_hops}")
            print("Press Ctrl+C to stop jamming")
            
            self.stop_jamming()
            self.stop_jamming_flag = False
            
            # Start sweeping in a separate thread
            import threading
            sweep_thread = threading.Thread(target=self._sweep_worker, 
                                          args=(start_f, end_f, bw, dwell))
            sweep_thread.daemon = True
            sweep_thread.start()
            
            print("Sweeping jammer started! It will run in the background.")
            print("Use option 4 to stop jamming.")
            
        except Exception as e:
            print(f"Sweeping jammer error: {e}")
        
        input("Press Enter to continue...")
    
    def _sweep_worker(self, start_freq, end_freq, bandwidth, dwell_time):
        """Worker function for sweeping jammer"""
        current_freq = start_freq
        step = bandwidth
        
        while not self.stop_jamming_flag and current_freq <= end_freq:
            print(f"Sweeping to {current_freq} MHz...")
            
            if self.start_jamming_at_frequency(current_freq, bandwidth, dwell_time):
                # Wait for the dwell time
                time.sleep(dwell_time)
            else:
                print(f"Failed to jam at {current_freq} MHz")
            
            # Move to next frequency
            current_freq += step
            
            # Stop if we've reached the end
            if current_freq > end_freq:
                current_freq = start_freq  # Restart sweep
        
        print("Sweeping jammer stopped.")
    
    def random_hopping_jammer(self):
        """Random channel hopping jammer - hops randomly between frequencies"""
        try:
            print("Random Channel Hopping Jammer Configuration")
            print("==========================================")
            
            start_freq = input("Enter start frequency in MHz (default 2400): ").strip() or "2400"
            end_freq = input("Enter end frequency in MHz (default 2500): ").strip() or "2500"
            bandwidth = input("Enter bandwidth per hop in MHz (default 28, max 28): ").strip() or "28"
            min_dwell = input("Enter minimum dwell time in seconds (default 1): ").strip() or "1"
            max_dwell = input("Enter maximum dwell time in seconds (default 5): ").strip() or "5"
            
            start_f = float(start_freq)
            end_f = float(end_freq)
            bw = float(bandwidth)
            min_d = float(min_dwell)
            max_d = float(max_dwell)
            
            if start_f >= end_f:
                print("Error: Start frequency must be less than end frequency!")
                return
            
            if bw > 28:
                print("Warning: Reducing bandwidth to 28 MHz maximum")
                bw = 28
            
            # Fix: Ensure max_dwell is greater than min_dwell
            if min_d > max_d:
                print("Warning: Minimum dwell time greater than maximum, swapping values")
                min_d, max_d = max_d, min_d
            elif min_d == max_d:
                # If they're equal, add some variation
                print("Warning: Dwell times are equal, adding 1 second to maximum")
                max_d = min_d + 1.0
            
            print(f"\nRandom Hopping Jammer Starting...")
            print(f"Frequency range: {start_f} - {end_f} MHz")
            print(f"Bandwidth per hop: {bw} MHz (MAXIMUM)")
            print(f"Dwell time: {min_d}-{max_d} seconds (random)")
            print("Press Ctrl+C to stop jamming")
            
            self.stop_jamming()
            self.stop_jamming_flag = False
            
            # Start random hopping in a separate thread
            import threading
            hop_thread = threading.Thread(target=self._random_hop_worker,
                                        args=(start_f, end_f, bw, min_d, max_d))
            hop_thread.daemon = True
            hop_thread.start()
            
            print("Random hopping jammer started! It will run in the background.")
            print("Use option 4 to stop jamming.")
            
        except Exception as e:
            print(f"Random hopping jammer error: {e}")
        
        input("Press Enter to continue...")
    
    def _random_hop_worker(self, start_freq, end_freq, bandwidth, min_dwell, max_dwell):
        """Worker function for random hopping jammer"""
        available_freqs = []
        current = start_freq
        
        # Generate available frequencies
        while current <= end_freq:
            available_freqs.append(current)
            current += bandwidth
        
        if not available_freqs:
            print("No frequencies available in the specified range!")
            return
        
        while not self.stop_jamming_flag:
            # Choose random frequency
            freq = random.choice(available_freqs)
            # Choose random dwell time
            dwell = random.uniform(min_dwell, max_dwell)
            
            print(f"Random hop to {freq} MHz for {dwell:.1f} seconds...")
            
            if self.start_jamming_at_frequency(freq, bandwidth, dwell):
                time.sleep(dwell)
            else:
                print(f"Failed to jam at {freq} MHz")
                # Short pause before retry
                time.sleep(0.5)
        
        print("Random hopping jammer stopped.")
    
    def stop_jamming(self):
        """Stop all jamming activities"""
        self.stop_jamming_flag = True
        
        if self.jamming_process:
            print("Stopping jamming process...")
            
            # Send SIGTERM
            self.jamming_process.terminate()
            
            # Wait for process to terminate
            try:
                self.jamming_process.wait(timeout=3)
                print("Jamming stopped successfully!")
            except subprocess.TimeoutExpired:
                # If process doesn't terminate, force kill it
                print("Process not responding, forcing termination...")
                self.jamming_process.kill()
                try:
                    self.jamming_process.wait(timeout=2)
                    print("Jamming force-stopped!")
                except subprocess.TimeoutExpired:
                    print("Warning: Could not terminate jamming process!")
            
            self.jamming_process = None
        
        # Additional cleanup - kill any remaining hackrf_transfer processes
        cleanup_cmd = ['pkill', '-f', 'hackrf_transfer']
        subprocess.run(cleanup_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Clean up noise file
        try:
            noise_file = Path(self.temp_dir) / "jamming_noise.bin"
            if noise_file.exists():
                noise_file.unlink()
        except:
            pass
        
        print("All jamming activities stopped!")
        time.sleep(1)
    
    def __del__(self):
        # Cleanup when object is destroyed
        self.stop_jamming()
