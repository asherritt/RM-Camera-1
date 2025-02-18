from dotenv import load_dotenv
import os
import time
import logging
import paho.mqtt.client as mqtt
from picamera2 import Picamera2


# Load environment variables
load_dotenv()

BROKER_IP = os.getenv("BROKER_IP")
GARDEN_TOPIC = "motion/garden"
LOG_FILE = os.getenv("LOG_FILEPATH")
VIDEO_DIR = os.getenv("VIDEO_DIR")

RECORD_DURATION=900

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
        timestamp = int(time.time())
        current_video_file = os.path.join(os.path.expanduser(VIDEO_DIR), f"motion_{timestamp}.h264")
        logging.info(f"Starting recording: {current_video_file}")

        picam2.set_controls({
            "FrameRate": 24.0,  # Set framerate to 24 FPS
            "ExposureTime": 50000,  # Adjust exposure (default is ~1000-5000, try increasing it)
            "AnalogueGain": 4.0  # Increase brightness by amplifying sensor signal
        })

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