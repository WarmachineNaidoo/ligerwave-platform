/*
 * Ligerwave CSI Sensor v0.1
 * ESP32-S3: WiFi CSI capture → baseline Z-score → HTTPS push
 *
 * Hardware:
 *   Status LED → GPIO48
 *   Pair button → GPIO0 (boot, internal pull-up)
 *
 * Pairing flow: hold button 3s → AP mode → web form → NVS save → reboot
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <esp_wifi.h>
#include <nvs_flash.h>
#include <nvs.h>
#include <driver/ledc.h>
#include <vector>

// === CONSTANTS ===
#define N_ANTENNAS 3
#define N_SUBCARRIERS 52
#define CSI_FLOAT_SIZE (N_ANTENNAS * N_SUBCARRIERS * 2)  // 312 floats (I+Q)
#define CSI_BYTE_SIZE (CSI_FLOAT_SIZE * 4)                // 1248 bytes
#define PUSH_INTERVAL_MS 100
#define BASELINE_WINDOW 100
#define PAIR_HOLD_MS 3000
#define LED_PIN 48
#define BUTTON_PIN 0
#define AP_SSID "Ligerwave-CSI"
#define AP_PASSWORD "configure123"

// === STATE ===
String home_id = "";
String api_token = "";
String gateway_id = "";
String api_url = "https://ligerwave.tech/devices/events";
String wifi_ssid = "";
String wifi_pass = "";

WiFiSTAClass wifi_sta;
HTTPClient http;
WebServer server(80);

// CSI baseline
struct {
  float mean[N_ANTENNAS][N_SUBCARRIERS];
  float std[N_ANTENNAS][N_SUBCARRIERS];
  int count;
} baseline;

// Status LED
enum LedMode { LED_BREATHING, LED_SOLID, LED_FAST_BLINK };
LedMode led_mode = LED_BREATHING;
unsigned long last_led_update = 0;

// Button debounce
unsigned long btn_press_start = 0;
bool btn_held = false;
bool pairing_mode = false;

// CSI callback buffer
struct CsiPacket {
  float data[N_ANTENNAS][N_SUBCARRIERS][2];  // [antenna][subcarrier][real,imag]
};
std::vector<CsiPacket> csi_buffer;
SemaphoreHandle_t csi_mutex;

// === CSI CALLBACK ===
extern "C" void csi_callback(void *ctx, wifi_csi_info_t *info) {
  if (!info || !info->buf) return;
  
  CsiPacket pkt;
  int len = info->data_len / 2;  // number of (I,Q) pairs per antenna
  
  for (int ant = 0; ant < N_ANTENNAS && ant < info->config.chan; ant++) {
    for (int sc = 0; sc < N_SUBCARRIERS && sc < len; sc++) {
      int idx = ant * len * 2 + sc * 2;
      pkt.data[ant][sc][0] = (float)info->buf[idx];      // real
      pkt.data[ant][sc][1] = (float)info->buf[idx + 1];  // imag
    }
  }
  
  if (xSemaphoreTake(csi_mutex, portMAX_DELAY) == pdTRUE) {
    csi_buffer.push_back(pkt);
    xSemaphoreGive(csi_mutex);
  }
}

// === NVS ===
void init_nvs() {
  nvs_handle_t handle;
  esp_err_t err = nvs_open("ligerwave", NVS_READWRITE, &handle);
  if (err != ESP_OK) {
    Serial.println("[NVS] open failed, erasing...");
    nvs_flash_erase();
    nvs_flash_init();
    nvs_open("ligerwave", NVS_READWRITE, &handle);
  }
  
  size_t len;
  char buf[256];
  
  len = sizeof(buf);
  if (nvs_get_str(handle, "home_id", buf, &len) == ESP_OK) home_id = String(buf);
  len = sizeof(buf);
  if (nvs_get_str(handle, "api_token", buf, &len) == ESP_OK) api_token = String(buf);
  len = sizeof(buf);
  if (nvs_get_str(handle, "gateway_id", buf, &len) == ESP_OK) gateway_id = String(buf);
  len = sizeof(buf);
  if (nvs_get_str(handle, "wifi_ssid", buf, &len) == ESP_OK) wifi_ssid = String(buf);
  len = sizeof(buf);
  if (nvs_get_str(handle, "wifi_pass", buf, &len) == ESP_OK) wifi_pass = String(buf);
  
  nvs_close(handle);
  
  if (gateway_id.length() == 0) {
    uint8_t mac[6];
    esp_read_mac(mac, ESP_MAC_WIFI_STA);
    char gid[32];
    snprintf(gid, sizeof(gid), "csi-%02x%02x%02x%02x%02x%02x", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    gateway_id = String(gid);
    save_nvs("gateway_id", gateway_id.c_str());
  }
}

void save_nvs(const char* key, const char* value) {
  nvs_handle_t handle;
  if (nvs_open("ligerwave", NVS_READWRITE, &handle) != ESP_OK) return;
  nvs_set_str(handle, key, value);
  nvs_commit(handle);
  nvs_close(handle);
}

// === WIFI ===
void connect_wifi() {
  if (wifi_ssid.length() == 0) {
    Serial.println("[WiFi] No credentials stored, entering pairing mode");
    start_ap_mode();
    return;
  }
  
  Serial.printf("[WiFi] Connecting to %s\n", wifi_ssid.c_str());
  WiFi.mode(WIFI_STA);
  WiFi.begin(wifi_ssid.c_str(), wifi_pass.c_str());
  
  int tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries < 120) {
    delay(500);
    Serial.print(".");
    tries++;
    led_mode = LED_BREATHING;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n[WiFi] Connected, IP: %s, MAC: %s\n", WiFi.localIP().toString().c_str(), WiFi.macAddress().c_str());
    led_mode = LED_SOLID;
  } else {
    Serial.println("\n[WiFi] Failed, entering pairing mode");
    start_ap_mode();
  }
}

// === CSI CAPTURE SETUP ===
void start_csi_capture() {
  esp_wifi_set_csi(true);
  wifi_csi_config_t cfg = {
    .lltf_en = 1,
    .htltf_en = 1,
    .stbc_htltf2_en = 1,
    .ltf_merge_en = 1,
    .channel_filter_en = 0,
    .manu_scale = 0,
    .shift = 0,
  };
  esp_wifi_set_csi_config(&cfg);
  esp_wifi_set_csi_rx_cb(&csi_callback, NULL);
  esp_wifi_set_csi(true);
  Serial.println("[CSI] Capture started");
}

// === BASELINE & CONFIDENCE ===
void update_baseline(const float data[N_ANTENNAS][N_SUBCARRIERS][2]) {
  if (baseline.count >= BASELINE_WINDOW) return;  // frozen after window
  
  for (int a = 0; a < N_ANTENNAS; a++) {
    for (int s = 0; s < N_SUBCARRIERS; s++) {
      float mag = sqrtf(data[a][s][0] * data[a][s][0] + data[a][s][1] * data[a][s][1]);
      float old_mean = baseline.mean[a][s];
      baseline.count++;
      baseline.mean[a][s] = old_mean + (mag - old_mean) / baseline.count;
    }
  }
  
  // After window, compute std
  if (baseline.count >= BASELINE_WINDOW) {
    Serial.println("[Baseline] Frozen, computing std...");
    // Recompute std from scratch (simplified)
    for (int a = 0; a < N_ANTENNAS; a++) {
      for (int s = 0; s < N_SUBCARRIERS; s++) {
        baseline.std[a][s] = baseline.mean[a][s] * 0.3f;  // heuristic
      }
    }
  }
}

float compute_confidence(const float data[N_ANTENNAS][N_SUBCARRIERS][2]) {
  if (baseline.count < 20) return 0.0f;
  
  int n_anom = 0;
  float max_z = 0.0f;
  
  for (int a = 0; a < N_ANTENNAS; a++) {
    for (int s = 0; s < N_SUBCARRIERS; s++) {
      float mag = sqrtf(data[a][s][0] * data[a][s][0] + data[a][s][1] * data[a][s][1]);
      float z = fabsf(mag - baseline.mean[a][s]) / (baseline.std[a][s] + 1e-8f);
      if (z > 2.5f) n_anom++;
      if (z > max_z) max_z = z;
    }
  }
  
  int total = N_ANTENNAS * N_SUBCARRIERS;
  float ratio = (float)n_anom / total;
  float conf = ratio * 0.6f + (max_z / 8.0f) * 0.3f;
  return fminf(1.0f, fmaxf(0.0f, conf));
}

// === HTTPS PUSH ===
void push_events() {
  if (WiFi.status() != WL_CONNECTED || api_token.length() == 0 || home_id.length() == 0) return;
  
  std::vector<CsiPacket> batch;
  if (xSemaphoreTake(csi_mutex, pdMS_TO_TICKS(10)) == pdTRUE) {
    batch = csi_buffer;
    csi_buffer.clear();
    xSemaphoreGive(csi_mutex);
  }
  
  if (batch.empty()) return;
  
  // Encode batch as hex
  std::vector<uint8_t> csi_bytes;
  float max_conf = 0;
  int worst_type_idx = -1;
  
  for (size_t i = 0; i < batch.size(); i++) {
    auto &pkt = batch[i];
    update_baseline(pkt.data);
    float conf = compute_confidence(pkt.data);
    if (conf > max_conf) {
      max_conf = conf;
      worst_type_idx = i;
    }
    // Append float buffer: [antenna][subcarrier][real, imag]
    uint8_t *ptr = (uint8_t*)pkt.data;
    csi_bytes.insert(csi_bytes.end(), ptr, ptr + CSI_BYTE_SIZE);
  }
  
  if (csi_bytes.empty()) return;
  
  // Build hex
  String hex_str;
  hex_str.reserve(csi_bytes.size() * 2 + 1);
  static const char hex[] = "0123456789abcdef";
  for (size_t i = 0; i < csi_bytes.size(); i++) {
    hex_str += hex[csi_bytes[i] >> 4];
    hex_str += hex[csi_bytes[i] & 0x0f];
  }
  
  // Determine event type
  const char* event_type = "normal";
  if (max_conf >= 0.92f) event_type = "intrusion";
  else if (max_conf >= 0.60f) event_type = "motion";
  
  // Build JSON
  JsonDocument doc;
  doc["gateway_id"] = gateway_id;
  doc["event_type"] = event_type;
  doc["confidence"] = max_conf;
  doc["zone"] = "esp32";
  doc["zone_path"][0] = "esp32";
  doc["csi_data_hex"] = hex_str;
  
  String payload;
  serializeJson(doc, payload);
  
  int code = 0;
  for (int retry = 0; retry < 3; retry++) {
    http.begin(api_url);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("Authorization", String("Bearer ") + api_token);
    code = http.POST(payload);
    http.end();
    
    if (code < 500) break;
    delay(100 * (retry + 1));
  }
  
  if (code >= 200 && code < 300) {
    led_mode = max_conf >= 0.92f ? LED_FAST_BLINK : LED_SOLID;
  }
}

// === PAIRING / AP MODE ===
void start_ap_mode() {
  pairing_mode = true;
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASSWORD);
  Serial.printf("[AP] Started SSID=%s IP=%s\n", AP_SSID, WiFi.softAPIP().toString().c_str());
  
  server.on("/", HTTP_GET, []() {
    String html = R"rawliteral(
<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Ligerwave CSI Pairing</title>
<style>body{font-family:sans-serif;padding:20px;max-width:400px;margin:auto}
input{width:100%;padding:8px;margin:6px 0;box-sizing:border-box}
button{width:100%;padding:10px;background:#2563eb;color:white;border:none;border-radius:4px;font-size:16px}
h2{text-align:center}</style></head>
<body><h2>Ligerwave CSI Pairing</h2>
<form action="/save" method="POST">
<input name="wifi_ssid" placeholder="WiFi SSID" required>
<input name="wifi_pass" type="password" placeholder="WiFi Password" required>
<input name="home_id" placeholder="Home ID from dashboard" required>
<input name="api_token" placeholder="API Token from dashboard" required>
<button type="submit">Pair Device</button>
</form>
<p style="font-size:12px;color:gray;text-align:center">Gateway: )rawliteral" + gateway_id + R"rawliteral(</p>
</body></html>)rawliteral";
    server.send(200, "text/html", html);
  });
  
  server.on("/save", HTTP_POST, []() {
    wifi_ssid = server.arg("wifi_ssid");
    wifi_pass = server.arg("wifi_pass");
    home_id = server.arg("home_id");
    api_token = server.arg("api_token");
    
    save_nvs("wifi_ssid", wifi_ssid.c_str());
    save_nvs("wifi_pass", wifi_pass.c_str());
    save_nvs("home_id", home_id.c_str());
    save_nvs("api_token", api_token.c_str());
    
    String html = "<html><body><h2>Pairing Complete</h2><p>Rebooting in 3 seconds...</p></body></html>";
    server.send(200, "text/html", html);
    delay(3000);
    ESP.restart();
  });
  
  server.begin();
}

// === STATUS LED ===
void setup_led() {
  ledcSetup(0, 5000, 8);
  ledcAttachPin(LED_PIN, 0);
}

void update_led() {
  unsigned long now = millis();
  int duty = 0;
  
  switch (led_mode) {
    case LED_BREATHING:
      // Slow pulse: 2s period
      duty = (int)((sinf((now % 2000) / 2000.0f * 2 * PI) + 1.0f) * 127.5f);
      break;
    case LED_SOLID:
      duty = 192;
      break;
    case LED_FAST_BLINK:
      // Fast blink: 200ms period
      duty = (now % 200 < 100) ? 255 : 0;
      break;
  }
  
  ledcWrite(0, duty);
}

// === BUTTON ===
void check_button() {
  if (digitalRead(BUTTON_PIN) == LOW) {
    if (!btn_held) {
      btn_press_start = millis();
      btn_held = true;
    } else if ((millis() - btn_press_start) > PAIR_HOLD_MS && !pairing_mode) {
      Serial.println("[Button] 3s hold — entering pairing mode");
      save_nvs("wifi_ssid", "");
      save_nvs("wifi_pass", "");
      start_ap_mode();
      led_mode = LED_FAST_BLINK;
    }
  } else {
    btn_held = false;
  }
}

// === SETUP ===
void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Ligerwave CSI Sensor v0.1 ===");
  
  csi_mutex = xSemaphoreCreateBinary();
  xSemaphoreGive(csi_mutex);
  
  setup_led();
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  init_nvs();
  
  if (wifi_ssid.length() > 0 && wifi_pass.length() > 0) {
    connect_wifi();
    if (WiFi.status() == WL_CONNECTED) {
      start_csi_capture();
      led_mode = LED_SOLID;
    }
  } else {
    start_ap_mode();
  }
  
  Serial.println("[Ready] Sensor operational");
}

// === LOOP ===
void loop() {
  if (pairing_mode) {
    server.handleClient();
    update_led();
    delay(10);
    return;
  }
  
  static unsigned long last_push = 0;
  unsigned long now = millis();
  
  check_button();
  update_led();
  
  if (now - last_push >= PUSH_INTERVAL_MS) {
    last_push = now;
    push_events();
  }
  
  static unsigned long wifi_check = 0;
  if (now - wifi_check > 30000) {
    wifi_check = now;
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("[WiFi] Reconnecting...");
      WiFi.reconnect();
    }
  }
  
  delay(1);
}
