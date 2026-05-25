#!/usr/bin/env python3
"""
api.py
Flask HTTP API for person-detection + Deep SORT tracking.

Endpoints
---------
  POST /start   – start the detection loop in a background thread (headless)
  POST /stop    – stop the detection loop
  GET  /status  – return current detection state as JSON

Detection logic mirrors detect.py but runs headless (no OpenCV window).

Camera config
-------------
  CAMERA_MODE = "ipcam"   → uses IP_CAM_URL (RTSP / HTTP stream)
  CAMERA_MODE = "laptop"  → uses index 0 (built-in / USB webcam)

Run
---
  python api.py
  python api.py --host 0.0.0.0 --port 5000
"""

import argparse
import threading
import time
import urllib.request
from pathlib import Path
from typing import Optional

import cv2
from flask import Flask, jsonify
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

# ── camera configuration ──────────────────────────────────────────────────────
CAMERA_MODE = "laptop"
IP_CAM_URL  = "rtsp://admin@2026:admin@2026@192.168.1.16/stream1"

# ── detection tuning ──────────────────────────────────────────────────────────
CONF_THRESH    = 0.40
IOU_THRESH     = 0.45
PERSON_CLASS   = 0
DEAD_ZONE_RATIO = 0.15   # ±15 % of frame width = centre dead-zone
MAX_LOST_FRAMES = 30     # frames before target is considered gone

# ── direction tokens ──────────────────────────────────────────────────────────
DIR_LEFT   = "LEFT"
DIR_RIGHT  = "RIGHT"
DIR_CENTER = "CENTER"
DIR_LOST   = "LOST"

# ── shared state (written by detector thread, read by API) ────────────────────
_lock  = threading.Lock()
_state = {
    "running":     False,
    "started_at":  None,
    "stopped_at":  None,
    "direction":   DIR_LOST,
    "target_id":   None,
    "bbox":        None,       # [x1, y1, x2, y2]
    "offset_x":    0.0,
    "confidence":  0.0,
    "lost_frames": 0,
    "frame_count": 0,
    "fps_avg":     0.0,
    "error":       None,
}

_stop_event = threading.Event()
_detector_thread: Optional[threading.Thread] = None

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)


# ── helpers ───────────────────────────────────────────────────────────────────

def _compute_direction(cx: float, frame_w: int) -> tuple[str, float]:
    """Return (direction, normalised_offset_x) and fire robot HTTP request."""
    centre   = frame_w / 2.0
    offset_x = (cx - centre) / centre      # -1 … +1
    dead     = DEAD_ZONE_RATIO

    if offset_x < -dead:
        print("[DIR] LEFT – sending turn-left request")
        try:
            urllib.request.urlopen("http://192.168.23.230/left", timeout=0.5)
        except Exception as e:
            print(f"[WARN] LEFT request failed: {e}")
        return DIR_LEFT, offset_x

    if offset_x > dead:
        print("[DIR] RIGHT – sending turn-right request")
        try:
            urllib.request.urlopen("http://192.168.23.230/right", timeout=0.5)
        except Exception as e:
            print(f"[WARN] RIGHT request failed: {e}")
        return DIR_RIGHT, offset_x

    return DIR_CENTER, offset_x


# ── detector thread ───────────────────────────────────────────────────────────

