/*
  IVA Robot Car - WiFi Access Point / Browser Controlled
  Motor Driver: DBH-12 Dual H-Bridge
  Board:        Arduino UNO R4 WiFi

  HOW TO USE:
    1. Power on the robot.
    2. On your phone or PC, connect to WiFi: "IVA_Robot"  password: robot1234
    3. Open a browser and go to: http://192.168.4.1
    4. Use the on-screen buttons to drive.

  Motor wiring (DBH-12):
    Channel A: IN1A -> pin 3 (PWM)  |  IN2A -> pin 6 (PWM)
    Channel B: IN1B -> pin 5 (PWM)  |  IN2B -> pin 9 (PWM)
*/

#include <WiFiS3.h>
#include "Arduino_LED_Matrix.h"

// ── LED Matrix ────────────────────────────────────────────────────────────────

ArduinoLEDMatrix matrix;

uint8_t FRAME_IVA[8][12] = {
  {1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0},
  {0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0},
  {0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0},
  {0, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 0},
  {0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0},
  {0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0},
  {1, 1, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0},
  {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}
};

void showIVA() { matrix.renderBitmap(FRAME_IVA, 8, 12); }

// ── WiFi Access Point credentials ────────────────────────────────────────────
const char* AP_SSID     = "IVA_Robot";
const char* AP_PASSWORD = "robot1234";   // WPA2 min 8 characters

WiFiServer server(80);

// ── Motor Driver (DBH-12) ─────────────────────────────────────────────────────
#define MA_1 3   // IN1A – PWM
#define MA_2 6   // IN2A – PWM
#define MB_1 5   // IN1B – PWM
#define MB_2 9   // IN2B – PWM

int motorSpeed       = 150;
const int SPEED_STEP =  20;
const int SPEED_MIN  =  60;
const int SPEED_MAX  = 230;

// ── Motor helpers ─────────────────────────────────────────────────────────────

void stopMotors() {
  analogWrite(MA_1, 0); analogWrite(MA_2, 0);
  analogWrite(MB_1, 0); analogWrite(MB_2, 0);
}

void moveForward() {
  analogWrite(MA_1, 0);          analogWrite(MA_2, motorSpeed);
  analogWrite(MB_1, 0);          analogWrite(MB_2, motorSpeed);
}

void moveBackward() {
  analogWrite(MA_1, motorSpeed); analogWrite(MA_2, 0);
  analogWrite(MB_1, motorSpeed); analogWrite(MB_2, 0);
}

void turnLeft() {   // Pivot: Motor A backward, Motor B forward
  analogWrite(MA_1, motorSpeed); analogWrite(MA_2, 0);
  analogWrite(MB_1, 0);          analogWrite(MB_2, motorSpeed);
}

void turnRight() {  // Pivot: Motor A forward, Motor B backward
  analogWrite(MA_1, 0);          analogWrite(MA_2, motorSpeed);
  analogWrite(MB_1, motorSpeed); analogWrite(MB_2, 0);
}

// ── HTTP helpers ──────────────────────────────────────────────────────────────

void sendJSON(WiFiClient& client, int code, const char* body) {
  client.print(F("HTTP/1.1 "));
  client.println(code == 200 ? F("200 OK") : F("404 Not Found"));
  client.println(F("Content-Type: application/json"));
  client.println(F("Access-Control-Allow-Origin: *"));
  client.println(F("Connection: close"));
  client.println();
  client.println(body);
}

void sendHTML(WiFiClient& client) {
  client.println(F("HTTP/1.1 200 OK"));
  client.println(F("Content-Type: text/html"));
  client.println(F("Connection: close"));
  client.println();

  client.print(F("<!DOCTYPE html><html lang='en'><head>"
    "<meta charset='UTF-8'>"
    "<meta name='viewport' content='width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no'>"
    "<title>IVA Robot</title><style>"
    "*{box-sizing:border-box;margin:0;padding:0}"
    "body{font-family:sans-serif;background:#1a1a2e;color:#eee;"
    "display:flex;flex-direction:column;align-items:center;"
    "justify-content:center;min-height:100vh;padding:20px}"
    "h1{margin-bottom:28px;font-size:1.7rem;color:#e94560;letter-spacing:2px}"
    ".grid{display:grid;grid-template-columns:repeat(3,100px);"
    "grid-template-rows:repeat(3,100px);gap:12px}"
    ".btn{border:none;border-radius:16px;font-size:2.2rem;cursor:pointer;"
    "transition:transform .1s;-webkit-tap-highlight-color:transparent}"
    ".btn:active{transform:scale(.9)}"
    ".dir{background:#16213e;color:#e94560}"
    ".stop{background:#e94560;color:#fff}"
    ".empty{visibility:hidden}"
    ".speed-row{margin-top:28px;display:flex;gap:20px;align-items:center}"
    ".sp{width:70px;height:70px;border-radius:50%;background:#16213e;"
    "color:#eee;font-size:1.8rem;border:none;cursor:pointer;"
    "-webkit-tap-highlight-color:transparent}"
    ".sp:active{background:#e94560}"
    "#spd{font-size:1rem;color:#aaa;min-width:90px;text-align:center}"
    "#st{margin-top:16px;font-size:.85rem;color:#555}"
    "</style></head><body>"
    "<h1>&#129302; IVA Robot</h1>"
    "<div class='grid'>"
    "<div class='empty'></div>"
    "<button class='btn dir' onclick=\"cmd('/forward')\">&#9650;</button>"
    "<div class='empty'></div>"
    "<button class='btn dir' onclick=\"cmd('/left')\">&#9668;</button>"
    "<button class='btn stop' onclick=\"cmd('/stop')\">&#9632;</button>"
    "<button class='btn dir' onclick=\"cmd('/right')\">&#9658;</button>"
    "<div class='empty'></div>"
    "<button class='btn dir' onclick=\"cmd('/backward')\">&#9660;</button>"
    "<div class='empty'></div>"
    "</div>"
    "<div class='speed-row'>"
    "<button class='sp' onclick=\"cmd('/speed/down')\">&minus;</button>"
    "<span id='spd'>Speed: ---</span>"
    "<button class='sp' onclick=\"cmd('/speed/up')\">+</button>"
    "</div>"
    "<p id='st'>Connecting...</p>"
    "<script>"
    "function cmd(p){"
    "fetch(p).then(r=>r.json()).then(d=>{"
    "if(d.speed)document.getElementById('spd').textContent='Speed: '+d.speed;"
    "document.getElementById('st').textContent=d.action||d.status;"
    "}).catch(()=>document.getElementById('st').textContent='Connection lost');}"
    "fetch('/status').then(r=>r.json()).then(d=>{"
    "document.getElementById('spd').textContent='Speed: '+d.speed;"
    "document.getElementById('st').textContent='Ready';});"
    "</script></body></html>"));
}

