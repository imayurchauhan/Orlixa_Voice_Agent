from utils.logger import get_logger
from executor.desktop_actions import DesktopActions
from executor.browser_actions import BrowserActions
from safety.confirmation import SafetyConfirmation
import time

logger = get_logger()

class TaskExecutor:
    def __init__(self, tts_engine):
        self.desktop = DesktopActions()
        self.browser = BrowserActions()
        self.safety = SafetyConfirmation(tts_engine)
        self.tts = tts_engine

    def get_current_observation(self):
        """Returns the current state of the browser or desktop as an observation."""
        if self.browser.page and not self.browser.page.is_closed():
            return self.browser.get_page_content()
        return "Browser is not open. Desktop is active."

    def execute_steps(self, steps):
        logger.info(f"Executing {len(steps)} steps.")
        last_success = True
        
        for index, step in enumerate(steps):
            action = step.get("action")
            print(f"\n[EXECUTOR] Starting step {index+1}: {action}")
            logger.info(f"Executing step {index+1}: {action}")
            
            # Safety Check
            if self.safety.is_dangerous(action):
                if not self.safety.confirm(f"{action} action"):
                    logger.info(f"Action {action} aborted by user.")
                    if self.tts:
                        self.tts.speak("Action cancelled.")
                    last_success = False
                    break # Stop executing further steps if dangerous action is cancelled

            success, message = self._run_action(step)
            
            if success:
                logger.info(message)
                if self.tts:
                    try:
                        self.tts.speak("Done.")
                    except:
                        pass
            else:
                last_success = False
                logger.error(f"Step failed: {message}")
                print(f"[WARN] Step {index+1} failed: {message}. Auto-skipping...")
                # Auto-skip and continue with remaining steps
                continue

        logger.info("Execution flow finished.")
        
        # Capture observation for the next planning turn
        observation = ""
        if last_success:
            # If we were in browser, get page content
            if self.browser.page and not self.browser.page.is_closed():
                observation = self.browser.get_page_content()
            else:
                observation = "Action completed successfully."
        else:
            observation = f"The last action failed with message: {message}. Please try a different approach or inform the user."
            
        return observation

    def _run_action(self, step):
        action = step.get("action")
        
        try:
            if action == "open_app":
                return self.desktop.open_app(step.get("app"))
            elif action == "shutdown":
                return self.desktop.shutdown()
            elif action == "open_folder":
                return self.desktop.open_folder(step.get("path"))
            elif action == "type_text":
                return self.desktop.type_text(step.get("text"))
            elif action == "press_key":
                return self.desktop.press_key(step.get("key"))
            elif action == "hotkey":
                return self.desktop.hotkey(step.get("key"))
            elif action == "open_browser":
                return self.browser.open_browser(step.get("url"))
            elif action == "navigate":
                return self.browser.navigate(step.get("url"))
            elif action == "click":
                return self.browser.click(step.get("selector"))
            elif action == "type":
                return self.browser.type(step.get("selector"), step.get("text"))
            elif action == "send_message":
                return self.desktop.send_message(step.get("contact"), step.get("message"))
            else:
                return False, f"Unknown action: {action}"
        except Exception as e:
            logger.error(f"Error running action {action}: {e}")
            return False, f"Exception during execution: {e}"

    def _handle_failure(self):
        print("\n[ERROR RECOVERY] Step failed.")
        print("Type 'skip' to ignore and continue, or 'abort' to stop execution.")
        
        while True:
            try:
                response = input("Choice (skip/abort): ").strip().lower()
                if response in ['skip', 'abort']:
                    return response
                else:
                    print("Invalid choice. Please type 'skip' or 'abort'.")
            except KeyboardInterrupt:
                return "abort"
            except Exception as e:
                logger.error(f"Error during error recovery: {e}")
                return "abort"

    def cleanup(self):
        self.browser.close()
