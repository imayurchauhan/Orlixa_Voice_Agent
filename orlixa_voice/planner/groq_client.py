import requests
import json
import config
from utils.logger import get_logger

logger = get_logger()

class GroqPlanner:
    def __init__(self):
        self.api_key = config.GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def plan_task(self, user_command, observation=None, last_action=None, turn=1):
        if not self.api_key or self.api_key == "your_api_key_here":
            logger.error("Groq API key is missing or invalid.")
            return None
            
        system_prompt = f"""You are Orlixa, an AI task planner. Convert user commands into JSON action steps.

Current Observation: {observation if observation else "None"}
Last Action: {last_action if last_action else "None"}

IMPORTANT: Parameters must be FLAT on each step object. Do NOT nest them under "params".

Available actions and their REQUIRED flat parameters:
- open_browser: "url" (string) - Opens a website
- navigate: "url" (string) - Go to URL in existing browser
- click: "selector" (string) - Click element (use "text=LinkText" or CSS like "[name='q']")  
- type: "selector" (string), "text" (string) - Type in a field. Google search box selector is "[name='q']"
- open_app: "app" (string) - Open a Windows app (e.g. "chrome", "notepad", "code")
- type_text: "text" (string) - Type text into active window
- press_key: "key" (string) - Press key like "enter", "esc", "tab"

RULES:
1. ALWAYS prefer using open_browser with a DIRECT URL that includes the search query:
   - Google: "https://www.google.com/search?q=YOUR+QUERY"
   - YouTube: "https://www.youtube.com/results?search_query=YOUR+QUERY"
   - Wikipedia: "https://en.wikipedia.org/wiki/YOUR_QUERY"
2. Do NOT use open_app for browsers. Use open_browser instead - it handles everything.
3. Parameters must be FLAT. CORRECT: {{"action":"open_browser","url":"..."}}. WRONG: {{"action":"open_browser","params":{{"url":"..."}}}}
4. Return this JSON format:

{{"reasoning":"...","status":"In Progress","chat_response":"...","steps":[...]}}

Example 1 - Google Search:
User: "search for latest news"
{{"reasoning":"Searching Google","status":"In Progress","chat_response":"Searching for latest news...","steps":[{{"action":"open_browser","url":"https://www.google.com/search?q=latest+news"}}]}}

Example 2 - YouTube:
User: "play naal nachna song on youtube"
{{"reasoning":"Searching YouTube for the song","status":"In Progress","chat_response":"Searching YouTube for naal nachna...","steps":[{{"action":"open_browser","url":"https://www.youtube.com/results?search_query=naal+nachna"}}]}}

Example 3 - Open app:
User: "open notepad"
{{"reasoning":"Opening notepad","status":"In Progress","chat_response":"Opening Notepad...","steps":[{{"action":"open_app","app":"notepad"}}]}}

Example 4 - Click:
User: "click the first link"
{{"reasoning":"Clicking first result","status":"In Progress","chat_response":"Clicking...","steps":[{{"action":"click","selector":"h3"}}]}}"""
        
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
            print(f"\n[DEBUG] Raw Groq Response:\n{content}\n")
            
            # Extract JSON if it's wrapped in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
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
                    status = parsed_json.get("status", "In Progress")
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
                if status:
                    print(f"Status: {status}")
                if chat_response:
                    print(f"Chat: {chat_response}")
                if steps:
                    print(f"Steps: {json.dumps(steps, indent=2)}")
                print("="*50 + "\n")
            else:
                logger.warning(f"Could not extract steps or chat from: {content}")
                
            return {"steps": steps, "chat_response": chat_response, "status": status}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error calling Groq: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Groq: {e}")
            print(f"Content that failed to parse: {content}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in GroqPlanner: {e}")
            return None
