from pathlib import Path

from preflight.detection import detect
from preflight.inventory import inventory_build


def test_unity_windows_detection(tmp_path: Path) -> None:
    (tmp_path / "Game.exe").write_bytes(b"")
    (tmp_path / "UnityPlayer.dll").write_bytes(b"")
    data = tmp_path / "Game_Data"
    data.mkdir()
    (data / "globalgamemanagers").write_bytes(b"")

    detections = detect(inventory_build(tmp_path))
    assert any(d.kind == "Engine" and d.name == "Unity" and d.confidence == "High" for d in detections)
    assert any(d.kind == "Platform" and d.name == "Windows" for d in detections)


def test_godot_detection_is_evidence_based(tmp_path: Path) -> None:
    (tmp_path / "MyGame.pck").write_bytes(b"")
    detections = detect(inventory_build(tmp_path))
    assert any(d.kind == "Engine" and d.name == "Godot" and d.confidence == "Medium" for d in detections)


def test_unknown_folder_is_not_guessed(tmp_path: Path) -> None:
    (tmp_path / "readme.txt").write_text("hello")
    assert detect(inventory_build(tmp_path)) == ()
