import os
import time
import boto3
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Load environment variables
load_dotenv()

VIDEO_DIR = os.getenv("VIDEO_DIR")
BUCKET_NAME = os.getenv("BUCKET")

s3_client = boto3.client("s3")

def is_file_complete(file_path):
    """Check if the file is still being written."""
    try:
        with open(file_path, "rb") as f:
            f.seek(0, os.SEEK_END)  # Move to end of file
        return True
    except IOError:
        return False  # File is still being written

def upload_video(file_path):
    """Upload video to S3 and delete it locally after successful upload."""
    if not is_file_complete(file_path):
        print(f"⏳ Skipping {file_path}, still being written.")
        return

    file_name = os.path.basename(file_path)
    print(f"📤 Uploading {file_name} to S3...")

    try:
        s3_client.upload_file(file_path, BUCKET_NAME, file_name)
        print(f"✅ Upload complete: {file_name}")
        os.remove(file_path)  # Delete after successful upload
        print(f"🗑️ Deleted local file: {file_name}")
    except Exception as e:
        print(f"❌ Upload failed for {file_name}: {e}")

class VideoHandler(FileSystemEventHandler):
    """Watch for new videos and upload when they are complete."""
    def on_created(self, event):
        if event.is_directory:
            return

        time.sleep(5)  # Wait briefly to ensure the file is stable
        upload_video(event.src_path)

if __name__ == "__main__":
    print("🔍 Scanning for existing videos...")
    for file in os.listdir(VIDEO_DIR):
        if file.endswith(".mp4"):  # Adjust for your file format
            upload_video(os.path.join(VIDEO_DIR, file))

    print(f"👀 Watching {VIDEO_DIR} for new videos...")
    event_handler = VideoHandler()
    observer = Observer()
    observer.schedule(event_handler, VIDEO_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()