// ── Request handler ───────────────────────────────────────────────────────────

void handleRequest(WiFiClient& client) {
  String reqLine = "";
  unsigned long deadline = millis() + 2000;
  while (client.connected() && millis() < deadline) {
    if (client.available()) {
      char c = client.read();
      if (c == '\n') break;
      if (c != '\r') reqLine += c;
    }
  }

  // Drain remaining headers
  String headerLine = "";
  deadline = millis() + 2000;
  while (client.connected() && millis() < deadline) {
    if (client.available()) {
      char c = client.read();
      if (c == '\n') {
        if (headerLine.length() == 0) break;
        headerLine = "";
      } else if (c != '\r') {
        headerLine += c;
      }
    }
  }

  // Extract path from "GET /path HTTP/1.1"
  String path = "";
  int s1 = reqLine.indexOf(' ');
  int s2 = reqLine.indexOf(' ', s1 + 1);
  if (s1 >= 0 && s2 > s1) path = reqLine.substring(s1 + 1, s2);

  Serial.print(F("GET "));
  Serial.println(path);

  if (path == "/" || path == "/index.html") {
    sendHTML(client);

  } else if (path == "/forward") {
    moveForward();
    sendJSON(client, 200, "{\"status\":\"ok\",\"action\":\"forward\"}");

  } else if (path == "/backward") {
    moveBackward();
    sendJSON(client, 200, "{\"status\":\"ok\",\"action\":\"backward\"}");

  } else if (path == "/left") {
    turnLeft();
    sendJSON(client, 200, "{\"status\":\"ok\",\"action\":\"left\"}");

  } else if (path == "/right") {
    turnRight();
    sendJSON(client, 200, "{\"status\":\"ok\",\"action\":\"right\"}");

  } else if (path == "/stop") {
    stopMotors();
    sendJSON(client, 200, "{\"status\":\"ok\",\"action\":\"stop\"}");

  } else if (path == "/speed/up") {
    motorSpeed = min(motorSpeed + SPEED_STEP, SPEED_MAX);
    Serial.print(F("Speed: ")); Serial.println(motorSpeed);
    char buf[64];
    snprintf(buf, sizeof(buf),
             "{\"status\":\"ok\",\"action\":\"speed_up\",\"speed\":%d}", motorSpeed);
    sendJSON(client, 200, buf);

  } else if (path == "/speed/down") {
    motorSpeed = max(motorSpeed - SPEED_STEP, SPEED_MIN);
    Serial.print(F("Speed: ")); Serial.println(motorSpeed);
    char buf[64];
    snprintf(buf, sizeof(buf),
             "{\"status\":\"ok\",\"action\":\"speed_down\",\"speed\":%d}", motorSpeed);
    sendJSON(client, 200, buf);

  } else if (path == "/status") {
    char buf[48];
    snprintf(buf, sizeof(buf), "{\"status\":\"ok\",\"speed\":%d}", motorSpeed);
    sendJSON(client, 200, buf);

  } else {
    sendJSON(client, 404, "{\"status\":\"error\",\"message\":\"Unknown endpoint\"}");
  }

  delay(1);
  client.stop();
}

// ── Setup ─────────────────────────────────────────────────────────────────────

void setup() {
  pinMode(MA_1, OUTPUT); pinMode(MA_2, OUTPUT);
  pinMode(MB_1, OUTPUT); pinMode(MB_2, OUTPUT);
  stopMotors();

  Serial.begin(9600);

  matrix.begin();
  showIVA();

  Serial.print(F("Starting WiFi AP: "));
  Serial.println(AP_SSID);

  WiFi.beginAP(AP_SSID, AP_PASSWORD);
  delay(2000);

  server.begin();

  Serial.print(F("AP ready. Connect to \""));
  Serial.print(AP_SSID);
  Serial.println(F("\" then open http://192.168.4.1"));
}

// ── Main loop ─────────────────────────────────────────────────────────────────

void loop() {
  WiFiClient client = server.available();
  if (client) handleRequest(client);
}
