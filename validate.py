import bisect
import csv
import json
import sqlite3

import cv2
from tqdm import tqdm

CONFIG = {
    "video_path": "data/vid.mp4",
    "wrists_csv": "data/wrists.csv",
    "zones_json": "data/zones.json",
    "db_path": "data/events.db",
    "out_video": "data/out.mp4",
    "max_seconds": None,  # cap render length; None = whole video
}


def main(cfg=CONFIG):
    with open(cfg["zones_json"]) as f:
        zones = json.load(f)

    wrists = {}
    with open(cfg["wrists_csv"], newline="") as f:
        for row in csv.DictReader(f):
            wrists[int(row["frame"])] = (
                float(row["lw_x"]), float(row["lw_y"]), float(row["rw_x"]), float(row["rw_y"])
            )

    conn = sqlite3.connect(cfg["db_path"])
    placement_times = [r[0] for r in conn.execute(
        "SELECT t_end FROM events WHERE event_type='PLACEMENT' ORDER BY t_end"
    )]
    cycle_ends = [r[0] for r in conn.execute("SELECT t_end FROM cycles ORDER BY cycle_id")]
    conn.close()

    cap = cv2.VideoCapture(cfg["video_path"])
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if cfg["max_seconds"]:
        total_frames = min(total_frames, int(cfg["max_seconds"] * fps))

    out = cv2.VideoWriter(cfg["out_video"], cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    for frame_idx in tqdm(range(total_frames), desc="validate"):
        ok, frame = cap.read()
        if not ok:
            break
        t = frame_idx / fps

        for name, (x1, y1, x2, y2) in zones.items():
            color = (0, 200, 255) if name == "PICKUP" else (0, 255, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, name, (x1, max(y1 - 6, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        if frame_idx in wrists:
            lw_x, lw_y, rw_x, rw_y = wrists[frame_idx]
            cv2.circle(frame, (int(lw_x), int(lw_y)), 6, (255, 0, 0), -1)
            cv2.circle(frame, (int(rw_x), int(rw_y)), 6, (0, 0, 255), -1)

        # running count = placements confirmed by this timestamp; current cycle
        # time = elapsed since the last completed cycle (0 if none completed yet)
        count = bisect.bisect_right(placement_times, t)
        last_cycle_end = 0.0
        for ce in cycle_ends:
            if ce <= t:
                last_cycle_end = ce
            else:
                break
        cycle_time = t - last_cycle_end

        cv2.putText(frame, f"placements: {count}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"cycle time: {cycle_time:.1f}s", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        out.write(frame)

    cap.release()
    out.release()
    print(f"wrote {cfg['out_video']}")


if __name__ == "__main__":
    main()
