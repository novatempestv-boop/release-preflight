from dataclasses import dataclass

from .models import Inventory


@dataclass(frozen=True, slots=True)
class Detection:
    kind: str
    name: str
    confidence: str
    evidence: tuple[str, ...]


def detect(inventory: Inventory) -> tuple[Detection, ...]:
    paths = {str(file.relative_path).replace("\\", "/").lower() for file in inventory.files}
    names = {file.relative_path.name.lower() for file in inventory.files}
    suffixes = {file.extension for file in inventory.files}
    detections: list[Detection] = []

    unity_evidence = []
    if "unityplayer.dll" in names:
        unity_evidence.append("UnityPlayer.dll")
    if any(path.endswith("_data/globalgamemanagers") for path in paths):
        unity_evidence.append("*_Data/globalgamemanagers")
    if unity_evidence:
        confidence = "High" if "UnityPlayer.dll" in unity_evidence else "Medium"
        detections.append(Detection("Engine", "Unity", confidence, tuple(unity_evidence)))

    godot_evidence = []
    if ".pck" in suffixes:
        godot_evidence.append("Godot-style .pck package")
    if any(name.startswith("godot") and name.endswith(".exe") for name in names):
        godot_evidence.append("Godot-named executable")
    if godot_evidence:
        confidence = "High" if len(godot_evidence) > 1 else "Medium"
        detections.append(Detection("Engine", "Godot", confidence, tuple(godot_evidence)))

    if ".exe" in suffixes:
        detections.append(Detection("Platform", "Windows", "High", ("Windows .exe present",)))
    elif ".app" in suffixes:
        detections.append(Detection("Platform", "macOS", "High", ("macOS .app bundle present",)))
    elif ".so" in suffixes or any("/lib/" in f"/{path}/" for path in paths):
        detections.append(Detection("Platform", "Linux", "Medium", ("Linux library structure present",)))

    return tuple(detections)
