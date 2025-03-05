from dotenv import load_dotenv
import os
import logging
import paho.mqtt.client as mqtt
from picamera2 import Picamera2
from datetime import datetime, timedelta
import json
import threading  # 🚀 For non-blocking recording

# Load environment variables
load_dotenv()

BROKER_IP = os.getenv("BROKER_IP")
GARDEN_TOPIC = "motion/garden"
LOG_FILE = os.getenv("LOG_FILE")
VIDEO_DIR = os.getenv("VIDEO_DIR")
RECORD_DURATION = int(os.getenv("RECORD_DURATION", "900"))  # Default 15 min

# ✅ Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)

class MotionRecorder:
    def __init__(self):
        self.picam2 = Picamera2()
        self.is_recording = False
        self.current_video_file = ""

    def start_recording(self):
        """Starts recording a new video in a separate thread."""
        if self.is_recording:
            logging.info("⚠️ Already recording, ignoring new request.")
            return
        
        self.is_recording = True  # Set recording flag
        
        def record_video():
            timestamp = datetime.now().strftime("%m_%d_%Y_%H-%M-%S")
            self.current_video_file = os.path.join(VIDEO_DIR, f"tmp_GRD_{timestamp}.mp4")

            logging.info(f"🎥 Starting recording: {self.current_video_file}")

            # Configure camera
            self.picam2.set_controls({"FrameRate": 24.0})
            config = self.picam2.create_video_configuration(main={"size": (2028, 1080)})
            self.picam2.configure(config)

            # Start recording (Blocking, but in its own thread)
            self.picam2.start_and_record_video(self.current_video_file, duration=RECORD_DURATION)

            # ✅ Rename file after recording
            final_video_file = self.current_video_file.replace("tmp_", "", 1)
            os.rename(self.current_video_file, final_video_file)
            logging.info(f"✅ Recording complete. Saved as: {final_video_file}")

            # Reset recording flag
            self.is_recording = False

        # 🚀 Run the recording in a separate thread to keep MQTT listener responsive
        threading.Thread(target=record_video, daemon=True).start()

# Global variables for motion detection state
recorder = MotionRecorder()
last_record_time = None
lock = threading.Lock()  # 🔒 Ensure thread safety

def on_message(client, userdata, msg):
    """Handles MQTT messages and determines whether to start a new recording."""
    global last_record_time

    logging.info(f"Motion detected")

    with lock:  # 🔒 Ensure thread safety when checking/modifying timestamps
        current_timestamp = datetime.now()
        logging.info(f"🚨 Motion detected at {current_timestamp}")

        # If this is the first motion event, record immediately
        if last_record_time is None:
            last_record_time = current_timestamp
            recorder.start_recording()
            return

        # Convert RECORD_DURATION to timedelta
        if current_timestamp > last_record_time + timedelta(seconds=RECORD_DURATION):
            last_record_time = current_timestamp
            recorder.start_recording()

# Setup MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message  # Now a standalone function

try:
    mqtt_client.connect(BROKER_IP, 1883, 60)
    mqtt_client.subscribe(GARDEN_TOPIC)
    logging.info(f"📡 Subscribed to MQTT topic: {GARDEN_TOPIC} on broker {BROKER_IP}")
    mqtt_client.loop_forever()
except Exception as e:
    logging.error(f"🚨 Failed to connect to MQTT broker: {e}")