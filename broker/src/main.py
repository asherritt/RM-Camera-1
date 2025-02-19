from dotenv import load_dotenv
import os
import time
import logging
import paho.mqtt.client as mqtt
from picamera2 import Picamera2
from datetime import datetime


# Load environment variables
load_dotenv()

BROKER_IP = os.getenv("BROKER_IP")
GARDEN_TOPIC = "motion/garden"
LOG_FILE = os.getenv("LOG_FILE")
VIDEO_DIR = os.getenv("VIDEO_DIR")

RECORD_DURATION=int(os.getenv("RECORD_DURATION", "600"))


# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Initialize Camera
picam2 = Picamera2()

# Define recording filename
is_recording = False  # Flag to prevent multiple recordings
current_video_file = ""  # To track the current video file

# MQTT Callback Functions
def on_connect(client, userdata, flags, rc):
    logging.info(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(GARDEN_TOPIC)

def on_message(client, userdata, msg):
    global is_recording, current_video_file

    logging.info(f"MQTT Message received on topic {msg.topic}: {msg.payload.decode()}")

    # If not already recording, start a new recording
    if not is_recording:
        is_recording = True
        timestamp = datetime.now().strftime("%m_%d_%Y_%H-%M-%S")  # Format: mm_dd_yyyy_HH-MM-SS
        current_video_file = os.path.join(VIDEO_DIR, f"GRD_{timestamp}.mp4")
        logging.info(f"Starting recording: {current_video_file}")

        picam2.set_controls({
            "FrameRate": 24.0,  # Set framerate to 24 FPS
        })
        # Configure resolution & framerate
        config = picam2.create_video_configuration(
            main={"size": (2028, 1080)},
        )

        picam2.configure(config)  # Apply configuration

        # Set framerate
        picam2.set_controls({"FrameRate": 24.0})  # Set framerate to 24 FPS

        # Start recording
        picam2.start_and_record_video(current_video_file, duration=RECORD_DURATION)
        
        logging.info("Recording complete.")
        is_recording = False
    else:
        logging.info("Recording already in progress, ignoring new motion event.")

# MQTT Client Setup
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Connect to MQTT broker
mqtt_client.connect(BROKER_IP, 1883, 60)
mqtt_client.subscribe(GARDEN_TOPIC)

# Start the MQTT loop
mqtt_client.loop_forever()