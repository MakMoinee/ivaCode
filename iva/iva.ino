#include <RPLidar.h>
#include <SoftwareSerial.h>

// Define RX and TX pins for SoftwareSerial
#define RPLIDAR_RX 10
#define RPLIDAR_TX 11

SoftwareSerial lidarSerial(RPLIDAR_RX, RPLIDAR_TX);
RPLidar lidar;

#define OBSTACLE_DISTANCE_CM 50 // threshold distance in cm

void setup() {
  Serial.begin(115200);
  lidarSerial.begin(115200);
  lidar.begin(lidarSerial);
  Serial.println("RPLidar obstacle detection started...");

  // Start the motor pin if your lidar has one (A1 usually needs this)
  pinMode(3, OUTPUT);
  digitalWrite(3, HIGH); // turn motor on
}

void loop() {
  if (IS_OK(lidar.waitPoint())) {
    float distance = lidar.getCurrentPoint().distance; // distance in mm
    float angle = lidar.getCurrentPoint().angle;       // angle in degrees
    bool startBit = lidar.getCurrentPoint().startBit;
    bool quality = lidar.getCurrentPoint().quality;

    if (distance > 0 && distance < (OBSTACLE_DISTANCE_CM * 10)) { // convert cm to mm
      Serial.print("Obstacle detected at ");
      Serial.print(distance / 10.0);
      Serial.print(" cm, angle: ");
      Serial.println(angle);
    }
  } else {
    // If communication failed, try to restart
    lidar.stop();
    lidar.startScan();
  }
}
