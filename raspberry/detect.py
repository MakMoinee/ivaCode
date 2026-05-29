#!/usr/bin/env python3
"""
detect.py
Person detection (Step A) + Deep SORT tracking (Step B).

Step A – YOLOv8 (ultralytics) detects all persons in each frame.
Step B – Deep SORT assigns a persistent track ID per person and locks
         onto the first confirmed target so the robot always follows
         the same individual.

Direction output (used by api.py):
  LEFT   – target center is left  of the left dead-zone boundary
  RIGHT  – target center is right of the right dead-zone boundary
  CENTER – target is inside the centre dead-zone (no correction needed)
  LOST   – target track was lost; robot should stop / search

Camera source – set CAMERA_MODE below, or override with --source:
  "laptop"  → built-in / USB webcam  (index 0)
  "ipcam"   → IP camera RTSP/HTTP stream (set IP_CAM_URL)

Usage:
  python detect.py                      # uses CAMERA_MODE default
  python detect.py --source 0           # force laptop webcam
  python detect.py --source <rtsp-url>  # force IP cam URL
  python detect.py --show               # open preview window
  python detect.py --save_out out.mp4
"""

import argparse
import threading
import time
from pathlib import Path

import urllib.request

import cv2
import numpy as np
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

# ── camera configuration ─────────────────────────────────────────────────────
# Change CAMERA_MODE to switch sources without touching the CLI.
#   "laptop" → index 0 (built-in / USB webcam)
#   "ipcam"  → IP camera stream defined by IP_CAM_URL
CAMERA_MODE = "laptop"

# Full RTSP or HTTP URL of your IP camera.
# Examples:
#   RTSP  – "rtsp://admin:password@192.168.1.64:554/stream"
#   HTTP  – "http://192.168.1.64:8080/video"
#   ESP32 – "http://192.168.1.64:81/stream"
IP_CAM_URL = "rtsp://admin@2026:admin@2026@192.168.1.16/stream1"

# Show the annotated OpenCV preview window while running.
# Set to False for headless mode (e.g. on Raspberry Pi without a display).
SHOW_WINDOW = True

# ── constants ────────────────────────────────────────────────────────────────

PERSON_CLASS_ID = 0          # COCO class index for "person"
DEAD_ZONE_RATIO = 0.15       # ±15 % of frame width = centre dead-zone
MAX_LOST_FRAMES = 30         # frames before target is considered gone

# Direction tokens consumed by api.py
DIR_LEFT   = "LEFT"
DIR_RIGHT  = "RIGHT"
DIR_CENTER = "CENTER"
DIR_LOST   = "LOST"

# ── shared tracking state (written by detector, read by api.py) ───────────────

_lock = threading.Lock()

_state = {
    "direction":    DIR_LOST,   # current direction command
    "target_id":    None,       # Deep SORT track ID of locked target
    "bbox":         None,       # (x1, y1, x2, y2) of target in latest frame
    "offset_x":     0.0,        # normalised horizontal offset  (-1.0 … +1.0)
    "confidence":   0.0,        # YOLO confidence of latest detection
    "lost_frames":  0,          # consecutive frames without target
}


def get_tracking_state() -> dict:
    """Return a snapshot of the current tracking state (thread-safe)."""
    with _lock:
        return dict(_state)


def get_direction() -> str:
    """Convenience helper for api.py – returns only the direction token."""
    with _lock:
        return _state["direction"]


# ── helpers ───────────────────────────────────────────────────────────────────

def _compute_direction(cx: float, frame_w: int) -> tuple[str, float]:
    """
    Given target centre-x and frame width, return (direction, offset_x).
    offset_x is normalised: 0 = frame centre, -1 = far left, +1 = far right.
    """
    centre = frame_w / 2.0
    offset_x = (cx - centre) / centre          # -1 … +1
    dead = DEAD_ZONE_RATIO

    if offset_x < -dead:
        print("Direction: LEFT, sending request to turn left")
        try:
            urllib.request.urlopen("http://192.168.1.9/left", timeout=0.5)
        except Exception as e:
            print(f"[WARN] LEFT request failed: {e}")
        return DIR_LEFT, offset_x
    if offset_x > dead:
        print("Direction: RIGHT, sending request to turn right")
        try:
            urllib.request.urlopen("http://192.168.1.9/right", timeout=0.5)
        except Exception as e:
            print(f"[WARN] RIGHT request failed: {e}")
        return DIR_RIGHT, offset_x
    return DIR_CENTER, offset_x


