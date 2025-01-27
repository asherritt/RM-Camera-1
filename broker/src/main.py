from dotenv import load_dotenv
import os
import paho.mqtt.client as mqtt

BROKER_IP = os.getenv("BROKER_IP")
GARDEN_TOPIC = "motion/garden"

def on_message(client, userdata, message):
    print(f"Message received: {message.payload.decode()}")
    # Process sensor data and trigger actions

client = mqtt.Client()
client.on_message = on_message

 print(f"BROKER_IP: {BROKER_IP}")

client.connect(BROKER_IP, 1883)
client.subscribe(GARDEN_TOPIC)

print(f"Subscribed to {GARDEN_TOPIC}. Waiting for messages...")
client.loop_forever()