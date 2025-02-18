# RM-Camera-1

## Broker

Recieves MQTT messages and starts video recording

## Publisher

The motion sensor powered by an ESP32 that sends MQTT messages

## Uploader

Checks a folder for completed videos and uploads them to S3. Deletes the local copy of the video once upload is successful.

pip install paho-mqtt
