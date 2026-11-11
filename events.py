import csv
import json
import sqlite3
from pathlib import Path

CONFIG = {
    "wrists_csv": "data/wrists.csv",
    "zones_json": "data/zones.json",
    "out_db": "data/events.db",
    "bottles_per_carton": 6,
    "smooth_window": 2,   # consecutive frames a wrist must sit in a zone before the zone change is "confirmed" (debounces flicker)
    "debounce_sec": 1.0,  # min time between two counted placements, across either wrist
    "conf_thres": 0.3,    # keypoints below this confidence are treated as "unknown" position
}


def in_zone(x, y, zone):
    x1, y1, x2, y2 = zone
    return x1 <= x <= x2 and y1 <= y <= y2


def zone_label(x, y, conf, zones, conf_thres):
    # CARTON is checked first: the drawn zones can overlap (CARTON often sits
    # inside the broader PICKUP area), and CARTON is the more specific one
    if conf < conf_thres:
        return None
    for name in ("CARTON", "PICKUP"):
        if name in zones and in_zone(x, y, zones[name]):
            return name
    return None


def wrist_placements(t_sec, labels, smooth_window):
    """Confirmed PICKUP -> CARTON transitions for one wrist, as (t_start, t_end).

    A zone change only "confirms" after `smooth_window` consecutive identical
    raw labels, which absorbs single-frame detection noise without a separate
    smoothing pass. t_start is when the wrist confirmed-entered PICKUP,
    t_end is when it confirmed-entered CARTON right after.
    """
    placements = []
    confirmed, confirmed_enter_t = None, None
    run_label, run_len, run_start_i = None, 0, 0

    for i, lbl in enumerate(labels):
        if lbl == run_label:
            run_len += 1
        else:
            run_label, run_len, run_start_i = lbl, 1, i

        if run_label is not None and run_len == smooth_window and run_label != confirmed:
            t_enter = t_sec[run_start_i]
            if run_label == "CARTON" and confirmed == "PICKUP":
                placements.append((confirmed_enter_t, t_enter))
            confirmed, confirmed_enter_t = run_label, t_enter

    return placements


def main(cfg=CONFIG):
    with open(cfg["zones_json"]) as f:
        zones = json.load(f)

    t_sec, left_labels, right_labels = [], [], []
    with open(cfg["wrists_csv"], newline="") as f:
        for row in csv.DictReader(f):
            t_sec.append(float(row["t_sec"]))
            conf = float(row["confidence"])
            left_labels.append(zone_label(float(row["lw_x"]), float(row["lw_y"]), conf, zones, cfg["conf_thres"]))
            right_labels.append(zone_label(float(row["rw_x"]), float(row["rw_y"]), conf, zones, cfg["conf_thres"]))

    left_p = wrist_placements(t_sec, left_labels, cfg["smooth_window"])
    right_p = wrist_placements(t_sec, right_labels, cfg["smooth_window"])

    # merge both wrists and debounce by placement (t_end) time, so a two-handed
    # placement or a quick re-trigger doesn't get counted twice
    merged = sorted(left_p + right_p, key=lambda p: p[1])
    placements = []
    last_t_end = float("-inf")
    for t_start, t_end in merged:
        if t_end - last_t_end >= cfg["debounce_sec"]:
            placements.append((t_start, t_end))
            last_t_end = t_end

    n = cfg["bottles_per_carton"]
    cycles = []
    for i in range(0, len(placements) - len(placements) % n, n):
        group = placements[i : i + n]
        t_start, t_end = group[0][1], group[-1][1]
        cycles.append((len(cycles) + 1, t_start, t_end, t_end - t_start))

    leftover = len(placements) % n
    if leftover:
        print(f"note: {leftover} trailing placement(s) don't complete a full carton, dropped from cycles")

    Path(cfg["out_db"]).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(cfg["out_db"])
    conn.execute("DROP TABLE IF EXISTS events")
    conn.execute("DROP TABLE IF EXISTS cycles")
    conn.execute("CREATE TABLE events (event_type TEXT, t_start REAL, t_end REAL)")
    conn.execute("CREATE TABLE cycles (cycle_id INTEGER, t_start REAL, t_end REAL, duration REAL)")
    conn.executemany("INSERT INTO events VALUES (?,?,?)", [("PLACEMENT", s, e) for s, e in placements])
    conn.executemany("INSERT INTO cycles VALUES (?,?,?,?)", cycles)
    conn.commit()
    conn.close()

    print(f"wrote {cfg['out_db']}: {len(placements)} placements, {len(cycles)} cycles")


if __name__ == "__main__":
    main()
