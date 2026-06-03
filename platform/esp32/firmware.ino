/*
 * Ligerwave Bridge Firmware v0.1
 * ESP32-S3: mmWave LD2410 + 433 MHz RX + BLE SpO₂ ring
 * Pushes all sensor data to Ligerwave API via HTTPS
 *
 * Hardware connections:
 *   LD2410 TX → GPIO4 (UART1 RX)
 *   433 MHz RX data → GPIO2 (RMT input)
 *   BLE antenna (built-in)
 *   Status LED → GPIO48
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <BLEDevice.h>
#include <BLEClient.h>
#include <ld2410.h>

// === CONFIGURATION ===
const char* WIFI_SSID = "YOUR_WIFI";
const char* WIFI_PASS = "YOUR_PASSWORD";
const char* API_URL = "https://ligerwave.tech/devices/events";
const char* HOME_ID = "your-home-id";       // set during pairing
const char* GATEWAY_ID = "bridge-001";
const char* API_TOKEN = "";                 // set during pairing, stored in NVS

// Pin definitions
#define LD2410_RX_PIN 4
#define RF433_PIN 2
#define STATUS_LED 48
#define BUTTON_PAIR 0

// === STATE ===
ld2410 radar;
HTTPClient http;
bool mmwave_presence = false;
uint16_t mmwave_distance = 0;
uint8_t mmwave_energy = 0;
unsigned long last_push = 0;
unsigned long last_scan = 0;
const unsigned long PUSH_INTERVAL = 2000;    // push every 2 seconds
const unsigned long BLE_SCAN_INTERVAL = 60000; // scan every 60s

// 433 MHz rolling buffer
#define RF_BUFFER 16
volatile unsigned long rf_pulses[RF_BUFFER];
volatile uint8_t rf_idx = 0;
volatile unsigned long rf_last = 0;

void IRAM_ATTR rf433_interrupt() {
  unsigned long now = micros();
  if (now - rf_last > 400) {  // debounce
    rf_pulses[rf_idx] = now - rf_last;
    rf_idx = (rf_idx + 1) % RF_BUFFER;
    rf_last = now;
  }
}

void connect_wifi() {
  Serial.printf("[WiFi] Connecting to %s", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  int tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries < 60) {
    delay(500);
    Serial.print(".");
    tries++;
    digitalWrite(STATUS_LED, tries % 2);
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n[WiFi] Connected, IP: %s\n", WiFi.localIP().toString().c_str());
    digitalWrite(STATUS_LED, HIGH);
  } else {
    Serial.println("\n[WiFi] Failed, restarting...");
    ESP.restart();
  }
}

void init_radar() {
  Serial1.begin(256000, SERIAL_8N1, LD2410_RX_PIN, -1);
  if (radar.begin(Serial1)) {
    radar.setDetectionMode(1);  // single-person mode
    radar.setMaxDistance(600);  // 6m max range
    Serial.println("[LD2410] mmWave radar initialized");
  } else {
    Serial.println("[LD2410] mmWave radar not found (check wiring)");
  }
}

void init_rf433() {
  pinMode(RF433_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(RF433_PIN), rf433_interrupt, CHANGE);
  Serial.println("[433MHz] RF receiver listening");
}

void init_ble() {
  BLEDevice::init("Ligerwave-Bridge");
  Serial.println("[BLE] Initialized");
}

void init_gpio() {
  pinMode(STATUS_LED, OUTPUT);
  pinMode(BUTTON_PAIR, INPUT_PULLUP);
  digitalWrite(STATUS_LED, LOW);
}

void read_radar() {
  if (!radar.isConnected()) return;
  radar.read();
  if (radar.presenceDetected() || radar.stationaryTargetDetected()) {
    mmwave_presence = true;
    mmwave_distance = radar.movingTargetDistance();
    mmwave_energy = radar.movingTargetEnergy();
  } else {
    mmwave_presence = false;
    mmwave_distance = 0;
    mmwave_energy = 0;
  }
}

void scan_ble_spo2() {
  BLEScan* scan = BLEDevice::getScan();
  scan->setActiveScan(true);
  scan->setInterval(100);
  scan->setWindow(99);
  BLEScanResults results = scan->start(5, false);
  for (int i = 0; i < results.getCount(); i++) {
    BLEAdvertisedDevice d = results.getDevice(i);
    // Wellue SleepU advertises "SleepU" or "O2" in name
    // Other SpO2 rings use standard BLE Health Thermometer service
    if (d.haveServiceUUID() && d.getServiceUUID().equals(BLEUUID("0x1809"))) {
      Serial.printf("[BLE] Found SPO2 device: %s (%d dBm)\n", d.getName().c_str(), d.getRSSI());
      // In production: connect, read SpO2/pulse, store
    }
  }
}

String read_rf433() {
  noInterrupts();
  uint8_t count = rf_idx;
  unsigned long pulses[RF_BUFFER];
  memcpy(pulses, (void*)rf_pulses, sizeof(rf_pulses));
  rf_idx = 0;
  rf_last = 0;
  interrupts();
  if (count == 0) return "[]";
  String json = "[";
  for (int i = 0; i < count; i++) {
    if (i > 0) json += ",";
    json += String(pulses[i]);
  }
  json += "]";
  return json;
}

void push_sensors() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  String rf_data = read_rf433();
  
  StaticJsonDocument<512> doc;
  doc["home_id"] = HOME_ID;
  doc["gateway_id"] = GATEWAY_ID;
  doc["sensors"] = "";
  
  JsonObject mm = doc.createNestedObject("mmwave");
  mm["present"] = mmwave_presence;
  mm["distance_cm"] = mmwave_distance;
  mm["energy"] = mmwave_energy;
  
  JsonArray rf = doc.createNestedArray("rf433");
  if (rf_data.length() > 2) {
    // Parse pulse data as push event
    rf.add("pulse_received");
  }
  
  doc["spo2_available"] = false;  // BLE SpO2 not yet implemented
  
  String payload;
  serializeJson(doc, payload);
  
  http.begin(API_URL);
  http.addHeader("Content-Type", "application/json");
  if (strlen(API_TOKEN) > 0) {
    http.addHeader("Authorization", String("Bearer ") + API_TOKEN);
  }
  int code = http.POST(payload);
  if (code == 200 || code == 201) {
    digitalWrite(STATUS_LED, HIGH);
  } else {
    Serial.printf("[API] Push failed: %d\n", code);
    digitalWrite(STATUS_LED, LOW);
  }
  http.end();
}

void check_pair_button() {
  if (digitalRead(BUTTON_PAIR) == LOW) {
    delay(50);
    if (digitalRead(BUTTON_PAIR) == LOW) {
      Serial.println("[Pair] Button pressed — entering pairing mode");
      // In production: start Bluetooth pairing, receive HOME_ID + API_TOKEN
      // Store in NVS for persistence
      while (digitalRead(BUTTON_PAIR) == LOW) {
        digitalWrite(STATUS_LED, millis() % 500 < 250 ? HIGH : LOW);
        delay(50);
      }
    }
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Ligerwave Bridge v0.1 ===");
  
  init_gpio();
  init_radar();
  init_rf433();
  init_ble();
  connect_wifi();
  
  Serial.println("[Ready] Bridge operational");
}

void loop() {
  unsigned long now = millis();
  
  read_radar();
  check_pair_button();
  
  // Periodic BLE scan for SpO2 rings
  if (now - last_scan > BLE_SCAN_INTERVAL) {
    last_scan = now;
    scan_ble_spo2();
  }
  
  // Push sensor data to API
  if (now - last_push > PUSH_INTERVAL) {
    last_push = now;
    push_sensors();
  }
  
  // Blink LED to show running
  static unsigned long blink = 0;
  if (now - blink > 5000 && WiFi.status() == WL_CONNECTED) {
    digitalWrite(STATUS_LED, !digitalRead(STATUS_LED));
    blink = now;
  }
  
  delay(100);
}
