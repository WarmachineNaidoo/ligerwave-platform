import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Configuration
const API_BASE = __ENV.API_URL || 'https://ligerwave.tech';
const JWT_TOKEN = __ENV.JWT_TOKEN || '';
const HOME_ID = __ENV.HOME_ID || 'test-home-0001';
const DEVICE_ID = __ENV.DEVICE_ID || 'loadtest-device-001';

// Metrics
const eventPushDuration = new Trend('event_push_duration');
const queryDuration = new Trend('query_duration');
const errorRate = new Rate('errors');

// Generate realistic CSI payload (simplified for load)
function makeCsiPayload() {
  const subcarriers = 52;
  const antennas = 3;
  let csi = [];
  for (let i = 0; i < antennas * subcarriers; i++) {
    csi.push((Math.random() * 2 - 1) + (Math.random() * 2 - 1));
  }
  return csi;
}

function randomEventType() {
  const types = ['normal', 'motion', 'intrusion'];
  return types[Math.floor(Math.random() * types.length)];
}

function randomConfidence() {
  return 0.3 + Math.random() * 0.7;
}

// === SCENARIO 1: Device Event Ingestion ===
export function scenarioDeviceEvents() {
  const payload = JSON.stringify({
    gateway_id: DEVICE_ID,
    firmware_ver: '2.1.0',
    csi_data_hex: btoa(String.fromCharCode(...new Float32Array(makeCsiPayload()).buffer)),
    event_type: randomEventType(),
    confidence: randomConfidence(),
    zone: 'living_room',
    wifi_signal_dbm: -55 + Math.floor(Math.random() * 20),
    uptime_s: Math.floor(Math.random() * 86400),
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${JWT_TOKEN}`,
    },
  };

  const start = Date.now();
  const res = http.post(`${API_BASE}/devices/events?home_id=${HOME_ID}`, payload, params);
  const duration = Date.now() - start;

  eventPushDuration.add(duration);
  check(res, {
    'event push status 200/201': (r) => r.status === 200 || r.status === 201,
    'event push fast (<500ms)': () => duration < 500,
  }) || errorRate.add(1);

  sleep(Math.random() * 2 + 0.5); // simulate 0.5-2.5s between pushes
}

// === SCENARIO 2: Dashboard Queries ===
export function scenarioDashboardQueries() {
  const endpoints = [
    `/events/${HOME_ID}?limit=50`,
    `/events/${HOME_ID}/count`,
    `/wellness/${HOME_ID}/breathing`,
    `/wellness/${HOME_ID}/sleep?nights=7`,
    `/premium/heart-rate?home_id=${HOME_ID}`,
    `/homes`,
  ];

  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const params = {
    headers: { 'Authorization': `Bearer ${JWT_TOKEN}` },
  };

  const start = Date.now();
  const res = http.get(`${API_BASE}${endpoint}`, params);
  const duration = Date.now() - start;

  queryDuration.add(duration);
  check(res, {
    'query status 200': (r) => r.status === 200,
    'query fast (<300ms)': () => duration < 300,
  }) || errorRate.add(1);

  sleep(Math.random() * 3 + 1); // simulate 1-4s between queries
}

// === MAIN ===
export default function() {
  // Simulate mixed traffic: 70% device events, 30% dashboard queries
  if (Math.random() < 0.7) {
    scenarioDeviceEvents();
  } else {
    scenarioDashboardQueries();
  }
}
