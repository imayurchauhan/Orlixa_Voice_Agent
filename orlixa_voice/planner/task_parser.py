from utils.logger import get_logger

logger = get_logger()

class TaskParser:
    def __init__(self):
        self.valid_actions = {
            "open_app": ["app"],
            "shutdown": [],
            "open_folder": ["path"],
            "type_text": ["text"],
            "press_key": ["key"],
            "hotkey": ["key"],
            "open_browser": ["url"],
            "navigate": ["url"],
            "click": ["selector"],
            "type": ["selector", "text"],
            "send_message": ["contact", "message"]
        }

    def parse_and_validate(self, steps):
        if not steps or not isinstance(steps, list):
            logger.error("Invalid steps format: expected a list.")
            return []

        validated_steps = []
        for index, step in enumerate(steps):
            if not isinstance(step, dict):
                logger.error(f"Step {index} is not a dictionary: {step}")
                continue
                
            action = step.get("action")
            if not action or action not in self.valid_actions:
                logger.error(f"Invalid or missing action in step {index}: {step}")
                continue

            required_fields = self.valid_actions[action]
            missing_fields = [field for field in required_fields if field not in step]
            
            if missing_fields:
                logger.error(f"Step {index} missing fields {missing_fields} for action '{action}'")
                continue

            validated_steps.append(step)

        if not validated_steps:
            logger.warning("No valid steps found after parsing.")
            
        return validated_steps
