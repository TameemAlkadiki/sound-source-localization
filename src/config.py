# =============================================================================
# ALPATA LOCALIZER -- CONFIG
# =============================================================================
# This is the ONLY file you normally edit.
# Change the room, the nodes, or the tuning here. The localizer logic
# (alpata_localizer.py) reads these values and never needs editing.
#
# Anything marked  # <-- MEASURE  is a placeholder. Replace it with a real
# measured value when you have access to the hall.
# =============================================================================


# -----------------------------------------------------------------------------
# ROOM SIZE  (metres)
# -----------------------------------------------------------------------------
# Origin (0, 0) is one corner of the room floor, seen from top-down.
ROOM_WIDTH  = 20.0   # <-- MEASURE  long wall, metres
ROOM_HEIGHT = 12.0   # <-- MEASURE  short wall, metres


# -----------------------------------------------------------------------------
# NODES  (the microphones)
# -----------------------------------------------------------------------------
# One entry per node. Add or remove entries freely -- the localizer adapts
# to however many nodes are listed (4 today, 6 or 8 later both just work).
#
#   name : must match the ID the server sends (e.g. "Alpata-1")
#   x, y : node's position on the floor map, in metres
#
# Positions below are ROUGHLY the four corners, nudged ~1 m inward from the
# walls (more realistic than a dead corner, and better for sound pickup).
#   <-- MEASURE all four when you can; these are estimates.
#
#     (0,H) Alpata-1 ------------- Alpata-4 (W,H)
#           |                            |
#           |                            |
#     (0,0) Alpata-2 ------------- Alpata-3 (W,0)
#
NODES = [
    {"name": "Alpata-1", "x": 1.0,              "y": ROOM_HEIGHT - 1.0},  # <-- MEASURE
    {"name": "Alpata-2", "x": 1.0,              "y": 1.0},                # <-- MEASURE
    {"name": "Alpata-3", "x": ROOM_WIDTH - 1.0, "y": 1.0},                # <-- MEASURE
    {"name": "Alpata-4", "x": ROOM_WIDTH - 1.0, "y": ROOM_HEIGHT - 1.0},  # <-- MEASURE
]


# -----------------------------------------------------------------------------
# MICROPHONE / NODE TYPE
# -----------------------------------------------------------------------------
# Hardware profile. Only "noise_floor_db" affects the math directly; the rest
# is documentation so the next person knows what hardware this was tuned for.
MIC_TYPE = "INMP441"

MIC_PROFILE = {
    "INMP441": {
        "interface":     "I2S (digital)",
        "directionality": "omnidirectional",   # correct for this method
        "noise_floor_db": 50.0,  # <-- TUNE  dB level of a quiet/empty room.
                                 # Readings at/below this count as "silence".
                                 # Sit in the empty hall, read the dashboard,
                                 # set this a few dB above that idle number.
    },
    # To switch hardware later, add a new profile here and change MIC_TYPE.
}


# -----------------------------------------------------------------------------
# TRACKING FEEL
# -----------------------------------------------------------------------------
# CONTRAST  -- how strongly the loudest node dominates the estimate.
#   1.0 = gentle (estimate stays nearer the middle)
#   2.0-3.0 = sharper (estimate snaps closer to the loud corner)
CONTRAST = 2.0

# SMOOTHING -- how the moving point behaves over time (0..1).
#   Low  (0.2) = very smooth, glides slowly, ignores jitter
#   High (0.6) = snappy, reacts fast, but can twitch
# Because live dB jitters a lot, keep this on the lower side.
SMOOTHING = 0.30

# MIN_ACTIVE_DB -- if even the loudest node is below this, report "no source"
# (the room is quiet; nothing worth pointing a camera at).
MIN_ACTIVE_DB = 55.0   # <-- TUNE  to taste, just above noise_floor_db
