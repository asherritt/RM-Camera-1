#include <Wire.h>
#include "Adafruit_VL6180X.h"
#include <WiFi.h>
#include <PubSubClient.h>
#include "config.h"

#define STEP_PIN 25
#define DIR_PIN 26
#define DOOR_STEPS 1200  // Steps to fully open or close door (adjust to match your hardware)

WiFiClient espClient;
PubSubClient client(espClient);

const char* motionTopic = "motion/garden";
const char* doorTopic = "door/garden";

Adafruit_VL6180X vl = Adafruit_VL6180X();

const uint8_t NUM_BASELINE_READINGS = 5;
uint8_t baseline = 0;
uint8_t readings[NUM_BASELINE_READINGS];
uint8_t readingCount = 0;
bool baselineCalculated = false;

const uint8_t baselineThreshold = 2;
const uint8_t detectionThreshold = 3;

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);

  setupWiFi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(handleMQTT);

  Serial.println("Adafruit VL6180x test!");
  if (!vl.begin()) {
    Serial.println("Failed to find sensor");
    while (1);
  }
  Serial.println("Sensor found!");
}

void loop() {
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();

  uint8_t range = vl.readRange();
  uint8_t status = vl.readRangeStatus();

  if (status == VL6180X_ERROR_NONE) {
    if (!baselineCalculated) {
      readings[readingCount++] = range;
      if (readingCount >= NUM_BASELINE_READINGS) {
        uint32_t sum = 0;
        for (uint8_t i = 0; i < NUM_BASELINE_READINGS; i++) {
          sum += readings[i];
        }
        baseline = sum / NUM_BASELINE_READINGS;
        baselineCalculated = true;
        Serial.print("Initial Baseline: ");
        Serial.println(baseline);
      }
    } else {
      if (abs(range - baseline) < baselineThreshold) {
        baseline = (baseline + range) / 2;
      }

      if (baseline - range > detectionThreshold) {
        Serial.println(", RAT DETECTED!");
        String payload = "{\"motion\": true, \"range\": " + String(range) + ", \"location\": \"garden\"}";
        client.publish(motionTopic, payload.c_str());
      }
    }
  }

  delay(100);
}

void handleMQTT(char* topic, byte* payload, unsigned int length) {
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  message.trim();

  if (String(topic) == doorTopic) {
    if (message == "close") {
      Serial.println("Closing Door");
      moveDoor(true);
    } else if (message == "open") {
      Serial.println("Openning Door");
      moveDoor(false);
    }
  }
}

void moveDoor(bool close) {
  digitalWrite(DIR_PIN, close ? HIGH : LOW);
  for (int i = 0; i < DOOR_STEPS; i++) {
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(1000);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(1000);
  }
}

void setupWiFi() {
  Serial.println("Connecting to WiFi:");
  Serial.print("SSID: ");
  Serial.println(ssid);

  WiFi.disconnect(true);
  delay(1000);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  int retries = 0;

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
    retries++;

    if (retries > 20) {
      Serial.println("Giving up and restarting...");
      ESP.restart();
    }
  }

  Serial.println("\nWiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP32Client")) {
      Serial.println("connected");
      client.subscribe(doorTopic);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" trying again in 10 seconds");
      delay(10000);
    }
  }
}