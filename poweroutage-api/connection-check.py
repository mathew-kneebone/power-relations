import os
import time
import subprocess
import socket

# Configuration
SCRIPT_TO_RUN = "/path/to/another_script.py"  # Replace with the path to your script
CHECK_INTERVAL = 5  # Time in seconds to wait between connection checks

def is_connected():
    """Check if the device is connected to the internet."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def prompt_wifi_credentials():
    """Prompt the user for Wi-Fi credentials."""
    print("\nYou are not connected to the internet.")
    print("Please provide your Wi-Fi network details to connect.")
    ssid = input("Enter Wi-Fi network name (SSID): ")
    password = input("Enter Wi-Fi password: ")

    try:
        # Use `nmcli` for Linux-based systems
        command = [
            "nmcli", "dev", "wifi", "connect", ssid, "password", password
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            print("Successfully connected to the Wi-Fi network.")
            return True
        else:
            print("Failed to connect to the Wi-Fi network. Error:")
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("Network connection utility 'nmcli' not found. Ensure it is installed.")
        return False

def ensure_internet_connection():
    """Ensure the Raspberry Pi is connected to the internet."""
    while not is_connected():
        success = prompt_wifi_credentials()
        if success:
            time.sleep(5)  # Wait for the connection to stabilize
        else:
            print("Retrying connection...")

if __name__ == "__main__":
    print("Checking internet connection...")
    ensure_internet_connection()
    print("Internet connection verified. Running the specified script...")

    try:
        subprocess.run(["python3", SCRIPT_TO_RUN])
    except Exception as e:
        print(f"Failed to run the script: {e}")
