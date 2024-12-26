import os
import time
import subprocess
import logging

# Configuration
SCRIPT_PATH = "/path/to/rpi-power-auth-bayarea.py"  # Update with the actual path
CHECK_INTERVAL = 5  # Time in seconds to check if the script is running
LOG_FILE = "/var/log/rpi_script_monitor.log"

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def is_script_running(script_name):
    """Check if the script is currently running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.returncode == 0
    except Exception as e:
        logging.error(f"Error checking script status: {e}")
        return False

def start_script():
    """Start the script."""
    try:
        subprocess.Popen(["python3", SCRIPT_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logging.info("Script started successfully.")
    except Exception as e:
        logging.error(f"Failed to start script: {e}")

if __name__ == "__main__":
    logging.info("Monitoring script started.")

    while True:
        if not is_script_running(os.path.basename(SCRIPT_PATH)):
            logging.warning("Script not running. Attempting to restart.")
            start_script()
        else:
            logging.info("Script is running.")

        time.sleep(CHECK_INTERVAL)
