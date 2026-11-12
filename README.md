

Minimal CV pipeline for a manual packing line: one fixed camera, one worker
packing bottles into cartons. Turns the raw video into placement events and
cycle-time metrics using YOLOv8-pose + two hand-drawn zones, no training.

## Pipeline

```
zones.py     -> data/zones.json        (one-time: draw PICKUP and CARTON zones)
pipeline.py  -> data/wrists.csv        (pose + tracking -> per-frame wrist positions)
events.py    -> data/events.db         (wrist positions + zones -> placements/cycles)
metrics.py   -> stdout                 (throughput, cycle time, idle gaps)
validate.py  -> data/out.mp4           (annotated video for an eyeball check)
```

Run in that order:

```
.\venv\Scripts\python.exe zones.py
.\venv\Scripts\python.exe pipeline.py
.\venv\Scripts\python.exe events.py
.\venv\Scripts\python.exe metrics.py
.\venv\Scripts\python.exe validate.py
```

Only `zones.py` needs a display (it opens a `cv2.selectROI` window). Only
re-run it if the camera angle changes. If you change a threshold in
`events.py`'s `CONFIG`, you just need to re-run `events.py` + `metrics.py`
(and `validate.py` for a fresh video) — `pipeline.py` doesn't need to re-run
since it doesn't touch zones.

Each script has a `CONFIG` dict at the top with its thresholds.

## How a placement is detected

`events.py`: each wrist's (x, y) per frame is tested against the two zone
rectangles (CARTON is checked before PICKUP, since the zones can legitimately
overlap — PICKUP is usually drawn generously to tolerate pose-keypoint noise).
A zone is only "confirmed" once a wrist holds the same raw label for
`smooth_window` consecutive frames, which filters single-frame jitter without
a separate smoothing pass. A **placement** is confirmed when a wrist's
confirmed zone flips from PICKUP straight to CARTON:

- `t_start` = moment it confirmed-entered PICKUP
- `t_end` = moment it confirmed-entered CARTON (the placement instant)

Left and right wrist streams are tracked independently, then merged and
debounced globally (`debounce_sec`) so a two-handed placement, or a quick
flicker re-trigger, isn't counted twice.

## How a cycle (carton) is detected

Placements are chopped into consecutive groups of `bottles_per_carton` (no
overlap). For each group: `t_start` = first placement's `t_end`, `t_end` =
last (Nth) placement's `t_end`, `duration = t_end - t_start`. This measures
first-bottle-to-last-bottle for one carton — it does not include any
walking/setup before the first bottle or sealing/removal after the last.
Leftover placements that don't complete a full group are dropped, not padded
into a partial cycle.

## Known limitations (be honest about these)

- **Rule-based, not learned.** Cycle boundaries are "every N placements," not
  a trained carton-open/close detector. It will misfire if the worker
  reorders steps or occasionally packs a partial carton.
- **Zone geometry is sensitive to pose noise.** YOLOv8-pose wrist keypoints
  are noisy; a tightly-drawn zone can miss genuine reaches. Draw PICKUP with
  generous margin rather than hugging the bottles exactly — this mattered in
  practice (a tight redraw once dropped carton counts from 41 to 13 on the
  same video).
- **Single-worker heuristic.** Per frame, the largest detected person box is
  assumed to be "the worker," to survive tracker ID switches and a second
  person appearing at the frame edge. This breaks if a second worker becomes
  equally or more prominent in frame.
- **CPU speed.** yolov8n-pose + tracking runs at roughly 0.6x real-time on
  this machine (~17-20 fps against a 30fps video) even downscaled — the model
  forward pass is the bottleneck, not frame size.
- **2D zones, not 3D.** A zone is a screen-space rectangle; depth and
  occlusion aren't modeled, so a hand passing over a zone without actually
  placing a bottle can register a false event.

## Files

| File | Purpose |
|---|---|
| `pipeline.py` | YOLOv8-pose + tracking over the video, logs wrist positions to CSV |
| `zones.py` | One-time ROI tool to draw PICKUP/CARTON, saves to JSON |
| `events.py` | Zone-crossing logic -> placement and cycle events in SQLite |
| `metrics.py` | Reads the DB, prints throughput/cycle-time/idle stats |
| `validate.py` | Renders an annotated video for a manual eyeball check |
