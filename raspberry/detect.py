#!/usr/bin/env python3
"""
detect_person_yolov5.py
Detect persons using default yolov5s (Ultralytics) via torch.hub.

Usage examples:
  # Webcam (default)
  python detect_person_yolov5.py --source 0

  # Image file
  python detect_person_yolov5.py --source path/to/image.jpg

  # Video file and save output
  python detect_person_yolov5.py --source path/to/video.mp4 --save_out out.mp4

Notes:
- First run downloads yolov5 from GitHub (internet required).
- If you have a GPU and torch with CUDA, model will use it automatically.
"""

import argparse
import time
import cv2
import torch
import numpy as np
from pathlib import Path

# Person class id in COCO for YOLOv5 is 0
PERSON_CLASS_ID = 0

def draw_box(frame, box, conf, label="person"):
    x1, y1, x2, y2 = map(int, box)
    text = f"{label} {conf:.2f}"
    # rectangle
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    # text background
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
    cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw, y1), (0, 255, 0), -1)
    cv2.putText(frame, text, (x1, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="0",
                    help="0 for webcam, or path to image/video file")
    ap.add_argument("--conf", type=float, default=0.25, help="confidence threshold")
    ap.add_argument("--iou", type=float, default=0.45, help="NMS IoU threshold")
    ap.add_argument("--save_out", default=None, help="optional path to save output video (mp4)")
    ap.add_argument("--show", action="store_true", help="show window (useful when running locally)")
    args = ap.parse_args()

    # Load model from torch.hub (will download YOLOv5 repo on first run)
    print("Loading yolov5s model (torch.hub)...")
    model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True)
    model.conf = args.conf  # confidence threshold
    model.iou = args.iou    # NMS IoU threshold
    # model.classes = [PERSON_CLASS_ID]  # alternative: directly filter by class inside results

    # Setup source
    source = args.source
    is_cam = False
    try:
        cam_index = int(source)
        is_cam = True
    except Exception:
        is_cam = False

    if is_cam:
        cap = cv2.VideoCapture(cam_index)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open camera index {cam_index}")
    else:
        if not Path(source).exists():
            raise FileNotFoundError(f"Source not found: {source}")
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open file {source}")

    # Prepare writer if saving output
    writer = None
    if args.save_out:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = cap.get(cv2.CAP_PROP_FPS) or 20.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        writer = cv2.VideoWriter(args.save_out, fourcc, fps, (width, height))
        print(f"Saving output to {args.save_out} (fps={fps}, size={width}x{height})")

    frame_count = 0
    t0 = time.time()
    print("Starting detection. Press 'q' to quit (if window shown).")

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        # YOLOv5 expects RGB images (BGR -> RGB)
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Inference
        results = model(img_rgb, size=640)  # size can be changed for speed/accuracy
        # results.xyxy[0] -> tensor of detections [x1, y1, x2, y2, conf, cls]
        detections = results.xyxy[0].cpu().numpy()

        person_count = 0
        for det in detections:
            x1, y1, x2, y2, conf, cls = det
            cls = int(cls)
            if cls != PERSON_CLASS_ID:
                continue  # we only want persons
            person_count += 1
            box = (x1, y1, x2, y2)
            draw_box(frame, box, float(conf), label="person")
            # print detection details
            print(f"[Frame {frame_count}] person conf={conf:.3f} bbox=({int(x1)},{int(y1)})-({int(x2)},{int(y2)})")

        # put summary text
        cv2.putText(frame, f"Persons: {person_count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)

        # show and/or write
        if args.show:
            cv2.imshow("yolov5 person detection", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("Quit requested.")
                break

        if writer:
            writer.write(frame)

    # cleanup
    cap.release()
    if writer:
        writer.release()
    if args.show:
        cv2.destroyAllWindows()

    elapsed = time.time() - t0
    print(f"Done. Processed {frame_count} frames in {elapsed:.2f}s -> {frame_count/elapsed:.2f} FPS (avg)")

if __name__ == "__main__":
    main()
