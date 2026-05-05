from utils.logger import get_logger

logger = get_logger()

class SafetyConfirmation:
    def __init__(self, tts_engine):
        self.tts = tts_engine
        self.dangerous_actions = ["shutdown", "delete", "format"] # Basic list of dangerous keywords

    def is_dangerous(self, action_name):
        return any(danger in action_name.lower() for danger in self.dangerous_actions)

    def confirm(self, action_description):
        question = f"Warning: You are about to {action_description}. Do you want to proceed? Yes or No."
        logger.warning(f"Safety confirmation required for: {action_description}")
        
        if self.tts:
            self.tts.speak(question)
            
        print(f"\n[SAFETY SYSTEM] {question}")
        
        while True:
            try:
                response = input("Type 'Yes' or 'No': ").strip().lower()
                if response in ['yes', 'y']:
                    logger.info("User confirmed action.")
                    return True
                elif response in ['no', 'n']:
                    logger.info("User cancelled action.")
                    return False
                else:
                    print("Please type 'Yes' or 'No'.")
            except KeyboardInterrupt:
                return False
            except Exception as e:
                logger.error(f"Error during confirmation: {e}")
                return False
