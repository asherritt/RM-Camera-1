from dotenv import load_dotenv
import os
import time
import logging
import paho.mqtt.client as mqtt
from picamera2 import Picamera2
from datetime import datetime
import json

# Load environment variables
load_dotenv()

BROKER_IP = os.getenv("BROKER_IP")
GARDEN_TOPIC = "motion/garden"
LOG_FILE = os.getenv("LOG_FILE")
VIDEO_DIR = os.getenv("VIDEO_DIR")
RECORD_DURATION = int(os.getenv("RECORD_DURATION", "900"))  # Default 15 min

# ✅ Configure logging to both console and file
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
        self.last_record_time = None

    def start_recording(self):
        """Start recording a new video."""
        timestamp = datetime.now().strftime("%m_%d_%Y_%H-%M-%S")
        self.current_video_file = os.path.join(VIDEO_DIR, f"tmp_GRD_{timestamp}.mp4")

        logging.info(f"🎥 Starting recording: {self.current_video_file}")

        # Configure camera
        self.picam2.set_controls({"FrameRate": 24.0})
        config = self.picam2.create_video_configuration(main={"size": (2028, 1080)})
        self.picam2.configure(config)

        # Start recording
        self.picam2.start_and_record_video(self.current_video_file, duration=RECORD_DURATION)

        # Rename file after recording
        final_video_file = self.current_video_file.replace("tmp_", "", 1)
        # os.rename(self.current_video_file, final_video_file)

        logging.info(f"✅ Recording complete. Saved as: {final_video_file}")

    def on_message(self, client, userdata, msg):
        """Handles MQTT messages and determines whether to start a new recording."""
        current_timestamp = datetime.now()
        logging.info(f"🚨 Motion detected at {current_timestamp}")
           
        try:
            if self.last_record_time is None:
                self.last_record_time = current_timestamp
                self.start_recording()
            if (current_timestamp > self.last_record_time + RECORD_DURATION):
                self.last_record_time = current_timestamp
                self.start_recording()
        except (json.JSONDecodeError, ValueError):
            logging.error("❌ Failed to decode MQTT message. Ignoring.")
        
        logging.info(f"last_record_time {self.last_record_time}")

# Initialize motion recorder
recorder = MotionRecorder()

# Setup MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_message = recorder.on_message

try:
    mqtt_client.connect(BROKER_IP, 1883, 60)
    mqtt_client.subscribe(GARDEN_TOPIC)
    logging.info(f"📡 Subscribed to MQTT topic: {GARDEN_TOPIC} on broker {BROKER_IP}")
    mqtt_client.loop_forever()
except Exception as e:
    logging.error(f"🚨 Failed to connect to MQTT broker: {e}")