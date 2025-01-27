from dotenv import load_dotenv
import os
import paho.mqtt.client as mqtt

BROKER_IP = os.getenv("BROKER_IP") # Replace with your RPi's IP address
TOPIC = "motion/garden"

def on_message(client, userdata, message):
    print(f"Message received: {message.payload.decode()}")
    # Process sensor data and trigger actions

client = mqtt.Client()
client.on_message = on_message

client.connect(BROKER, 1883)
client.subscribe(TOPIC)

print(f"Subscribed to {TOPIC}. Waiting for messages...")
client.loop_forever()