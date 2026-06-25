# Sound-Source Localization System

Estimates where in a room the active speaker is, using four corner microphone nodes. Each node reports a sound level in dB — louder means closer — so the system uses a weighted average of all four positions to place the source on a room map in real time.

Built for a conference hall camera system. The estimated (x, y) position feeds a camera controller that steers the lens toward the active speaker automatically.

---

## How it works

```
[Alpata-1] [Alpata-2] [Alpata-3] [Alpata-4]
     \           |          |          /
      \          |          |         /
       -----> AlpataLocalizer.update() -----> (x, y) on room map
```

Each microphone node sends a dB reading every frame. The localizer:

1. Converts each dB level to linear sound energy
2. Subtracts the room noise floor (so silence = zero weight)
3. Raises each weight to a contrast power (sharpens the estimate toward the loudest node)
4. Takes the **weighted centroid** of all node positions
5. Applies temporal smoothing so the tracked point glides instead of twitching

### Why energy-based, not TDOA?

The nodes are independent WiFi devices with unsynchronised clocks. True time-difference-of-arrival (TDOA) requires microsecond-level clock sync — impossible here. Energy-based localization needs no sync at all. Trade-off: room-zone accuracy (~2–4 m), which is enough to steer a camera but not sub-meter. This is a hardware constraint, not a tuning issue.

---

## Project Structure

```
sound-source-localization/
├── src/
│   ├── config.py            # All tunable settings — the only file you normally edit
│   ├── alpata_localizer.py  # Core algorithm — weighted centroid + smoothing
│   └── demo.py              # Simulation runner — walks a fake talker across the room
└── tests/
    ├── conftest.py          # Adds src/ to sys.path for imports
    ├── test_localizer.py    # Full pytest suite (corner, silence, config validation)
    └── __init__.py
```

---

## Tech Stack

- **Python 3** (standard library only for runtime — no dependencies to install)
- **INMP441 MEMS microphones** — digital I2S omnidirectional mics on each node
- **pytest** — full test suite covering localization accuracy and config validation

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/TameemAlkadiki/sound-source-localization.git
cd sound-source-localization
```

### 2. Configure the room

Open `src/config.py` and set:

```python
ROOM_WIDTH  = 20.0   # long wall, metres
ROOM_HEIGHT = 12.0   # short wall, metres

NODES = [
    {"name": "Alpata-1", "x": 1.0,  "y": 11.0},  # top-left
    {"name": "Alpata-2", "x": 1.0,  "y": 1.0},   # bottom-left
    {"name": "Alpata-3", "x": 19.0, "y": 1.0},   # bottom-right
    {"name": "Alpata-4", "x": 19.0, "y": 11.0},  # top-right
]
```

Measure the actual node positions and room dimensions on site. Everything else in `config.py` has sensible defaults.

### 3. Run the demo (no hardware needed)

```bash
python src/demo.py
```

This simulates a talker walking across the room and prints the tracker's estimates each tick:

```
Room 20 x 12 m | mic=INMP441 | nodes=4
Simulating a talker walking across the room...

t= 0  true=( 0.6, 6.0)  est=( 2.1, 5.8)  err= 1.5m  nearest=Alpata-2  conf=high
t= 1  true=( 1.9, 6.0)  est=( 2.8, 5.9)  err= 0.9m  nearest=Alpata-2  conf=high
t= 2  true=( 3.1, 6.0)  est=( 3.5, 6.1)  err= 0.4m  nearest=Alpata-2  conf=medium
...
```

### 4. Run the tests

```bash
pip install pytest
pytest tests/ -v
```

The test suite covers:
- Corner localization — dominant signal at each corner pulls estimate into correct quadrant
- Silence detection — all nodes below `MIN_ACTIVE_DB` returns `None`
- Equal signal — all nodes same dB → low confidence, centred estimate
- Config validation — missing fields, duplicate node names, unknown mic type
- Real dashboard snapshots — recorded live frames used as regression fixtures

---

## Integrating with a live system

```python
from alpata_localizer import AlpataLocalizer

tracker = AlpataLocalizer()

# On every fresh frame from your server:
result = tracker.update({
    "Alpata-1": 77.1,
    "Alpata-2": 79.0,
    "Alpata-3": 75.3,
    "Alpata-4": 72.8,
})

if result:
    x, y = result["x"], result["y"]
    confidence = result["confidence"]   # "high", "medium", or "low"
    # camera.point_to(x, y, confidence=confidence)
```

`update()` returns `None` when the room is quiet (all nodes below `MIN_ACTIVE_DB`).

---

## Configuration Reference

All settings live in `src/config.py`. No other file needs editing.

| Setting | Default | Description |
|---|---|---|
| `ROOM_WIDTH` | `20.0` | Room long wall in metres |
| `ROOM_HEIGHT` | `12.0` | Room short wall in metres |
| `NODES` | 4 corners | List of `{name, x, y}` dicts — add more nodes freely |
| `MIC_TYPE` | `"INMP441"` | Hardware profile to use from `MIC_PROFILE` |
| `noise_floor_db` | `50.0` | Idle room dB — measure in an empty hall and set a few dB above |
| `CONTRAST` | `2.0` | Sharpness — higher values snap the estimate closer to the loudest node |
| `SMOOTHING` | `0.30` | Temporal smoothing — lower = smoother but slower to react |
| `MIN_ACTIVE_DB` | `55.0` | Below this on all nodes → room is quiet, return `None` |

---

## License

MIT
