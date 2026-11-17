import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHUFFLE_START = 1794956400
SHUFFLE_END = 1795561200
EMPIRE_START = 1793138400
EMPIRE_END = 1795906800

def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def test_bundled_state_has_requested_windows():
    state = read("data/state.json")
    admin = state["admin"]
    assert (admin["site_settings"]["start_time"], admin["site_settings"]["end_time"]) == (SHUFFLE_START, SHUFFLE_END)
    assert (admin["empiredrop_race"]["start_time"], admin["empiredrop_race"]["end_time"]) == (EMPIRE_START, EMPIRE_END)

def test_seed_has_requested_windows():
    seed = read("private/admin_store.seed.json")
    assert (seed["site_settings"]["start_time"], seed["site_settings"]["end_time"]) == (SHUFFLE_START, SHUFFLE_END)
    assert (seed["empiredrop_race"]["start_time"], seed["empiredrop_race"]["end_time"]) == (EMPIRE_START, EMPIRE_END)

def test_shuffle_defaults_match_requested_window():
    settings = read("private/settings.json")
    assert (settings["start_time"], settings["end_time"]) == (SHUFFLE_START, SHUFFLE_END)

def test_new_shuffle_snapshot_matches_new_window():
    state = read("data/state.json")
    assert state["live"]["shuffle"]["updated_at"] == 0
    assert state["live"]["shuffle"]["rows"] == []

def test_schedule_save_paths_verify_readback():
    text = (ROOT / "wager_backend.py").read_text(encoding="utf-8")
    assert "Shuffle schedule verification failed after save" in text
    assert "EmpireDrop schedule verification failed after save" in text


def test_empiredrop_display_window_does_not_gate_provider_stats():
    state = read("data/state.json")
    assert state["admin"]["empiredrop_races"]["source_mode"] == "races"
    assert state["admin"]["empiredrop_races"]["race_window_policy"] == "provider"
