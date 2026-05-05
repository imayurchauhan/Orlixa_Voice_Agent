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

    def execute_steps(self, steps):
        logger.info(f"Executing {len(steps)} steps.")
        
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
                    break # Stop executing further steps if dangerous action is cancelled

            success, message = self._run_action(step)
            
            if success:
                logger.info(message)
                if self.tts:
                    self.tts.speak("Done.")
            else:
                logger.error(f"Step failed: {message}")
                if self.tts:
                    self.tts.speak(f"Error occurred: {message}. What should I do?")
                
                # Wait & Resume logic
                action_to_take = self._handle_failure()
                if action_to_take == "skip":
                    logger.info("Skipping failed step and continuing.")
                    continue
                elif action_to_take == "abort":
                    logger.info("Aborting remaining steps.")
                    break
                else:
                    logger.info("Aborting by default.")
                    break

        logger.info("Execution flow finished.")

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
                return self.browser.type_text(step.get("selector"), step.get("text"))
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
