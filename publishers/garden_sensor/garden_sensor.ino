#include <Wire.h>
#include "Adafruit_VL6180X.h"
#include <WiFi.h>
#include <PubSubClient.h>
#include "config.h"

// WiFi and MQTT Configuration
// const char* ssid = "Your_SSID";         // Replace with your WiFi SSID
// const char* password = "Your_PASSWORD"; // Replace with your WiFi password
// const char* mqtt_server = "192.168.1.100"; // Replace with your MQTT broker's IP

WiFiClient espClient;
PubSubClient client(espClient);

// MQTT Topic
const char* topic = "motion/garden";

Adafruit_VL6180X vl = Adafruit_VL6180X();

// Dynamic Baseline Variables
const uint8_t NUM_BASELINE_READINGS = 10; // Number of readings for baseline calculation
uint8_t baseline = 0;                     // Baseline value
uint8_t readings[NUM_BASELINE_READINGS];  // Array to store initial readings
uint8_t readingCount = 0;                 // Counter for the initial readings
bool baselineCalculated = false;          // Flag to check if baseline is ready

// Thresholds
const uint8_t baselineThreshold = 2;      // Threshold for adjusting baseline
const uint8_t detectionThreshold = 10;    // Threshold for detecting significant decreases

void setup() {
  Serial.begin(115200);

  // Initialize WiFi
  setupWiFi();

  // Initialize MQTT
  client.setServer(mqtt_server, 1883);

  // Initialize the sensor
  Serial.println("Adafruit VL6180x test!");
  if (!vl.begin()) {
    Serial.println("Failed to find sensor");
    while (1);
  }
  Serial.println("Sensor found!");
}

void loop() {
  // Ensure the MQTT client stays connected
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();

  // Read range from the sensor
  uint8_t range = vl.readRange();
  uint8_t status = vl.readRangeStatus();

  if (status == VL6180X_ERROR_NONE) {
    if (!baselineCalculated) {
      // Collect initial readings for baseline calculation
      readings[readingCount++] = range;

      if (readingCount >= NUM_BASELINE_READINGS) {
        // Calculate baseline as the average of the collected readings
        uint32_t sum = 0; // Use a larger type to prevent overflow
        for (uint8_t i = 0; i < NUM_BASELINE_READINGS; i++) {
          sum += readings[i];
        }
        baseline = sum / NUM_BASELINE_READINGS;
        baselineCalculated = true; // Mark baseline as calculated
        Serial.print("Initial Baseline Calculated: ");
        Serial.println(baseline);
      }
    } else {
      // Baseline is ready; detect significant decreases
      Serial.print("Baseline: ");
      Serial.print(baseline);

      // Update the baseline if the range is stable
      if (abs(range - baseline) < baselineThreshold) {
        baseline = (baseline + range) / 2; // Smoothly adjust the baseline
      }

      // Detect a significant decrease in range (something moving closer)
      if (baseline - range > detectionThreshold) {
        Serial.println(", RAT DETECTED!");

        // Publish motion detection to MQTT
        String payload = "{\"motion\": true, \"range\": " + String(range) + ", \"location\": \"garden\"}";
        client.publish(topic, payload.c_str());
      } else {
        Serial.println(", No significant change.");
      }
    }
  } else {
    handleError(status); // Print error messages for debugging
  }

  delay(100); // Adjust delay as needed
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
    // Attempt to connect
    if (client.connect("ESP32Client")) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void handleError(uint8_t status) {
  // Print error messages for debugging
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