def _detection_loop(source: str):
    """
    Headless detection + tracking loop.
    Reads frames, runs YOLOv8 + Deep SORT, updates _state.
    Exits cleanly when _stop_event is set.
    """
    global _state

    try:
        # ── load model ────────────────────────────────────────────────────────
        print("[A] Loading YOLOv8n model…")
        model = YOLO("yolov8n.pt")
        print("[A] Model ready.")

        # ── initialise tracker ────────────────────────────────────────────────
        print("[B] Initialising Deep SORT tracker…")
        tracker = DeepSort(
            max_age=MAX_LOST_FRAMES,
            n_init=3,
            nms_max_overlap=1.0,
            max_cosine_distance=0.3,
            nn_budget=100,
        )
        print("[B] Tracker ready.")

        # ── open video source ─────────────────────────────────────────────────
        print(f"[CAM] Opening source: {source}")
        try:
            cap = cv2.VideoCapture(int(source))
        except (ValueError, TypeError):
            cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            raise RuntimeError(f"Cannot open source: {source}")

        frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[CAM] Stream opened — {frame_w}×{frame_h}")

        frame_idx = 0
        target_id = None
        t0        = time.time()

        # ── main loop ─────────────────────────────────────────────────────────
        while not _stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print("[CAM] No frame received – stream ended or lost.")
                break
            frame_idx += 1

            # Step A: YOLO inference
            results = model.predict(
                frame,
                conf=CONF_THRESH,
                iou=IOU_THRESH,
                classes=[PERSON_CLASS],
                verbose=False,
            )[0]

            raw_dets = []
            for box in results.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                raw_dets.append(([x1, y1, x2 - x1, y2 - y1], conf, "person"))

            # Step B: Deep SORT update
            tracks    = tracker.update_tracks(raw_dets, frame=frame)
            confirmed = [t for t in tracks if t.is_confirmed()]

            # Lock onto first confirmed track
            if target_id is None and confirmed:
                target_id = confirmed[0].track_id
                print(f"[B] Target locked: ID={target_id}")

            target_track = next(
                (t for t in confirmed if t.track_id == target_id), None
            )

            elapsed = time.time() - t0
            fps_avg = frame_idx / elapsed if elapsed > 0 else 0.0

            with _lock:
                _state["frame_count"] = frame_idx
                _state["fps_avg"]     = round(fps_avg, 1)

                if target_track is not None:
                    l, t, r, b = map(float, target_track.to_ltrb())
                    cx_target  = (l + r) / 2.0
                    direction, offset_x = _compute_direction(cx_target, frame_w)

                    _state["direction"]   = direction
                    _state["target_id"]   = int(target_id)
                    _state["bbox"]        = [round(l), round(t), round(r), round(b)]
                    _state["offset_x"]    = round(offset_x, 4)
                    _state["lost_frames"] = 0

                    # Match nearest YOLO confidence
                    best_conf = 0.0
                    for box in results.boxes:
                        rx1, ry1, rx2, ry2 = box.xyxy[0].cpu().numpy()
                        rcx = (rx1 + rx2) / 2.0
                        rcy = (ry1 + ry2) / 2.0
                        tcx = (l + r) / 2.0
                        tcy = (t + b) / 2.0
                        if abs(rcx - tcx) < 40 and abs(rcy - tcy) < 40:
                            best_conf = max(best_conf, float(box.conf[0]))
                    _state["confidence"] = round(best_conf, 4)

                else:
                    _state["lost_frames"] += 1
                    if _state["lost_frames"] >= MAX_LOST_FRAMES:
                        print(f"[B] Target ID={target_id} lost. Re-acquiring…")
                        target_id           = None
                        _state["target_id"] = None
                        _state["bbox"]      = None
                        _state["direction"] = DIR_LOST
                        _state["offset_x"]  = 0.0

        # ── cleanup ───────────────────────────────────────────────────────────
        cap.release()
        elapsed = time.time() - t0
        print(f"[DET] Stopped. {frame_idx} frames in {elapsed:.2f}s "
              f"→ {frame_idx/elapsed:.1f} FPS avg")

    except Exception as exc:
        print(f"[ERROR] Detection loop crashed: {exc}")
        with _lock:
            _state["error"] = str(exc)

    finally:
        with _lock:
            _state["running"]    = False
            _state["stopped_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            _state["direction"]  = DIR_LOST


# ── API routes ────────────────────────────────────────────────────────────────

@app.post("/start")
def start():
    global _detector_thread

    with _lock:
        if _state["running"]:
            return jsonify({"status": "already_running",
                            "message": "Detection is already running."}), 409

    # resolve camera source
    source = IP_CAM_URL if CAMERA_MODE == "ipcam" else "0"

    _stop_event.clear()

    with _lock:
        _state.update({
            "running":     True,
            "started_at":  time.strftime("%Y-%m-%dT%H:%M:%S"),
            "stopped_at":  None,
            "direction":   DIR_LOST,
            "target_id":   None,
            "bbox":        None,
            "offset_x":    0.0,
            "confidence":  0.0,
            "lost_frames": 0,
            "frame_count": 0,
            "fps_avg":     0.0,
            "error":       None,
        })

    _detector_thread = threading.Thread(
        target=_detection_loop,
        args=(source,),
        daemon=True,
        name="DetectorThread",
    )
    _detector_thread.start()

    return jsonify({
        "status":  "started",
        "message": "Detection started.",
        "source":  source,
    }), 200


@app.post("/stop")
def stop():
    with _lock:
        if not _state["running"]:
            return jsonify({"status": "not_running",
                            "message": "Detection is not running."}), 409

    _stop_event.set()

    # Give the thread a moment to wind down
    if _detector_thread and _detector_thread.is_alive():
        _detector_thread.join(timeout=5)

    return jsonify({
        "status":  "stopped",
        "message": "Stop signal sent. Detection will halt shortly.",
    }), 200


@app.get("/status")
def status():
    with _lock:
        snapshot = dict(_state)

    return jsonify({
        "status":      "running" if snapshot["running"] else "stopped",
        "started_at":  snapshot["started_at"],
        "stopped_at":  snapshot["stopped_at"],
        "detection": {
            "direction":   snapshot["direction"],
            "target_id":   snapshot["target_id"],
            "bbox":        snapshot["bbox"],
            "offset_x":    snapshot["offset_x"],
            "confidence":  snapshot["confidence"],
            "lost_frames": snapshot["lost_frames"],
        },
        "performance": {
            "frame_count": snapshot["frame_count"],
            "fps_avg":     snapshot["fps_avg"],
        },
        "error": snapshot["error"],
    }), 200


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Person-detection API server")
    ap.add_argument("--host", default="0.0.0.0",
                    help="Host to bind (default: 0.0.0.0)")
    ap.add_argument("--port", type=int, default=5000,
                    help="Port to listen on (default: 5000)")
    ap.add_argument("--debug", action="store_true",
                    help="Enable Flask debug mode")
    args = ap.parse_args()

    print(f"[API] Starting on http://{args.host}:{args.port}")
    print("[API] Endpoints:  POST /start  |  POST /stop  |  GET /status")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
