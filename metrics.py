import sqlite3
import statistics
from collections import defaultdict

CONFIG = {
    "db_path": "data/events.db",
    "idle_gap_sec": 5.0,
}


def main(cfg=CONFIG):
    conn = sqlite3.connect(cfg["db_path"])
    placements = [r[0] for r in conn.execute("SELECT t_end FROM events WHERE event_type='PLACEMENT' ORDER BY t_end")]
    cycles = [r[0] for r in conn.execute("SELECT duration FROM cycles ORDER BY cycle_id")]
    conn.close()

    if not placements:
        print("no placement events found")
        return

    print("=== throughput (bottles/min) ===")
    per_minute = defaultdict(int)
    for t in placements:
        per_minute[int(t // 60)] += 1
    for minute in range(max(per_minute) + 1):
        print(f"  minute {minute}: {per_minute.get(minute, 0)}")

    print(f"\n=== cycle time (sec), n={len(cycles)} cartons ===")
    if cycles:
        p90 = statistics.quantiles(cycles, n=100, method="inclusive")[89] if len(cycles) > 1 else cycles[0]
        print(f"  mean={statistics.mean(cycles):.2f}  median={statistics.median(cycles):.2f}  p90={p90:.2f}")
    else:
        print("  no complete cycles yet")

    print(f"\n=== idle gaps (no placement for > {cfg['idle_gap_sec']}s) ===")
    gaps = [(a, b, b - a) for a, b in zip(placements, placements[1:]) if b - a > cfg["idle_gap_sec"]]
    if gaps:
        for start, end, dur in gaps:
            print(f"  {start:.1f}s -> {end:.1f}s  ({dur:.1f}s idle)")
        print(f"  total idle: {sum(g[2] for g in gaps):.1f}s across {len(gaps)} gap(s)")
    else:
        print("  none")


if __name__ == "__main__":
    main()
