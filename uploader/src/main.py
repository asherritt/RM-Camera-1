from dotenv import load_dotenv
import os
import time
import boto3
import botocore
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Load environment variables
load_dotenv()

LOG_FILE = os.getenv("LOG_FILE")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)

VIDEO_DIR = os.getenv("VIDEO_DIR")
BUCKET_NAME = os.getenv("BUCKET")

s3_client = boto3.client("s3")

def is_file_complete(file_path):
    """Check if the file is still being written."""
    if os.path.basename(file_path).startswith("tmp_"):
        return False  # Skip temporary files
    
    try:
        with open(file_path, "rb") as f:
            f.seek(0, os.SEEK_END)  # Move to end of file
        return True
    except IOError:
        logging.error(f"IOError while checking file: {file_path}")
        return False  # File is still being written

def upload_video(file_path, retries=3):
    """Upload video to S3 and delete it locally after successful upload."""
    file_name = os.path.basename(file_path)
    logging.info(f"📤 Uploading {file_name} to S3...")

    for attempt in range(retries):
        try:
            s3_client.upload_file(file_path, BUCKET_NAME, file_name)
            logging.info(f"✅ Upload complete: {file_name}")
            os.remove(file_path)  # Delete after successful upload
            logging.info(f"🗑️ Deleted local file: {file_name}")
            return
        except botocore.exceptions.BotoCoreError as e:
            logging.info(f"❌ Upload failed for {file_name} (attempt {attempt+1}/{retries}): {e}")
            time.sleep(5)  # Wait before retrying

    logging.info(f"⚠️ Upload permanently failed after {retries} attempts: {file_name}")

class VideoHandler(FileSystemEventHandler):
    """Watch for new videos and upload when they are complete."""
    def on_modified(self, event):
        if event.is_directory or event.src_path.startswith("tmp_"):
            return  # Ignore directories and temporary files

        file_path = event.src_path
        logging.info(f"📁 New file detected: {file_path}")

        # Wait until file is stable before uploading
        while not is_file_complete(file_path):
            print(f"⏳ Waiting for {file_path} to finish writing...")
            time.sleep(10)  # Adjust sleep interval as needed

        upload_video(file_path)

if __name__ == "__main__":
    logging.info("🔍 Scanning for existing videos...")
    for file in os.listdir(VIDEO_DIR):
        if file.endswith(".mp4") and not file.startswith("tmp_"):
            upload_video(os.path.join(VIDEO_DIR, file))

    logging.info(f"👀 Watching {VIDEO_DIR} for new videos...")
    event_handler = VideoHandler()
    observer = Observer()
    observer.schedule(event_handler, VIDEO_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()