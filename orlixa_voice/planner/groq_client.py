import requests
import json
import config
from utils.logger import get_logger

logger = get_logger()

class GroqPlanner:
    def __init__(self):
        self.api_key = config.GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def plan_task(self, user_command):
        if not self.api_key or self.api_key == "your_api_key_here":
            logger.error("Groq API key is missing or invalid.")
            return None
            
        system_prompt = """
        Convert the user command into a JSON array of step-by-step actions.

        Rules:
        - Output ONLY JSON array.
        - Each step must be atomic (one action only).
        - Do NOT skip steps.
        - Follow correct real-world order.
        - Choose steps based on task type (do not force same pattern for all tasks).

        Available actions:
        - open_app (app)
        - open_browser (url)
        - open_folder (path)
        - hotkey (key)
        - press_key (key)
        - type_text (text)
        - navigate (url)
        - click (selector)
        - type (selector, text)

        ---

        ### Task Handling:

        1. Browser Tasks (YouTube, Google, Gmail, etc.):
        - ALWAYS use "open_browser" (url). NEVER use "open_app chrome".
        - For Gmail, use URL: https://mail.google.com
        - For Search, use URL: https://www.google.com/search?q=query
        - click (selector) - Click buttons/links.
        - type (selector, text) - Type into specific fields.

        2. Run / System Commands:
        - hotkey win+r
        - type_text command
        - press_key enter

        3. File Operations:
        - open_folder
        - use hotkey ctrl+a if needed
        - press_key delete

        4. Typing Tasks:
        - open_app (notepad or relevant app)
        - type_text

        ---

        ### Important:
        - Do not use unnecessary steps
        - Do not assume anything is open
        - Adapt steps based on the user request

        ---

        ### Example 1:

        User: search for latest AI news on google

        [
        {"action": "open_browser", "url": "https://www.google.com/search?q=latest+AI+news"}
        ]

        ---

        ### Example 2:

        User: play shayad song on youtube

        [
        {"action": "open_browser", "url": "https://www.youtube.com/results?search_query=shayad+song"},
        {"action": "click", "selector": "ytd-video-renderer"},
        {"action": "click", "selector": "video"}
        ]

        ---

        ### Example 2:

        User: delete temp files

        [
        {"action": "hotkey", "key": "win+r"},
        {"action": "type_text", "text": "%temp%"},
        {"action": "press_key", "key": "enter"},
        {"action": "hotkey", "key": "ctrl+a"},
        {"action": "press_key", "key": "delete"}
        ]

        ---

        ### Example 3:

        User: open gmail in chrome

        [
        {"action": "open_browser", "url": "https://mail.google.com"}
        ]
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_command}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }

        try:
            logger.info("Sending request to Groq API...")
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            parsed_json = json.loads(content)
            
            steps = []
            chat_response = ""
            reasoning = ""
            
            # Robust Parsing Logic
            if isinstance(parsed_json, list):
                # Format: [{action: ...}, ...]
                steps = parsed_json
            elif isinstance(parsed_json, dict):
                # Check if the dictionary itself is a single action
                if "action" in parsed_json:
                    steps = [parsed_json]
                else:
                    # Format: {steps: [...], chat_response: "..."}
                    reasoning = parsed_json.get("reasoning", "")
                    # Fallback for common key names
                    steps = parsed_json.get("steps") or parsed_json.get("actions") or parsed_json.get("plan") or []
                    chat_response = parsed_json.get("chat_response") or parsed_json.get("message") or parsed_json.get("reply") or ""
                    
                    # If steps is still empty, check if any value in the dict is a list of dicts
                    if not steps:
                        for val in parsed_json.values():
                            if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                                steps = val
                                break
            
            # Final validation: Ensure steps is a list
            if not isinstance(steps, list):
                steps = []

            # Print for debugging
            if steps or chat_response:
                print("\n" + "="*50)
                print("ORLIXA RESPONSE:")
                print("="*50)
                if reasoning:
                    print(f"Reasoning: {reasoning}")
                if chat_response:
                    print(f"Chat: {chat_response}")
                if steps:
                    print(f"Steps: {json.dumps(steps, indent=2)}")
                print("="*50 + "\n")
            else:
                logger.warning(f"Could not extract steps or chat from: {content}")
                
            return {"steps": steps, "chat_response": chat_response}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error calling Groq: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Groq: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in GroqPlanner: {e}")
            return None
