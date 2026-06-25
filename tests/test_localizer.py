"""
Unit tests for AlpataLocalizer.

Geometry reminder (from config.py defaults):
    Alpata-1  (1, 11)  -- top-left
    Alpata-2  (1,  1)  -- bottom-left
    Alpata-3  (19, 1)  -- bottom-right
    Alpata-4  (19,11)  -- top-right
    room centre: (10, 6)
"""

import copy

import pytest

import config
from alpata_localizer import AlpataLocalizer

# Room-centre coordinates derived from config so tests stay in sync with it.
MID_X = config.ROOM_WIDTH / 2
MID_Y = config.ROOM_HEIGHT / 2

# Real dashboard snapshots provided as handover fixtures.
# Both have Alpata-2 as loudest node (bottom-left corner).
FRAME_A = {"Alpata-1": 77, "Alpata-2": 79, "Alpata-3": 78, "Alpata-4": 74}
FRAME_B = {"Alpata-1": 62, "Alpata-2": 70, "Alpata-3": 62, "Alpata-4": 56}


def _dominant_readings(dominant: str, loud: float = 80.0, quiet: float = 60.0) -> dict:
    """One node is 20 dB louder than the rest — a strong single-corner signal."""
    return {n["name"]: (loud if n["name"] == dominant else quiet) for n in config.NODES}


# ---------------------------------------------------------------------------
# Corner localisation
# ---------------------------------------------------------------------------

class TestCornerLocalization:
    """A dominant signal at one corner should pull the estimate into that quadrant."""

    def test_near_alpata1_top_left(self):
        tracker = AlpataLocalizer()
        r = tracker.update(_dominant_readings("Alpata-1"))
        assert r is not None
        assert r["x"] < MID_X, f"Expected x < {MID_X}, got {r['x']}"
        assert r["y"] > MID_Y, f"Expected y > {MID_Y}, got {r['y']}"

    def test_near_alpata2_bottom_left(self):
        tracker = AlpataLocalizer()
        r = tracker.update(_dominant_readings("Alpata-2"))
        assert r is not None
        assert r["x"] < MID_X, f"Expected x < {MID_X}, got {r['x']}"
        assert r["y"] < MID_Y, f"Expected y < {MID_Y}, got {r['y']}"

    def test_near_alpata3_bottom_right(self):
        tracker = AlpataLocalizer()
        r = tracker.update(_dominant_readings("Alpata-3"))
        assert r is not None
        assert r["x"] > MID_X, f"Expected x > {MID_X}, got {r['x']}"
        assert r["y"] < MID_Y, f"Expected y < {MID_Y}, got {r['y']}"

    def test_near_alpata4_top_right(self):
        tracker = AlpataLocalizer()
        r = tracker.update(_dominant_readings("Alpata-4"))
        assert r is not None
        assert r["x"] > MID_X, f"Expected x > {MID_X}, got {r['x']}"
        assert r["y"] > MID_Y, f"Expected y > {MID_Y}, got {r['y']}"


# ---------------------------------------------------------------------------
# Centre / low-confidence case
# ---------------------------------------------------------------------------

def test_centered_talker_returns_low_confidence():
    """Equal dB on all nodes → zero spread → confidence must be 'low'."""
    tracker = AlpataLocalizer()
    equal_readings = {n["name"]: 70.0 for n in config.NODES}
    r = tracker.update(equal_readings)
    assert r is not None
    assert r["spread_db"] == 0.0
    assert r["confidence"] == "low", f"Expected 'low', got {r['confidence']!r}"


# ---------------------------------------------------------------------------
# Silent room
# ---------------------------------------------------------------------------

def test_silent_room_returns_none():
    """All readings below MIN_ACTIVE_DB → room is quiet → update() returns None."""
    tracker = AlpataLocalizer()
    silent = {n["name"]: config.MIN_ACTIVE_DB - 5.0 for n in config.NODES}
    assert tracker.update(silent) is None


# ---------------------------------------------------------------------------
# Bad config — must raise ValueError with a clear message
# ---------------------------------------------------------------------------

class TestBadConfig:

    def test_unknown_mic_type(self, monkeypatch):
        monkeypatch.setattr(config, "MIC_TYPE", "NONEXISTENT_MIC")
        with pytest.raises(ValueError, match="MIC_TYPE"):
            AlpataLocalizer()

    def test_missing_required_field(self, monkeypatch):
        monkeypatch.delattr(config, "NODES")
        with pytest.raises(ValueError, match="NODES"):
            AlpataLocalizer()

    def test_fewer_than_3_nodes(self, monkeypatch):
        monkeypatch.setattr(config, "NODES", config.NODES[:2])
        with pytest.raises(ValueError, match="3"):
            AlpataLocalizer()

    def test_duplicate_node_names(self, monkeypatch):
        duped = copy.deepcopy(config.NODES)
        duped[1]["name"] = duped[0]["name"]
        monkeypatch.setattr(config, "NODES", duped)
        with pytest.raises(ValueError, match="[Dd]uplicate"):
            AlpataLocalizer()


# ---------------------------------------------------------------------------
# Bad readings passed to update()
# ---------------------------------------------------------------------------

class TestBadReadings:

    def test_non_numeric_db_value(self):
        tracker = AlpataLocalizer()
        with pytest.raises(ValueError, match="dB value"):
            tracker.update({"Alpata-1": "quiet", "Alpata-2": 77.0,
                            "Alpata-3": 75.0, "Alpata-4": 72.0})

    def test_readings_must_be_dict(self):
        tracker = AlpataLocalizer()
        with pytest.raises(TypeError):
            tracker.update([77, 79, 78, 74])


# ---------------------------------------------------------------------------
# Dashboard snapshot fixtures
# ---------------------------------------------------------------------------

class TestDashboardSnapshots:
    """Smoke-tests on real recorded frames; Alpata-2 is loudest in both."""

    def test_frame_a_returns_result(self):
        tracker = AlpataLocalizer()
        r = tracker.update(FRAME_A)
        assert r is not None
        assert r["loudest_node"] == "Alpata-2"
        assert r["confidence"] in ("low", "medium", "high")

    def test_frame_b_high_confidence(self):
        """Frame B spread = 70 - 56 = 14 dB → confidence must be 'high'."""
        tracker = AlpataLocalizer()
        r = tracker.update(FRAME_B)
        assert r is not None
        assert r["loudest_node"] == "Alpata-2"
        assert r["confidence"] == "high"

    def test_frame_a_resolves_toward_bottom_left(self):
        """Alpata-2 (bottom-left) is loudest in Frame A → estimate in that quadrant."""
        tracker = AlpataLocalizer()
        r = tracker.update(FRAME_A)
        assert r["x"] < MID_X, f"Frame A: expected x < {MID_X}, got {r['x']}"
        assert r["y"] < MID_Y, f"Frame A: expected y < {MID_Y}, got {r['y']}"

    def test_frame_b_resolves_toward_bottom_left(self):
        """Alpata-2 (bottom-left) dominates Frame B heavily → estimate in that quadrant."""
        tracker = AlpataLocalizer()
        r = tracker.update(FRAME_B)
        assert r["x"] < MID_X, f"Frame B: expected x < {MID_X}, got {r['x']}"
        assert r["y"] < MID_Y, f"Frame B: expected y < {MID_Y}, got {r['y']}"
