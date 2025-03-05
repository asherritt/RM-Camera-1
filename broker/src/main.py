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

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class MotionRecorder:
    def __init__(self):
        self.picam2 = Picamera2()
        self.is_recording = False
        self.current_video_file = ""
        self.last_recording_time = 0  # Timestamp of last recording

    def start_recording(self, motion_timestamp):
        """Starts recording if it's not already in progress and cooldown has passed."""
        current_time = time.time()

        # Convert motion timestamp from ESP32 uptime (milliseconds) to seconds
        motion_time_seconds = int(motion_timestamp) / 1000

        # Ignore old/duplicate motion events
        if motion_time_seconds <= self.last_recording_time:
            logging.info("⚠️ Ignoring duplicate or old motion event.")
            return

        # Enforce cooldown between recordings
        if current_time - self.last_recording_time < POST_RECORD_COOLDOWN:
            logging.info("⏳ Still in cooldown period. Ignoring motion event.")
            return

        self.is_recording = True
        timestamp = datetime.now().strftime("%m_%d_%Y_%H-%M-%S")
        self.current_video_file = f"{VIDEO_DIR}/tmp_GRD_{timestamp}.mp4"

        logging.info(f"🎥 Starting recording: {self.current_video_file}")

        self.picam2.set_controls({"FrameRate": 24.0})
        config = self.picam2.create_video_configuration(main={"size": (2028, 1080)})
        self.picam2.configure(config)

        self.picam2.start_and_record_video(self.current_video_file, duration=RECORD_DURATION)

        final_video_file = self.current_video_file.replace("tmp_", "", 1)
        os.rename(self.current_video_file, final_video_file)

        logging.info(f"✅ Recording complete. Saved as: {final_video_file}")

        self.last_recording_time = motion_time_seconds  # Store last event time
        self.is_recording = False

    def on_message(self, client, userdata, msg):
        """Handles MQTT messages."""
        payload = json.loads(msg.payload.decode())
        motion_timestamp = payload.get("timestamp", "0")

        logging.info(f"📩 Motion event received with timestamp {motion_timestamp}")
        self.start_recording(motion_timestamp)

recorder = MotionRecorder()
mqtt_client = mqtt.Client()
mqtt_client.on_message = recorder.on_message
mqtt_client.connect(BROKER_IP, 1883, 60)
mqtt_client.subscribe(GARDEN_TOPIC)
mqtt_client.loop_forever()