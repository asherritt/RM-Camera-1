from dotenv import load_dotenv
import os
import logging
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
import json

# Load environment variables
load_dotenv()

BROKER_IP = os.getenv("BROKER_IP")
GARDEN_TOPIC = "motion/garden"
LOG_FILE = os.getenv("LOG_FILE")
COMMAND_FILE = "/tmp/camera_command.json"
RECORD_DURATION = int(os.getenv("RECORD_DURATION", "900"))  # Default 15 min

# ✅ Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)

class CameraController:
    def __init__(self):
        self.last_record_time = None

    def handle_motion_event(self):
        """Write a command file to trigger the camera recorder."""
        current_timestamp = datetime.now()
        logging.info(f"🚨 Motion detected at {current_timestamp}")

        if self.last_record_time and current_timestamp < self.last_record_time + timedelta(seconds=RECORD_DURATION):
            logging.info("⚠️ Skipping recording (too soon since last one).")
            return

        self.last_record_time = current_timestamp

        command_data = {
            "timestamp": current_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": RECORD_DURATION
        }

        with open(COMMAND_FILE, "w") as f:
            json.dump(command_data, f)

        logging.info("✅ Recording command written.")

    def on_message(self, client, userdata, msg):
        """Handles MQTT messages for motion detection."""
        try:
            logging.info(f"📩 Received MQTT message: {msg.payload.decode()}")
            self.handle_motion_event()
        except (json.JSONDecodeError, ValueError):
            logging.error("❌ Failed to decode MQTT message.")

# Initialize and start the MQTT listener
controller = CameraController()
mqtt_client = mqtt.Client()
mqtt_client.on_message = controller.on_message

try:
    mqtt_client.connect(BROKER_IP, 1883, 60)
    mqtt_client.subscribe(GARDEN_TOPIC)
    logging.info(f"📡 Subscribed to MQTT topic: {GARDEN_TOPIC} on broker {BROKER_IP}")
    mqtt_client.loop_forever()
except Exception as e:
    logging.error(f"🚨 Failed to connect to MQTT broker: {e}")