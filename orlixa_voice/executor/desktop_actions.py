import subprocess
import pyautogui
import os
import time
from utils.logger import get_logger

logger = get_logger()

class DesktopActions:
    def open_app(self, app_name):
        try:
            print(f"[DESKTOP] Attempting to launch app: {app_name}")
            logger.info(f"Attempting to open {app_name}...")
            
            # 1. Try 'start' command first (fastest and most robust for registered apps)
            # We use shell=True and 'start' to let Windows handle the application lookup
            try:
                subprocess.run(f"start {app_name}", shell=True, check=True, capture_output=True)
                return True, f"Successfully opened {app_name} via system shell."
            except Exception:
                logger.warning(f"'start' command failed for {app_name}. Falling back to Search method.")

            # 2. Fallback to Windows Search (pyautogui)
            # Press Windows key
            pyautogui.press('win')
            time.sleep(0.5)
            # Type the app name
            pyautogui.typewrite(app_name, interval=0.05)
            time.sleep(1.5) # Wait for search results to populate
            # Press Enter to open the best match
            pyautogui.press('enter')
            time.sleep(2) # Give it a moment to open
            return True, f"Requested to open {app_name} via Windows Search."
            
        except Exception as e:
            logger.error(f"Unexpected error opening app {app_name}: {e}")
            return False, f"Unexpected error: {e}"

    def shutdown(self):
        try:
            logger.info("Initiating system shutdown.")
            # /s = shutdown, /t 60 = 60 seconds delay
            subprocess.run(["shutdown", "/s", "/t", "60"], check=True)
            return True, "Shutdown initiated. System will power off in 60 seconds."
        except Exception as e:
            logger.error(f"Failed to initiate shutdown: {e}")
            return False, f"Failed to shutdown: {e}"

    def open_folder(self, path):
        try:
            logger.info(f"Opening folder: {path}")
            # Ensure path exists or is a standard windows path format
            normalized_path = os.path.normpath(path)
            
            # Using os.startfile is more robust on Windows as it uses the shell 
            # and doesn't care about the explorer.exe exit codes which can be misleading.
            os.startfile(normalized_path)
            
            return True, f"Successfully opened folder {path}"
        except Exception as e:
            logger.error(f"Failed to open folder {path}: {e}")
            return False, f"Failed to open folder: {e}"

    def type_text(self, text):
        try:
            logger.info(f"Typing text: {text}")
            pyautogui.typewrite(text, interval=0.05)
            return True, f"Successfully typed text."
        except Exception as e:
            logger.error(f"Failed to type text: {e}")
            return False, f"Failed to type text: {e}"

    def press_key(self, key):
        try:
            # Check if it's a combination like 'win+r' or 'ctrl+c'
            if '+' in key:
                return self.hotkey(key)
                
            logger.info(f"Pressing key: {key}")
            pyautogui.press(key)
            return True, f"Successfully pressed key {key}"
        except Exception as e:
            logger.error(f"Failed to press key {key}: {e}")
            return False, f"Failed to press key: {e}"

    def hotkey(self, combo):
        try:
            logger.info(f"Pressing hotkey combination: {combo}")
            keys = [k.strip() for k in combo.split('+')]
            pyautogui.hotkey(*keys)
            return True, f"Successfully pressed hotkey {combo}"
        except Exception as e:
            logger.error(f"Failed to press hotkey {combo}: {e}")
            return False, f"Failed to press hotkey: {e}"

    def send_message(self, contact, message):
        try:
            logger.info(f"Sending desktop message to {contact}")
            # Ensure the app is in focus (the previous step usually opens it, but let's wait a moment)
            time.sleep(1)
            
            # Ctrl+F to focus the search bar in WhatsApp Desktop
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(0.5)
            
            # Type contact name
            pyautogui.typewrite(contact, interval=0.05)
            time.sleep(1.5) # Wait for results
            
            # Press enter to select the contact
            pyautogui.press('enter')
            time.sleep(1)
            
            # Type the message
            pyautogui.typewrite(message, interval=0.05)
            time.sleep(0.5)
            
            # Press enter to send
            pyautogui.press('enter')
            
            return True, f"Sent message to {contact} via Desktop App"
        except Exception as e:
            logger.error(f"Failed to send desktop message: {e}")
            return False, f"Failed to send message: {e}"
