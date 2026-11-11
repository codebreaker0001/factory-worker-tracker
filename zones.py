import json
from pathlib import Path

import cv2

CONFIG = {
    "video_path": "data/vid.mp4",
    "out_json": "data/zones.json",
}


def main(cfg=CONFIG):
    cap = cv2.VideoCapture(cfg["video_path"])
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"could not read first frame of {cfg['video_path']}")

    zones = {}
    for name in ("PICKUP", "CARTON"):
        print(f"Draw the {name} zone, then press ENTER/SPACE (ESC cancels).")
        x, y, w, h = cv2.selectROI(f"Draw {name} zone - ENTER to confirm", frame, showCrosshair=True)
        cv2.destroyWindow(f"Draw {name} zone - ENTER to confirm")
        if w == 0 or h == 0:
            raise RuntimeError(f"no {name} zone drawn")
        zones[name] = [int(x), int(y), int(x + w), int(y + h)]  # x1, y1, x2, y2

    Path(cfg["out_json"]).parent.mkdir(parents=True, exist_ok=True)
    with open(cfg["out_json"], "w") as f:
        json.dump(zones, f, indent=2)
    print(f"wrote {cfg['out_json']}: {zones}")


if __name__ == "__main__":
    main()
