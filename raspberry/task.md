A. Camera Side (Who is the person?)

Person Detection Algorithm

YOLO (YOLOv5 / YOLOv8) 


Fast (real-time)

Accurate for person detection

Widely used in robotics

B. Tracking (Keep following the same person)

Tracking Algorithms

Deep SORT (Best balance) (Deep Simple Online and Realtime Tracking)

Uses bounding box + appearance features

Prevents switching to another person



C. LiDAR Side (How far is the person?)

LiDAR is used for:

Distance measurement

Obstacle detection

Collision avoidance

LiDAR Processing Algorithms

Euclidean Clustering

DBSCAN

Point cloud segmentation

Purpose:


Match detected person (from camera) to a LiDAR cluster

Get accurate distance (meters) and angle



D. Sensor Fusion (Camera + LiDAR)

This is the brain of the system.

Fusion Techniques

Kalman Filter 

Extended Kalman Filter (EKF)

Particle Filter (advanced)

What it does:
Camera → gives direction (left/right)
LiDAR → gives distance
Fusion → stable and smooth target position

E. Motion Control (Following behavior)

Once the person’s position is known:

Control Algorithms

PID Controller 


Controls speed

Controls turning angle

Input: distance & angle to person

Output: motor speed commands








System Flow

Camera captures frame

YOLO detects person

Deep SORT assigns ID (target person)

LiDAR scans environment

Cluster LiDAR points

Match LiDAR cluster to person

Kalman Filter fuses data

Compute distance & angle

PID controller calculates movement

Robot follows the person

Loop repeats

