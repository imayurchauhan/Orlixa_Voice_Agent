import time
import keyboard
import threading
import sys

from utils.logger import setup_logger
import config

# Setup global logger first
logger = setup_logger(config.LOG_FILE)

from voice.stt import SpeechToText
from voice.tts import TextToSpeech
from input.push_to_talk import PushToTalk
from input.text_input import TextInput
from planner.groq_client import GroqPlanner
from planner.task_parser import TaskParser
from executor.task_executor import TaskExecutor
from memory.memory_manager import MemoryManager

def main():
    logger.info(f"Starting {config.ASSISTANT_NAME} Voice Agent...")
    print(f"--- {config.ASSISTANT_NAME} AI Voice Assistant ---")

    try:
        # Initialize Memory
        memory = MemoryManager(config.DB_PATH)
        
        # Initialize Voice
        tts = TextToSpeech()
        stt = SpeechToText()
        
        # Initialize Input
        ptt = PushToTalk()
        text_input = TextInput()
        
        # Initialize Planner & Executor
        planner = GroqPlanner()
        parser = TaskParser()
        executor = TaskExecutor(tts)

        tts.speak(f"{config.ASSISTANT_NAME} is online and ready.")
        command_queue = []
        observation = None

        def text_input_thread():
            while True:
                cmd = text_input.get_input()
                if cmd:
                    command_queue.append(cmd)

        t = threading.Thread(target=text_input_thread, daemon=True)
        t.start()

        while True:
            print(f"\n[WAITING] Action: (1) Hold '{config.PUSH_KEY}' to talk (2) Type in console")
            command = None
            
            # Check queue first
            while not command:
                if command_queue:
                    command = command_queue.pop(0)
                else:
                    # Check for PUSH_KEY
                    if keyboard.is_pressed(config.PUSH_KEY):
                        print("\n[LISTENING] Recording audio...")
                        audio_file = ptt.record_audio()
                        if audio_file:
                            print("Transcribing...")
                            command = stt.transcribe(audio_file)
                            if command:
                                print(f"Transcribed: {command}")
                            else:
                                print("I couldn't hear any words. Try again.")
                                break # break inner loop to print waiting again
                        else:
                            print("\nRecording was too short or empty! Please hold the keys down while speaking.")
                            break # break inner loop to print waiting again
                    else:
                        time.sleep(0.05)
            
            if not command:
                continue

            logger.info(f"Received command: {command}")
            memory.log_command(command, "Received")
            
            # Always take a fresh look at the screen before planning
            observation = executor.get_current_observation()
            
            try:
                tts.speak("Thinking...")
            except:
                pass
            
            # Reasoning Loop
            MAX_LOOPS = 5
            last_action = None
            
            for loop_count in range(MAX_LOOPS):
                logger.info(f"Reasoning Loop {loop_count + 1}/{MAX_LOOPS}")
                
                # Plan
                plan = planner.plan_task(command, observation, last_action, turn=loop_count + 1)
                if not plan:
                    try:
                        tts.speak("I'm sorry, I encountered an error while planning.")
                    except:
                        pass
                    memory.log_command(command, "Error Planning")
                    break
                
                steps = plan.get("steps", [])
                chat_msg = plan.get("chat_response", "")
                
                # Speak chat response if present
                if chat_msg:
                    print(f"\n[ORLIXA] {chat_msg}")
                    try:
                        tts.speak(chat_msg)
                    except:
                        logger.error("TTS failed but continuing loop.")
                    
                # If reasoning exists, log it
                reasoning = plan.get("reasoning", "")
                if reasoning:
                    logger.info(f"AI Reasoning: {reasoning}")
                    print(f"[REASONING] {reasoning}")
                    
                # If no steps or status is Completed, we are done
                status = plan.get("status", "In Progress")
                if not steps or status == "Completed":
                    memory.log_command(command, "Completed")
                    break
                    
                # Parse & Validate Steps
                valid_steps = parser.parse_and_validate(steps)
                if not valid_steps:
                    try:
                        tts.speak("I'm sorry, the generated steps were invalid.")
                    except:
                        pass
                    memory.log_command(command, "Invalid Steps")
                    break
                    
                # Execute and get new observation
                observation = executor.execute_steps(valid_steps)
                
                # Record the last action taken for the next loop turn
                if valid_steps:
                    last_action = valid_steps[-1].get("action")
                
                memory.log_command(command, f"Executed")
                
                # DONE! Steps ran successfully. Stop the loop.
                # The user will give the next command manually.
                break

    except KeyboardInterrupt:
        logger.info("Application stopped by user (Ctrl+C).")
        print("\nShutting down...")
    except Exception as e:
        logger.error(f"Critical error in main loop: {e}")
    finally:
        try:
            executor.cleanup()
            memory.close()
        except:
            pass
        logger.info(f"{config.ASSISTANT_NAME} Voice Agent offline.")

if __name__ == "__main__":
    main()
