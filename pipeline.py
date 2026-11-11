import csv
from pathlib import Path

import cv2
from tqdm import tqdm
from ultralytics import YOLO

CONFIG = {
    "video_path": "data/vid.mp4",
    "weights": "yolov8n-pose.pt",
    "out_csv": "data/wrists.csv",
    "conf_thres": 0.3,
    "resize_width": 640,  # downscale for CPU speed; None to disable
    "max_seconds": None,  # cap processing length; None = whole video
}

LEFT_WRIST, RIGHT_WRIST = 9, 10  # COCO keypoint indices


def main(cfg=CONFIG):
    model = YOLO(cfg["weights"])
    cap = cv2.VideoCapture(cfg["video_path"])
    if not cap.isOpened():
        raise RuntimeError(f"could not open {cfg['video_path']}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if cfg["max_seconds"]:
        total_frames = min(total_frames, int(cfg["max_seconds"] * fps))

    scale = 1.0
    src_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    if cfg["resize_width"] and src_w > cfg["resize_width"]:
        scale = cfg["resize_width"] / src_w

    out_path = Path(cfg["out_csv"])
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows_written = 0
    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "t_sec", "track_id", "lw_x", "lw_y", "rw_x", "rw_y", "confidence"])

        for frame_idx in tqdm(range(total_frames), desc="pipeline"):
            ok, frame = cap.read()
            if not ok:
                break
            if scale != 1.0:
                frame = cv2.resize(frame, None, fx=scale, fy=scale)

            result = model.track(frame, persist=True, conf=cfg["conf_thres"], verbose=False)[0]
            if result.boxes is None or result.boxes.id is None or len(result.boxes) == 0:
                continue

            # multiple detections per frame are either noise or ID switches from the
            # tracker; the largest box each frame is taken as "the worker" instead of
            # trusting track_id continuity across the whole video
            boxes = result.boxes.xyxy.cpu().numpy()
            ids = result.boxes.id.cpu().numpy().astype(int)
            kpts = result.keypoints.xy.cpu().numpy()
            kconf = result.keypoints.conf.cpu().numpy() if result.keypoints.conf is not None else None

            areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
            best = int(areas.argmax())

            lw = kpts[best, LEFT_WRIST] / scale
            rw = kpts[best, RIGHT_WRIST] / scale
            conf = float(min(kconf[best, LEFT_WRIST], kconf[best, RIGHT_WRIST])) if kconf is not None else 0.0

            t_sec = frame_idx / fps
            writer.writerow(
                [frame_idx, round(t_sec, 3), ids[best], *lw.round(1), *rw.round(1), round(conf, 3)]
            )
            rows_written += 1

    cap.release()
    print(f"wrote {rows_written} rows to {out_path}")


if __name__ == "__main__":
    main()
