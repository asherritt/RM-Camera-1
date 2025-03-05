from dotenv import load_dotenv
import os
import time
import logging
import json
from picamera2 import Picamera2
from datetime import datetime

# Load environment variables
load_dotenv()

VIDEO_DIR = os.getenv("VIDEO_DIR")
LOG_FILE = os.getenv("LOG_FILE")
COMMAND_FILE = "/tmp/camera_command.json"

# ✅ Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)

class CameraRecorder:
    def __init__(self):
        self.picam2 = Picamera2()

    def start_recording(self, duration):
        """Start video recording for the given duration."""
        timestamp = datetime.now().strftime("%m_%d_%Y_%H-%M-%S")
        tmp_video_file = os.path.join(VIDEO_DIR, f"tmp_GRD_{timestamp}.mp4")
        final_video_file = tmp_video_file.replace("tmp_", "", 1)

        logging.info(f"🎥 Starting recording: {tmp_video_file}")

        # Configure camera
        self.picam2.set_controls({"FrameRate": 24.0})
        config = self.picam2.create_video_configuration(main={"size": (2028, 1080)})
        self.picam2.configure(config)

        # Start recording
        self.picam2.start_and_record_video(tmp_video_file, duration=duration)

        # Rename file after recording
        os.rename(tmp_video_file, final_video_file)

        logging.info(f"✅ Recording complete. Saved as: {final_video_file}")

    def monitor_commands(self):
        """Continuously check for new recording commands."""
        logging.info("📡 Camera Recorder started, watching for commands...")

        while True:
            if os.path.exists(COMMAND_FILE):
                try:
                    with open(COMMAND_FILE, "r") as f:
                        command_data = json.load(f)

                    os.remove(COMMAND_FILE)  # Remove command file after reading
                    duration = command_data.get("duration", 900)  # Default 15 min

                    logging.info(f"🔹 New recording request: {command_data}")
                    self.start_recording(duration)

                except Exception as e:
                    logging.error(f"❌ Failed to process command: {e}")

            time.sleep(1)  # Check every second for new commands

# Start the camera recorder process
recorder = CameraRecorder()
recorder.monitor_commands()