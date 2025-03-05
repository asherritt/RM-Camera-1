#include <Wire.h>
#include "Adafruit_VL6180X.h"
#include <WiFi.h>
#include <PubSubClient.h>
#include "config.h"

// WiFi and MQTT Configuration
WiFiClient espClient;
PubSubClient client(espClient);

// MQTT Topic
const char* topic = "motion/garden";

Adafruit_VL6180X vl = Adafruit_VL6180X();

// Dynamic Baseline Variables
const uint8_t NUM_BASELINE_READINGS = 5;
uint8_t baseline = 0;
uint8_t readings[NUM_BASELINE_READINGS];
uint8_t readingCount = 0;
bool baselineCalculated = false;

// Thresholds
const uint8_t baselineThreshold = 2;
const uint8_t detectionThreshold = 3;

void setup() {
  Serial.begin(115200);
  setupWiFi();
  client.setServer(mqtt_server, 1883);

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
        Serial.print("Initial Baseline Calculated: ");
        Serial.println(baseline);
      }
    } else {
      Serial.print("Baseline: ");
      Serial.print(baseline);

      if (abs(range - baseline) < baselineThreshold) {
        baseline = (baseline + range) / 2;
      }

      if (baseline - range > detectionThreshold) {
        Serial.println(", RAT DETECTED!");

        // **Generate a timestamp for the event**
        unsigned long currentMillis = millis();  // Get ESP32 uptime in milliseconds
        char timestamp[20];
        sprintf(timestamp, "%lu", currentMillis);  // Convert to string

        // **Include the timestamp in the MQTT payload**
        String payload = "{\"motion\": true, \"range\": " + String(range) +
                         ", \"location\": \"garden\", \"timestamp\": " + String(timestamp) + "}";
        client.publish(topic, payload.c_str());
      } else {
        Serial.println(", No significant change.");
      }
    }
  } else {
    handleError(status);
  }

  delay(100);
}

void setupWiFi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect("ESP32Client")) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 10 seconds");
      delay(10000);
    }
  }
}

void handleError(uint8_t status) {
  if ((status >= VL6180X_ERROR_SYSERR_1) && (status <= VL6180X_ERROR_SYSERR_5)) {
    Serial.println("System error");
  } else if (status == VL6180X_ERROR_ECEFAIL) {
    Serial.println("ECE failure");
  } else if (status == VL6180X_ERROR_NOCONVERGE) {
    Serial.println("No convergence");
  } else if (status == VL6180X_ERROR_RANGEIGNORE) {
    Serial.println("Ignoring range");
  } else if (status == VL6180X_ERROR_SNR) {
    Serial.println("Signal/Noise error");
  } else if (status == VL6180X_ERROR_RAWUFLOW) {
    Serial.println("Raw reading underflow");
  } else if (status == VL6180X_ERROR_RAWOFLOW) {
    Serial.println("Raw reading overflow");
  } else if (status == VL6180X_ERROR_RANGEUFLOW) {
    Serial.println("Range reading underflow");
  } else if (status == VL6180X_ERROR_RANGEOFLOW) {
    Serial.println("Range reading overflow");
  }
}