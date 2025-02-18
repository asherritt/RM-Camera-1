from dotenv import load_dotenv
import os
import time
import boto3
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Load environment variables
load_dotenv()

os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("ACCESS_KEY")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("SECRET")
os.environ["AWS_DEFAULT_REGION"] = os.getenv("REGION")

# AWS S3 Configuration
S3_BUCKET = os.getenv("BUCKET")
S3_FOLDER = "videos/"  # S3 folder prefix
VIDEO_DIR = os.getenv("VIDEO_DIR")


# Initialize S3 Client (Ensure AWS credentials are configured)
s3_client = boto3.client("s3")

class VideoUploadHandler(FileSystemEventHandler):
    """Handles new files detected in the video directory."""
    
    def on_created(self, event):
        """Triggered when a new file is created in the directory."""
        if event.is_directory:
            return

        file_path = event.src_path
        if file_path.endswith(".mp4"):  # Only upload MP4 files
            print(f"🎥 New video detected: {file_path}")
            upload_and_delete(file_path)

def upload_and_delete(file_path):
    """Uploads a video to S3 and deletes it locally after success."""
    file_name = os.path.basename(file_path)
    s3_key = os.path.join(S3_FOLDER, file_name)

    try:
        print(f"📤 Uploading {file_name} to S3 bucket {S3_BUCKET}...")
        s3_client.upload_file(file_path, S3_BUCKET, s3_key)
        print(f"✅ Upload complete: {s3_key}")

        # Delete the local file after successful upload
        os.remove(file_path)
        print(f"🗑️ Deleted local file: {file_path}")

    except Exception as e:
        print(f"❌ Upload failed for {file_name}: {e}")

def scan_and_upload_existing():
    """Scans the video directory and uploads any leftover files."""
    print("🔍 Scanning for existing videos...")
    for file_name in os.listdir(VIDEO_DIR):
        file_path = os.path.join(VIDEO_DIR, file_name)
        if file_path.endswith(".mp4"):
            upload_and_delete(file_path)

def start_folder_watcher():
    """Starts the watchdog observer to monitor the folder."""
    observer = Observer()
    event_handler = VideoUploadHandler()
    observer.schedule(event_handler, VIDEO_DIR, recursive=False)
    observer.start()

    print(f"👀 Watching {VIDEO_DIR} for new videos...")
    
    try:
        while True:
            time.sleep(300)  # Sleep for 5 minutes, then check again
            scan_and_upload_existing()
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == "__main__":
    print(f"Starting Uploader")
    scan_and_upload_existing()  # Check for old videos on startup
    start_folder_watcher()  # Start watching for new videos