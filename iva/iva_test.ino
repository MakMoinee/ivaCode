/*
  IVA Robot Car - Bluetooth Controlled
  Motor Driver: DBH-12 Dual H-Bridge
  Bluetooth:    HC-05 / HC-06 (SoftwareSerial, pins 10 & 11)

  Mobile Commands:
    F / f  -> Forward
    B / b  -> Backward
    L / l  -> Turn Left
    R / r  -> Turn Right
    S / s  -> Stop
    + / -  -> Increase / Decrease speed
*/

#include <SoftwareSerial.h>

// --- Bluetooth module ---
// Connect HC-05/HC-06 TX -> Arduino pin 10
// Connect HC-05/HC-06 RX -> Arduino pin 11 (use voltage divider: 1kΩ + 2kΩ for 3.3V logic)
#define BT_RX 10
#define BT_TX 11
SoftwareSerial bluetooth(BT_RX, BT_TX);

// --- Motor Driver (DBH-12) ---
// Motor 1: Left wheel
#define M1_A 3   // PWM
#define M1_B 5   // PWM
// Motor 2: Right wheel
#define M2_A 6   // PWM
#define M2_B 9   // PWM

// Speed range: 0–255 (keep under 250 for DBH-12)
int motorSpeed = 150;
const int SPEED_STEP = 20;
const int SPEED_MIN  = 60;
const int SPEED_MAX  = 230;

// ─── Motor helpers ────────────────────────────────────────────────────────────

void stopMotors() {
  analogWrite(M1_A, 0);
  analogWrite(M1_B, 0);
  analogWrite(M2_A, 0);
  analogWrite(M2_B, 0);
}

void moveForward() {
  analogWrite(M1_A, motorSpeed);
  analogWrite(M1_B, 0);
  analogWrite(M2_A, motorSpeed);
  analogWrite(M2_B, 0);
}

void moveBackward() {
  analogWrite(M1_A, 0);
  analogWrite(M1_B, motorSpeed);
  analogWrite(M2_A, 0);
  analogWrite(M2_B, motorSpeed);
}

// Pivot left: left wheel backward, right wheel forward
void turnLeft() {
  analogWrite(M1_A, 0);
  analogWrite(M1_B, motorSpeed);
  analogWrite(M2_A, motorSpeed);
  analogWrite(M2_B, 0);
}

// Pivot right: left wheel forward, right wheel backward
void turnRight() {
  analogWrite(M1_A, motorSpeed);
  analogWrite(M1_B, 0);
  analogWrite(M2_A, 0);
  analogWrite(M2_B, motorSpeed);
}

// ─── Setup ────────────────────────────────────────────────────────────────────

void setup() {
  pinMode(M1_A, OUTPUT);
  pinMode(M1_B, OUTPUT);
  pinMode(M2_A, OUTPUT);
  pinMode(M2_B, OUTPUT);

  stopMotors();

  Serial.begin(9600);       // USB serial for debugging
  bluetooth.begin(9600);    // HC-05/HC-06 default baud rate

  Serial.println("IVA Robot ready. Waiting for Bluetooth commands...");
}

// ─── Main loop ────────────────────────────────────────────────────────────────

void loop() {
  if (bluetooth.available()) {
    char cmd = (char)bluetooth.read();

    switch (cmd) {
      case 'F': case 'f':
        moveForward();
        Serial.println("Forward");
        break;

      case 'B': case 'b':
        moveBackward();
        Serial.println("Backward");
        break;

      case 'L': case 'l':
        turnLeft();
        Serial.println("Turn Left");
        break;

      case 'R': case 'r':
        turnRight();
        Serial.println("Turn Right");
        break;

      case 'S': case 's':
        stopMotors();
        Serial.println("Stop");
        break;

      case '+':
        motorSpeed = min(motorSpeed + SPEED_STEP, SPEED_MAX);
        Serial.print("Speed: ");
        Serial.println(motorSpeed);
        break;

      case '-':
        motorSpeed = max(motorSpeed - SPEED_STEP, SPEED_MIN);
        Serial.print("Speed: ");
        Serial.println(motorSpeed);
        break;

      default:
        // Ignore unknown characters (newlines, spaces, etc.)
        break;
    }
  }
}
