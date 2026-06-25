"""
Alpata Localizer -- DEMO RUNNER
===============================

Run this from the project root to watch the localizer work WITHOUT any server:

    python src/demo.py

It invents constantly-changing dB levels (like the real, jittery live feed),
moves a pretend "talker" around the room, and prints the tracked point each
tick. Use it to sanity-check src/config.py before connecting the real system.

TO GO LIVE: ignore this file. In the server, do:

    from alpata_localizer import AlpataLocalizer
    tracker = AlpataLocalizer()
    # ...whenever fresh node levels arrive:
    result = tracker.update({"Alpata-1": db1, "Alpata-2": db2, ...})
    if result:
        point = (result["x"], result["y"])   # feed this to the camera later
"""

import math
import random
import time

import config
from alpata_localizer import AlpataLocalizer


def fake_levels(talker_xy):
    """
    Pretend a person is talking at talker_xy and produce a dB reading per node:
    closer node -> louder, plus random jitter to mimic the real flickering feed.
    This stands in for the server's live data.
    """
    tx, ty = talker_xy
    source_db = 92.0          # loudness at the talker
    floor = config.MIC_PROFILE[config.MIC_TYPE]["noise_floor_db"]
    readings = {}
    for n in config.NODES:
        dist = math.hypot(n["x"] - tx, n["y"] - ty)
        # Sound drops ~6 dB per doubling of distance; clamp near the source.
        db = source_db - 20.0 * math.log10(max(dist, 0.5))
        db = max(db, floor)
        db += random.uniform(-1.5, 1.5)   # live jitter
        readings[n["name"]] = round(db, 1)
    return readings


if __name__ == "__main__":
    tracker = AlpataLocalizer()
    W, H = config.ROOM_WIDTH, config.ROOM_HEIGHT

    print("Room %.0f x %.0f m | mic=%s | nodes=%d"
          % (W, H, config.MIC_TYPE, len(config.NODES)))
    print("Simulating a talker walking across the room...\n")

    # Walk a pretend talker from one side to the other.
    steps = 16
    for i in range(steps):
        talker = (W * (i + 0.5) / steps, H * 0.5)   # left -> right, mid-height
        levels = fake_levels(talker)
        r = tracker.update(levels)

        if r is None:
            print("t=%2d  quiet, no source" % i)
        else:
            err = math.hypot(r["x"] - talker[0], r["y"] - talker[1])
            print("t=%2d  true=(%4.1f,%4.1f)  est=(%4.1f,%4.1f)  "
                  "err=%4.1fm  nearest=%s  conf=%s"
                  % (i, talker[0], talker[1], r["x"], r["y"],
                     err, r["loudest_node"], r["confidence"]))
            # TODO (live): feed r["x"] and r["y"] to your camera-steering API here.
            #   The camera controller expects a position in room metres; pass confidence
            #   too so it can decide whether to move or hold position.
            #   Example: camera.point_to(r["x"], r["y"], confidence=r["confidence"])
        time.sleep(0.15)
