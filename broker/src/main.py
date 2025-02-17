from dotenv import load_dotenv
import os
import time
import logging
import threading
import paho.mqtt.client as mqtt
from picamera2 import Picamera2

# Load environment variables from .env file
load_dotenv()

# Configurable Parameters
BROKER_IP = os.getenv("BROKER_IP", "192.168.1.240")  # Default if not set
LOG_FILE = os.getenv("LOG_FILEPATH", "/home/asherritt/Desktop/RM-Camera-1/broker/mqtt_logs.log")
VIDEO_DIR = os.getenv("VIDEO_DIR", "~/Desktop/videos/")  # Default video directory
GARDEN_TOPIC = "motion/garden"

# Expand paths to absolute paths
VIDEO_DIR = os.path.expanduser(VIDEO_DIR)
LOG_FILE = os.path.expanduser(LOG_FILE)

# Ensure directories exist
os.makedirs(VIDEO_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Initialize Camera
picam2 = Picamera2()

# Thread-safe lock to prevent multiple recordings
recording_lock = threading.Lock()
is_recording = False

# MQTT Callback Functions
def on_connect(client, userdata, flags, rc):
    logging.info(f"Connected to MQTT broker with result code {rc}")
    client.subscribe(GARDEN_TOPIC)

def on_message(client, userdata, msg):
    global is_recording

    logging.info(f"MQTT Message received on topic {msg.topic}: {msg.payload.decode()}")

    with recording_lock:
        if not is_recording:
            is_recording = True
            timestamp = int(time.time())

            # Ensure video directory exists before saving
            os.makedirs(VIDEO_DIR, exist_ok=True)

            current_video_file = os.path.join(VIDEO_DIR, f"motion_{timestamp}.h264")
            logging.info(f"Starting recording: {current_video_file}")

            # Start recording for 10 minutes (600 seconds)
            picam2.start_and_record_video(current_video_file, duration=600)

            logging.info("Recording complete.")
            is_recording = False
        else:
            logging.info("Recording already in progress, ignoring new motion event.")

# MQTT Client Setup
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)  # Use latest API
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Debugging Output
logging.info(f"Attempting to connect to MQTT Broker at {BROKER_IP}")

# Connect to MQTT broker
mqtt_client.connect(BROKER_IP, 1883, 60)
mqtt_client.subscribe(GARDEN_TOPIC)

# Start the MQTT loop
mqtt_client.loop_forever()