def _draw_hud(frame, tracks, target_id, direction, frame_w, frame_h):
    """Draw bounding boxes, IDs, dead-zone lines and direction HUD."""
    dz = int(frame_w * DEAD_ZONE_RATIO)
    cx = frame_w // 2

    # dead-zone verticals
    cv2.line(frame, (cx - dz, 0), (cx - dz, frame_h), (200, 200, 0), 1)
    cv2.line(frame, (cx + dz, 0), (cx + dz, frame_h), (200, 200, 0), 1)
    # centre vertical
    cv2.line(frame, (cx, 0), (cx, frame_h), (100, 100, 100), 1)

    for trk in tracks:
        if not trk.is_confirmed():
            continue
        tid  = trk.track_id
        l, t, r, b = map(int, trk.to_ltrb())
        is_target = (tid == target_id)

        colour = (0, 255, 0) if is_target else (180, 180, 180)
        thickness = 2 if is_target else 1
        cv2.rectangle(frame, (l, t), (r, b), colour, thickness)

        label = f"{'TARGET' if is_target else 'person'} #{tid}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(frame, (l, t - th - 6), (l + tw + 4, t), colour, -1)
        cv2.putText(frame, label, (l + 2, t - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)

    # direction banner
    colour_map = {
        DIR_LEFT:   (0, 140, 255),
        DIR_RIGHT:  (0, 140, 255),
        DIR_CENTER: (0, 220, 0),
        DIR_LOST:   (0, 0, 220),
    }
    banner = f">> {direction} <<"
    cv2.putText(frame, banner, (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, colour_map[direction], 2, cv2.LINE_AA)


# ── main detector loop ────────────────────────────────────────────────────────

def run(source=None, conf_thresh=0.40, iou_thresh=0.45,
        show=False, save_out=None):
    """
    Main detection + tracking loop.

    Parameters
    ----------
    source     : camera index (int-like str), URL, or file path.
                 Pass None to use CAMERA_MODE / IP_CAM_URL globals.
    conf_thresh: YOLO confidence threshold
    iou_thresh : YOLO NMS IoU threshold
    show       : open an OpenCV window
    save_out   : path to save annotated output video (optional)
    """

    # ── Step A: load YOLOv8 ──────────────────────────────────────────────────
    print("[A] Loading YOLOv8n model (ultralytics)…")
    model = YOLO("yolov8n.pt")          # downloads on first run (~6 MB)
    print("[A] Model ready.")

    # ── Step B: initialise Deep SORT tracker ────────────────────────────────
    print("[B] Initialising Deep SORT tracker…")
    tracker = DeepSort(
        max_age=MAX_LOST_FRAMES,        # keep track alive for N missed frames
        n_init=3,                       # frames needed to confirm a new track
        nms_max_overlap=1.0,
        max_cosine_distance=0.3,        # appearance similarity threshold
        nn_budget=100,
    )
    print("[B] Tracker ready.")

    # ── resolve camera source ────────────────────────────────────────────────
    # Explicit --source overrides CAMERA_MODE; otherwise use the global switch.
    if source is None:
        if CAMERA_MODE == "ipcam":
            source = IP_CAM_URL
            print(f"[CAM] Mode=ipcam  → {IP_CAM_URL}")
        else:
            source = "0"
            print("[CAM] Mode=laptop → index 0 (built-in/USB webcam)")
    else:
        print(f"[CAM] Source overridden via CLI → {source}")

    # ── open video source ────────────────────────────────────────────────────
    try:
        cam_index = int(source)
        cap = cv2.VideoCapture(cam_index)
    except ValueError:
        # URL or file path
        if not source.startswith(("rtsp://", "rtsps://", "http://", "https://")) \
                and not Path(source).exists():
            raise FileNotFoundError(f"Source not found: {source}")
        cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        raise RuntimeError(f"Cannot open source: {source}")

    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps_src = cap.get(cv2.CAP_PROP_FPS) or 30.0

    writer = None
    if save_out:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(save_out, fourcc, fps_src, (frame_w, frame_h))
        print(f"Saving output to {save_out}")

    frame_idx   = 0
    target_id   = None       # Deep SORT ID of the locked target
    t0          = time.time()
    print("Starting. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1

        # ── Step A: YOLO inference ───────────────────────────────────────────
        results = model.predict(
            frame,
            conf=conf_thresh,
            iou=iou_thresh,
            classes=[PERSON_CLASS_ID],
            verbose=False,
        )[0]

        # Build detection list for Deep SORT:
        # each entry → ([left, top, w, h], confidence, class_name)
        raw_dets = []
        for box in results.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = float(box.conf[0])
            w, h = x2 - x1, y2 - y1
            raw_dets.append(([x1, y1, w, h], conf, "person"))

        # ── Step B: Deep SORT update ─────────────────────────────────────────
        tracks = tracker.update_tracks(raw_dets, frame=frame)

        # Confirmed tracks with bounding boxes
        confirmed = [t for t in tracks if t.is_confirmed()]

        # --- target lock-on logic -------------------------------------------
        # Lock onto the first confirmed track if no target yet.
        if target_id is None and confirmed:
            target_id = confirmed[0].track_id
            print(f"[B] Target locked: ID={target_id}")

        # Find the target track in this frame
        target_track = next(
            (t for t in confirmed if t.track_id == target_id), None
        )

        # Update shared state
        with _lock:
            if target_track is not None:
                l, t, r, b   = map(float, target_track.to_ltrb())
                cx_target    = (l + r) / 2.0
                direction, offset_x = _compute_direction(cx_target, frame_w)

                _state["direction"]   = direction
                _state["target_id"]   = target_id
                _state["bbox"]        = (l, t, r, b)
                _state["offset_x"]    = offset_x
                _state["lost_frames"] = 0

                # Find matching raw YOLO confidence (closest bbox centre)
                best_conf = 0.0
                for box in results.boxes:
                    rx1, ry1, rx2, ry2 = box.xyxy[0].cpu().numpy()
                    rcx = (rx1 + rx2) / 2.0
                    rcy = (ry1 + ry2) / 2.0
                    tcx = (l + r) / 2.0
                    tcy = (t + b) / 2.0
                    if abs(rcx - tcx) < 40 and abs(rcy - tcy) < 40:
                        best_conf = max(best_conf, float(box.conf[0]))
                _state["confidence"] = best_conf

            else:
                # Target not visible this frame
                _state["lost_frames"] += 1
                if _state["lost_frames"] >= MAX_LOST_FRAMES:
                    # Target gone too long → re-acquire
                    print(f"[B] Target ID={target_id} lost. Re-acquiring…")
                    target_id           = None
                    _state["target_id"] = None
                    _state["bbox"]      = None
                    _state["direction"] = DIR_LOST
                    _state["offset_x"]  = 0.0

            direction = _state["direction"]

        # ── visualise ────────────────────────────────────────────────────────
        _draw_hud(frame, tracks, target_id, direction, frame_w, frame_h)

        if show:
            cv2.imshow("Detect & Track", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("Quit.")
                break

        if writer:
            writer.write(frame)

    # ── cleanup ───────────────────────────────────────────────────────────────
    cap.release()
    if writer:
        writer.release()
    if show:
        cv2.destroyAllWindows()

    elapsed = time.time() - t0
    print(f"Done. {frame_idx} frames in {elapsed:.2f}s → {frame_idx/elapsed:.1f} FPS avg")


# ── CLI entry point ───────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Person detect + track (Steps A & B)")
    ap.add_argument("--source",   default=None,
                    help="camera index, IP-cam URL, or video path "
                         "(default: uses CAMERA_MODE variable)")
    ap.add_argument("--conf",     type=float, default=0.40,
                    help="YOLO confidence threshold (default 0.40)")
    ap.add_argument("--iou",      type=float, default=0.45,
                    help="YOLO NMS IoU threshold (default 0.45)")
    ap.add_argument("--show",     dest="show", action="store_true",
                    default=SHOW_WINDOW,
                    help="display annotated live preview window")
    ap.add_argument("--no-show",  dest="show", action="store_false",
                    help="run headless (no preview window)")
    ap.add_argument("--save_out", default=None,
                    help="path to save annotated output video")
    args = ap.parse_args()

    run(
        source   = args.source,
        conf_thresh = args.conf,
        iou_thresh  = args.iou,
        show     = args.show,
        save_out = args.save_out,
    )


if __name__ == "__main__":
    main()
