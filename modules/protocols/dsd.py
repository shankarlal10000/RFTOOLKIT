import os
import subprocess
import threading
import time
import signal
import sys
import shutil
from pathlib import Path
import io 

class DSD:
    def __init__(self):
        #base dir for storing stuff
        self.base_dir = Path.home() / ".rf_toolkit" / "protocols" / "dsd"
        self.rx_tools_dir = self.base_dir / "rx_tools" 
        self.soapy_remote_dir = self.base_dir / "SoapyRemote"
        self.soapy_modules_path = Path('/usr/local/lib/SoapySDR/modules0.8')
        self.recordings_dir = self.base_dir / "recordings" # rec dir
        
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.recordings_dir.mkdir(exist_ok=True) #existence check
        
        #path for logs
        self.log_file_path = self.base_dir / "dsd_log.txt"
        self.log_file_handle = None

        # Process management
        self.pipeline_process = None    
        
        # state management
        self.monitoring = False
        self._dsd_output_pipe = None 
        
        # Config
        self.monitor_freq = "146.52" 
        self.rf_gain = "20"
        self.debug_mode = False #debug mode - also enables logging in /root/.rf_toolkit/protocols/dsd/dsd_log.txt
        self.playback_mode = "playback" # Options: "playback", "record", "both"
        
        # Graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
	#ctrcl+c handling
        if self.monitoring:
            print("\nCaught signal, stopping monitoring...")
            self.stop_monitoring()

    def run(self):
        #Main menu
        while True:
            os.system('clear')
            print("========================================")
            print("     DIGITAL SPEECH DECODER (DSD)")
            print("========================================")
            print("1. Start DSD Monitoring (Real-time)")
            print("2. Install/Update Dependencies (DSD + rx_tools)")
            print("3. Configure DSD Options")
            print("4. View Recordings")
            print("5. Toggle debugging + logging(/root/.rf_toolkit/protocols/dsd/dsd_log.txt)")
            print("6. Back to Protocols Menu")
            print("="*40)
            
            #checks binaries and displays status
            dsd_ok, rx_ok = self.check_binary_availability()
            install_status = ""
            if dsd_ok and rx_ok:
                install_status = "INSTALLED"
            elif not dsd_ok and not rx_ok:
                install_status = "MISSING"
            else:
                install_status = "PARTIAL"
                
            monitoring_status = "ACTIVE" if self.monitoring else "IDLE"
            
            #update debug status(god fucking damn that took an embarassing amount of time)
            debug_status = "ON (Logging Active)" if self.debug_mode else "OFF (No Logging)"
            
            print(f"Monitor Status: {monitoring_status}")
            print(f"Dependency Status: {install_status}")
            print(f"Frequency: {self.monitor_freq} MHz")
            print(f"Gain: {self.rf_gain}")
            print(f"Debug Mode: {debug_status}")
            print(f"Playback Mode: {self.playback_mode.upper()}") # Fily implemented! YIPPIE
            
            try:
                choice = input("\nEnter choice (1-6): ").strip()
                
                if choice == '1':
                    self.start_realtime_monitoring()
                elif choice == '2':
                    self.install_dependencies()
                elif choice == '3':
                    self.configure_dsd()
                elif choice == '4':
                    self.view_recordings()
                elif choice == '5':
                    self.debug_mode = not self.debug_mode
                    print(f"Debug mode and Logging set to {'ON' if self.debug_mode else 'OFF'}.")
                    input("Press Enter to continue...")
                elif choice == '6':
                    self.stop_monitoring()
                    return
                else:
                    print("Invalid choice!")
                    input("Press Enter to continue...")
                    
            except KeyboardInterrupt:
                print("\nReturning to menu...")
            except EOFError:
                print("\nEnd of input received, exiting...")
                return

    def check_binary_availability(self):
        #checks if dsdccx(NOTE: the package name is dsdcc, but the executable binary is dsdccx) and rx_fm are available in $PATH.
        dsd_ok = shutil.which('dsdccx') is not None
        rx_ok = shutil.which('rx_fm') is not None
        return dsd_ok, rx_ok

    def _clone_and_build(self, repo_url, repo_dir, step_title):
        #helper function for git stuff
        print(f"\n[{step_title}] Processing {repo_dir.name}...")
        
        if repo_dir.exists():
            print(f"Existing {repo_dir.name} directory found. Deleting and recloning to ensure a clean build.")
            shutil.rmtree(repo_dir)
            
        print(f"Cloning {repo_url}...")
        subprocess.run(['git', 'clone', '--branch', 'master', repo_url, str(repo_dir)], check=True)

        print("Building and installing...")
        build_dir = repo_dir / "build"
        
        if build_dir.exists():
            shutil.rmtree(build_dir)
        build_dir.mkdir()

        # Build steps
        subprocess.run(['cmake', '..'], cwd=build_dir, check=True)
        subprocess.run(['make'], cwd=build_dir, check=True)
        
        subprocess.run(['sudo', 'make', 'install'], cwd=build_dir, check=True)
        
        print(f"Successfully built and installed {repo_dir.name}.")
    
    def _cleanup_soapy_duplicates(self):
        #Remove soapysdr shit if was installed earlier - else faces duplicate errors
        soapy_remote_lib = self.soapy_modules_path / 'libremoteSupport.so'
        if soapy_remote_lib.exists():
            print(f"\nWARNING: Removing duplicate SoapyRemote library at {soapy_remote_lib}.")
            print("This prevents the [ERROR] SoapySDR::loadModule duplicate entry issue.")
            try:
                subprocess.run(['sudo', 'rm', str(soapy_remote_lib)], check=True)
                print("Removed successfully.")
            except subprocess.CalledProcessError:
                print("ERROR: Failed to remove duplicate library. Manual removal may be required.")
        else:
            print("\nNo duplicate SoapyRemote library found in local path.")

    def install_dependencies(self):
        #Install required deps
        print("Starting Dependency Installation...")
        
        #install apt-able stuff
	#NOTE: not sure we need allat, but oh well
        try:
            print("\n[STEP 1/5] Installing APT dependencies...")
            apt_deps = [
                'dsdcc', 'sox', 'alsa-utils', 'git', 'cmake', 
                'build-essential', 'libhackrf-dev', 'libusb-1.0-0-dev', 
                'libsoapysdr-dev', 'avahi-daemon', 'libavahi-client-dev'
            ]
            
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            install_cmd = ['sudo', 'apt', 'install', '-y'] + apt_deps
            subprocess.run(install_cmd, check=True)
            
            # rx_tools
            self._clone_and_build(
                repo_url="https://github.com/rxseger/rx_tools.git",
                repo_dir=self.rx_tools_dir,
                step_title="STEP 2/5"
            )
            
            # sloppyremote EDIT: huh?????
            self._clone_and_build(
                repo_url="https://github.com/pothosware/SoapyRemote.git",
                repo_dir=self.soapy_remote_dir,
                step_title="STEP 3/5"
            )
            
            # Clean up soapyremote duplicate
            self._cleanup_soapy_duplicates()
            
            #final step
            print("\n[STEP 5/5] Updating shared library cache...")
            subprocess.run(['sudo', 'ldconfig'], check=True)
            
            print("\nSUCCESS: All dependencies installed and checked.")
            dsd_ok, rx_ok = self.check_binary_availability()
            if dsd_ok and rx_ok:
                print("dsdccx and rx_fm are ready to use.")
            else:
                print("WARNING: dsdccx or rx_fm still not found in PATH. Check build logs for errors.")


        except subprocess.CalledProcessError as e:
            print(f"ERROR: A command failed with return code {e.returncode}.")
            print(f"Command: {' '.join(e.cmd)}")
            print("Installation failed!")
        except Exception as e:
            print(f"ERROR: An unexpected error occurred: {e}")
        
        input("Press Enter to continue...")


    def configure_dsd(self):
        #config menu for dsd stuff
        try:
            while True:
                os.system('clear')
                print("DSD Configuration")
                print("=================")
                print(f"1. Monitor Frequency (MHz): {self.monitor_freq}")
                print(f"2. RF Gain (VGA): {self.rf_gain} (0-47dB for rx_fm based on hackrf_transfer -x)") 
                print(f"3. Playback/Recording Mode: {self.playback_mode.upper()}")
                print("4. Back to DSD Menu")
                
                try:
                    choice = input("\nSelect option to configure (1-4): ").strip()
                    
                    if choice == '1':
                        freq = input(f"Enter frequency in MHz (current: {self.monitor_freq}): ").strip()
                        if freq:
                            try:
                                freq_float = float(freq)
                                if 1 <= freq_float <= 7250:
                                    self.monitor_freq = freq
                                else:
                                    print("Frequency range is typically 1-6000 MHz.")
                            except ValueError:
                                print("Invalid frequency format")
                            input("Press Enter to continue...")
                    
                    elif choice == '2':
                        gain = input(f"Enter RF gain (0-47, current: {self.rf_gain}): ").strip()
                        if gain:
                            try:
                                gain_int = int(gain)
                                if 0 <= gain_int <= 47:
                                    self.rf_gain = str(gain_int)
                                elif gain_int > 47:
                                    print("Value is too big, setting gain to 47")
                                    self.rf_gain = 47
                                else:
                                    print("Gain must be between 0-47")
                            except ValueError:
                                print("Invalid gain format")
                            input("Press Enter to continue...")

                    elif choice == '3':
                        print("\nPlayback options:")
                        print(" 1. Playback (Only audio output)")
                        print(" 2. Record (Only save to file)")
                        print(" 3. Both (Audio output and save to file)")
                        mode_choice = input(f"Enter choice (1-3, current: {self.playback_mode}): ").strip()
                        
                        if mode_choice == '1':
                            self.playback_mode = "playback"
                        elif mode_choice == '2':
                            self.playback_mode = "record"
                        elif mode_choice == '3':
                            self.playback_mode = "both"
                        else:
                            print("Invalid choice. Mode remains unchanged.")
                        input("Press Enter to continue...")
                            
                    elif choice == '4':
                        return
                    else:
                        print("Invalid choice!")
                        input("Press Enter to continue...")
                        
                except KeyboardInterrupt:
                    print("\nConfiguration cancelled")
                    return
                    
        except KeyboardInterrupt:
            print("\nConfiguration cancelled")
        except Exception as e:
            print(f"Configuration error: {e}")
            
    def _stream_dsd_output(self):
        #read stdout AND stderr stream from the pipeline, print and log it, if logging is enabled
        logging_active = self.debug_mode
        #Yes, i will spam with functions
        """
        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&#BBB#&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#BBBGGGGGB@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&#B#BBGP5PGB&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        &BBGGBB##&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&#BGGP55J?Y5GB#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        &B#BGPPGGGB##&@@@@@@@@@@@@@@@@@@@@@@@@@@@&BGBBGPYJJ?7?5G#B@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        @###BBGPPGGGBBB##&&&@@@@@@@@@@@@@@@@&&&#BG5G#5Y55YJ?7Y5B##@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        @@###BBBGGPPPGGBGBGGGGGBGGPP5PPYYJYPBBBGGBB&&BBBGBGPPGB###@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@##BGPPPP555PGB#B##GGGGP5YY5YYJ?JG#####GBBBBBBBBBBB&&#B#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@&#BGP55PGGBB###BB&&&&#BBBBGP5Y5G####B####BBGGGPPG###BB@@@@#G5YYY5G#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@@&#&#BGBBGP5Y5GGGB&&&&&&&##BPPGGGBBBB##########BBGB&&B&&5!^:::::::^!P@@@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@@@&#&&&#GP5PPPPPGGG#####&#BGGGGGGGGGPGGGGBBBB###BGPPGBP!:::^^::::::::Y@@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@@@@##&#GPGBBBGP5Y55G###&&#BGGGB####BGPPPPP5YYY5PGP5YY5J^:::::::::::::7&@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@@@@@##BGBBBP55YY5PGB###&&#GP5PB#&&&&&&#G5YPGGPY5PPP5YYJ~:::::::::::::7&@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@@@@@BGGPPPPPP5PB#GG#####&#G5YYG#&&&#B&&###&&Y5GPGGP555Y~:::::::::::::7&@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@@@@@GGP5PPBBBYP&@&&&@&####B5YYP#&#GY?5#####57JPGGGPPPP5!:::::::::::::7&@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@@@@&GGBBB#BGPY?5GGB#BGGB###G55PB##B5??JYYYJ?YPPPPPPPGG5~:::::::::::::7&@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@@@@@&GB##BGGP5J?JY55PGPG###G5JJYGB#GJJYYY55555PPGGGGGG5~:::::::::::::7&@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@@@@@@&BB##&#BGPP55PPBB5P##B5J?7JPB#GJ?JJJY5PPGB####BGPY~:::::::::::::7&@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@@@@@@@@#BBB####BBBGBBBG5P#GJJ???YGBYJYYY55PGB#####BG5JJ~:^^^:::::::::7&@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@@@@@@@@@&#BGPP###&##GGGGPGGYJJJJYYP5Y55YJJJ55PGGP5J?JJ?~^^^^^::::::::7&@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@@@@@@@@@@@@&#GPPPGGP5PPGGB#&BPGB##GGBGP55YYYJ???7~~!JY?~^^^^^::::::::7&@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@@@@@@@@@@@@@@#5YYY5GGGGBB###BGGB#BBBBBGGPJ!^::::::^^^7J~::^^:::::::::7&@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@@@@@@@@@@@@@@#55Y???Y5PGBBBBBBBBB####G5J!^:::::::^^^^^7~^^^::::::::::7&@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@@@@@@@@@@@@@@@G555?7!~~!77?J5GBBBGPJ?!~^^::^:::::::^^^:^:^:::::::::^:7@@@@@@@@@@@@@@@@@@@@@@@@@@
        @@@@@@@@@@@@@@@@@@BPG55PJ7~^^:::^^~~~^^::::::^:::::::::::^:::::::::::::::7&#P5YJYYPG#@@@@@@@@@@@@@@@
        @@@@@@@@@@@@@@@@@@#55PBBPYYJ7~^^^^^::::::^~~^^:::::::::::::::::::::::::^:~!^:::::::^~7P@@@@@@@@@@@@@
        @@@@@@@@@@@@@@@@@@#PG#&#GPGBP5Y?!~^^^^^^^~77~^:::::::::::::::::::::::::::::::::::::^:::?&#P555PB&@@@
        @@@@@@@@@@@@@@@@@@#PGB#&BGB&&&#BP?^^^^^^^~!7~^::::::::::::::::::::::::::::::::::::::::::!^:::::^~?G@
        @@@@@@@@@@@@@@@@@@&GGBB####&&&##G!^^^^^^:~!!~^::::::::::::::::::::::::::::::::::::::::::::::::::::^J
        @@@@@@@@@@@@@@@@@@@BPBGBB#&#####J^::^^^^:~!!~:::::::::::::::::::::::::::::::::::::::::::::::::::^^::
        @@@@@@@@@@@@@@@@@@@&GGGGGB#&&&@P^:::::::^~77~:::::::::::::::::::::::::::::::::::::::::::::::::::::::
        @@@@@@@@@@@@@@@@@@@@&BGGGB#&&&G~::::::::^~77~:::::::::::::::::::::::::::::::::::::::::::::::::::::::
        @@@@@@@@@@@@@@@@@@@@@@#BGGB#&&?:^^::::::^~77~:::::::::::::::::::::::::::::::::::::::::::::::::::::::
        @@@@@@@@@@@@@@@@@@@@@#G5Y5PB##!:^:::::::^~77~:::::::::::::::::::::::::::::::::::::::::::::::::::::::
        @@@@@@@@@@@@@@@@@@@G7~~7??5GPG?:::::::::^~77~:::::::::::::::::::::::::::::::::::::::::::::::::::::::
        @@@@@@@@@@@@@@@@@@#!^^~~!7J5PGP!::::::::^~!!~:::::::::::::::::::::::::::::::::::::::::::::::::::::::
        @@@@@@@@@@@@@@@@@@#7!~~!??5GGGPY!::::::::^^^^::::::::::::::::::::::::::::::::::::::::::::::::::::::!
        @@@@@@@@@@@@@@@@@@@&#BBBBBBBBBB#P!::^:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::^P
        @@@@@@@@@@@@@@@@@@@@@@@@@@&#BGPPGGJ^::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::J@
        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&#GBP!::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::?&@
        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#B#&P!::::::::::::::::::::::::::::::::::::::::::::::::::::::::^Y@@@
        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&&@@&5!:::::::::::::::::::::::::::::::::::::::::::::::::::::7B@@@@
        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&P7^:::::::::::::::::::::::::::::::::::::::::::::::^7G@@@@@@
        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@BJ~::::::::::::::::::::::::::::::::::::::::::^!YB@@@@@@@@
        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&P?~:::::::::::::::::::::::::::::::::::^~75B@@@@@@@@@@@
        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&GY7~^^:::::::::::::::::::::::^~!?YPB&@@@@@@@@@@@@@@
        @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&#G5J?7!~~~~~~~~~~!!7?JY5GB#&@@@@@@@@@@@@@@@@@@@
        """
        if logging_active:
            try:
                self.log_file_handle = open(self.log_file_path, 'a', encoding='utf-8')
                self.log_file_handle.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- NEW DSD MONITORING SESSION STARTED ---\n")
                self.log_file_handle.write(f"Frequency: {self.monitor_freq} MHz, Gain: {self.rf_gain}, Mode: {self.playback_mode}\n")
            except Exception as e:
                print(f"WARNING: Failed to open log file {self.log_file_path}: {e}")
                logging_active = False 
        
        if self._dsd_output_pipe:
            print(f"--- Pipeline Traffic/Debug Output (Reader: {threading.current_thread().name}) ---")
            print(f"Debug thread started, reading from fd {self._dsd_output_pipe.fileno()}")
            if logging_active:
                print(f"Logging all output to: {self.log_file_path}")

            pipe_stream = io.TextIOWrapper(self._dsd_output_pipe, encoding='utf-8', errors='ignore')

            try:
                while self.monitoring:
                    line = pipe_stream.readline()
                    if not line:
                        time.sleep(0.05) 
                        continue
                        
                    line_str = line.strip()
                    
                    if line_str:
                        # LOGGING: Write the raw stuff to a file
                        if logging_active and self.log_file_handle:
                            self.log_file_handle.write(f"[{time.strftime('%H:%M:%S.%f')[:-3]}] {line_str}\n")
                            self.log_file_handle.flush() 

                        #output into console only if debugging is on
                        if self.debug_mode:
                            # DSD traffic
                            if any(key in line_str for key in ['DMR', 'D-STAR', 'YSF', 'NXDN', 'dPMR', 'sync:']):
                                print(f"\033[94mDSD: {line_str}\033[0m") 
                            # Debug Output
                            #only place where coloring is actually needed
                            else:
                                if not any(noise in line_str for noise in ['ALSA lib', 'PulseAudio:', 'RtApi::', 'avahi_service_browser']):
                                    if any(key in line_str for key in ['INFO', 'HackRF', 'Tuned to', 'Oversampling']):
                                        print(f"\033[35mRX_DEBUG: {line_str}\033[0m") 
                                    elif 'DSD' in line_str or 'Decoder' in line_str or 'sync' in line_str:
                                        print(f"\033[36mDSD_DEBUG: {line_str}\033[0m") 
                                    else:
                                        print(f"\033[33mPIPE_DEBUG: {line_str}\033[0m") 
                        
            except Exception as e:
                if self.monitoring: 
                    print(f"\033[91mPipeline output thread error: {e}\033[0m")
            finally:
                if self._dsd_output_pipe:
                    print("Pipeline traffic stream stopped.")
                
                #handling of log file closing
                if self.log_file_handle:
                    self.log_file_handle.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- MONITORING SESSION ENDED ---\n")
                    self.log_file_handle.close()
                    self.log_file_handle = None


    def start_realtime_monitoring(self):
        #actually start the god damn DSD monitoring and optionally recording.
        if self.monitoring:
            print("DSD monitoring is already running!")
            input("Press Enter to continue...")
            return
        
        dsd_ok, rx_ok = self.check_binary_availability()
        if not dsd_ok or not rx_ok:
            print("ERROR: dsdccx or rx_fm not found! Please install dependencies (option 2)")
            input("Press Enter to continue...")
            return
            
        print(f"Starting DSD Monitoring on {self.monitor_freq} MHz...")
        
        #pipeline building EDIT: fixed random bullshit NOTE: it doesnt work smh?????? EDIT: fixed, fr this time
        freq_hz = int(float(self.monitor_freq) * 1e6)
        
        #sdr capture
        rx_fm_cmd = f"rx_fm -f {freq_hz} -s 48000 -g {self.rf_gain} -"
        
        #dsd decode EDIT: this shit doesnt work NOTE: i am a fucking bafoon
        dsd_cmd = "dsdccx -i - -o - -fa -e" #dsd sends decoded stuff from rx_fm to stdout
        
        #output
        audio_output_cmd = ""
        pipeline_description = f"rx_fm (HackRF) -> dsdccx (Decode)"
        
        use_process_substitution = False
        
        if self.playback_mode == "playback":
            #Look at me not realising how nut crushing this will be
            #playback only: decoded audio to aplay
            #Edit - doesnt work, why???? NOTE - pulseaudio is a bitch, fixed later on
            audio_output_cmd = "aplay -r 8000 -f S16_LE -t raw - 2>/dev/null"
            pipeline_description += " -> aplay (Audio)"
            
        elif self.playback_mode == "record":
            # Recording only: decoded audio to sox file save
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            recording_filename = self.recordings_dir / f"{timestamp}_{self.monitor_freq}MHz_DSD.wav"
            #sox reads raw s16_le audio at 8kHz from stdin, and writes into WAV file
            audio_output_cmd = f"sox -t raw -r 8000 -e signed-integer -b 16 -c 1 - {recording_filename} 2>/dev/null"
            pipeline_description += f" -> sox (Record to {recording_filename.name})"
            print(f"Recording audio to: {recording_filename.resolve()}")

        elif self.playback_mode == "both":
            #both: decoded audio -> tee -> aplay + sox file save EDIT: shit has happened
            #NOTE: requires process substitution
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            recording_filename = self.recordings_dir / f"{timestamp}_{self.monitor_freq}MHz_DSD.wav"
            # tee duplicates the stream: one goes to aplay, the other to sox
            audio_output_cmd = f"tee >(aplay -r 8000 -f S16_LE -t raw - 2>/dev/null) | sox -t raw -r 8000 -e signed-integer -b 16 -c 1 - {recording_filename} 2>/dev/null"
            pipeline_description += f" -> tee -> aplay/sox (Audio + Record to {recording_filename.name})"
            print(f"Recording audio to: {recording_filename.resolve()} and playing back.")
            use_process_substitution = True #trigger the bash wrapper
        
        #pipeline command base
        core_pipeline_cmd = f"{rx_fm_cmd} | {dsd_cmd} | {audio_output_cmd}"
        
        # FIX: wrapped the command in 'bash -c' if process substitution is used
        if use_process_substitution:
            full_pipeline_cmd = f'bash -c "{core_pipeline_cmd}"'
            print("NOTE: Using 'bash -c' to support simultaneous record/playback via `tee`.")
        else:
            full_pipeline_cmd = f"({core_pipeline_cmd})"
        # wanted to comment something and forgot 
        print(f"Pipeline: {pipeline_description}")
        print("NOTE: Audio output errors (PulseAudio/ALSA) are ignored for pipeline stability.")
        print("-" * 50)
        
        self.stop_monitoring()
        time.sleep(0.5)
        
        try:
            #execute the command chain in a shell (either /bin/sh or the bash wrapper)
            self.pipeline_process = subprocess.Popen(
                full_pipeline_cmd,
                shell=True,             
                stdout=subprocess.PIPE,     #captures the stdout
                stderr=subprocess.STDOUT,   #merges stderr into stdout
                preexec_fn=os.setsid
            )
            
            self._dsd_output_pipe = self.pipeline_process.stdout
            
            self.monitoring = True
            
            #a thread to show DSD and debug output with name
            self._monitor_thread = threading.Thread(
                target=self._stream_dsd_output, 
                daemon=True,
                name="DSD_OutputReader"
            )
            self._monitor_thread.start()

            time.sleep(1)
            
            print("Monitoring started successfully! Press Ctrl+C to stop.")

            while self.pipeline_process.poll() is None and self.monitoring:
                time.sleep(1)
                
            if self.pipeline_process and self.pipeline_process.returncode not in [None, 0, -signal.SIGINT]:
                print(f"WARNING: Pipeline exited with return code {self.pipeline_process.returncode}.")


        except KeyboardInterrupt:
            print("\nMonitoring interrupted. Returning to menu...")
        except Exception as e:
            print(f"Error during monitoring: {e}")
        finally:
            self.stop_monitoring()

    def stop_monitoring(self):
        #Stop all monitoring processes and clean up EDIT: AGGRESIVLY
        if not self.monitoring and not self.pipeline_process:
            return
        
        print("Stopping monitoring processes...")
        
        self.monitoring = False
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            time.sleep(0.5)
            
        if self.pipeline_process and self.pipeline_process.poll() is None:
            try:
                pgid = os.getpgid(self.pipeline_process.pid)
                #SIGTERM first for graceful exit
                os.killpg(pgid, signal.SIGTERM)
                self.pipeline_process.wait(timeout=2)
            except Exception:
                try:
                    #SIGKILL to kill the remaining
                    os.killpg(pgid, signal.SIGKILL)
                    self.pipeline_process.wait(timeout=1)
                except Exception as e:
                    if self.debug_mode:
                        print(f"Failed to kill process group {pgid}: {e}")
                    pass
        
        if self._dsd_output_pipe:
            self._dsd_output_pipe.close()
            
        self.pipeline_process = None
        self._dsd_output_pipe = None
        
        # Close the log file
        if self.log_file_handle:
            self.log_file_handle.close()
            self.log_file_handle = None

        print("All processes stopped.")

    def view_recordings(self):
        #View recorded files
        os.system('clear')
        print("Recording Directory Contents")
        print("=============================")
        
        try:
            recordings = sorted(
                [f.name for f in self.recordings_dir.iterdir() if f.is_file()],
                reverse=True
            )
            
            if recordings:
                print(f"Location: {self.recordings_dir.resolve()}")
                print("-" * 25)
                for i, filename in enumerate(recordings):
                    print(f"{i+1:02}. {filename}")
            else:
                print("No recorded audio files found.")
                
        except Exception as e:
            print(f"ERROR: Could not read recordings directory: {e}")
        
        input("\nPress Enter to continue...")
