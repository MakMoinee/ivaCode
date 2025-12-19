#include <RPLidar.h>

RPLidar lidar;

#define RPLIDAR_MOTOR 9

bool btConnected = false;
unsigned long lastBTActivity = 0;

void setup() {
  // USB Serial (Debug)
  Serial.begin(9600);

  // RPLIDAR (TX -> RX1)
  Serial1.begin(115200);

  // Bluetooth HC-05 (TX -> RX2, RX -> TX2)
  Serial2.begin(9600);

  pinMode(RPLIDAR_MOTOR, OUTPUT);
  analogWrite(RPLIDAR_MOTOR, 255);   // Spin LIDAR motor
  delay(2000);

  lidar.begin(Serial1);
  lidar.startScan();

  Serial.println("System Ready");
  Serial.println("Waiting for Bluetooth connection...");
}

void loop() {
  /* ---------------- Bluetooth Handling ---------------- */

  if (Serial2.available()) {
    btConnected = true;
    lastBTActivity = millis();

    String msg = Serial2.readStringUntil('\n');
    Serial.print("BT → ");
    Serial.println(msg);
  }

  if (btConnected && millis() - lastBTActivity > 3000) {
    btConnected = false;
    Serial.println("Bluetooth Disconnected");
  }

  /* ---------------- LIDAR Handling ---------------- */

  if (IS_OK(lidar.waitPoint())) {
    float angle = lidar.getCurrentPoint().angle;
    float distance = lidar.getCurrentPoint().distance;
    uint8_t quality = lidar.getCurrentPoint().quality;

    // Print to Serial Monitor
    Serial.print("Angle: ");
    Serial.print(angle);
    Serial.print(" | Distance: ");
    Serial.print(distance);
    Serial.print(" mm | Quality: ");
    Serial.println(quality);

    // Send to Bluetooth if connected
    if (btConnected) {
      Serial2.print(angle);
      Serial2.print(",");
      Serial2.print(distance);
      Serial2.print(",");
      Serial2.println(quality);
    }
  }
}
