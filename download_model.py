from huggingface_hub import snapshot_download
import sys

print("Starting explicit download of the Whisper 'small' model...")
print("You should see progress bars below:")

try:
    path = snapshot_download(
        repo_id="Systran/faster-whisper-small",
        local_files_only=False,
    )
    print(f"\nDownload fully complete! Model saved at: {path}")
except Exception as e:
    print(f"\nError downloading model: {e}")
    sys.exit(1)
