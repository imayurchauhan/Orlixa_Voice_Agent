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
            
            tts.speak("Thinking...")
            
            # Plan
            plan = planner.plan_task(command)
            if not plan:
                tts.speak("I'm sorry, I encountered an error while planning.")
                memory.log_command(command, "Error Planning")
                continue
            
            steps = plan.get("steps", [])
            chat_msg = plan.get("chat_response", "")
            
            # Speak chat response if present
            if chat_msg:
                tts.speak(chat_msg)
                
            # If no steps, we are done (it was just a conversation)
            if not steps:
                memory.log_command(command, "Conversational")
                continue
                
            # Parse & Validate Steps
            valid_steps = parser.parse_and_validate(steps)
            if not valid_steps:
                tts.speak("I'm sorry, the generated steps were invalid.")
                memory.log_command(command, "Invalid Steps")
                continue
                
            # Execute
            executor.execute_steps(valid_steps)
            memory.log_command(command, "Executed")

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
