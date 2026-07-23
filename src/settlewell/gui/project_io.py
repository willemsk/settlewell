"""Project file serialization and deserialization (.settlewell JSON format)."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Union

from settlewell import __version__


def save_project(state: dict, path: Union[str, Path]) -> None:
    """Serialize wizard state dictionary to a .settlewell JSON file.

    Parameters
    ----------
    state : dict
        State dictionary containing soil_profile, construction_pit, wells, dewatering, buildings.
    path : str or Path
        Destination file path.
    """
    file_path = Path(path)
    if not file_path.suffix:
        file_path = file_path.with_suffix(".settlewell")

    payload = {
        "settlewell_version": __version__,
        "created": datetime.now(timezone.utc).isoformat(),
        "state": state,
    }

    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def load_project(path: Union[str, Path]) -> dict:
    """Deserialize a .settlewell JSON file into a wizard state dictionary.

    Parameters
    ----------
    path : str or Path
        Path to .settlewell or .json project file.

    Returns
    -------
    dict
        State dictionary for populating the wizard.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Projectbestand niet gevonden: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "state" in data:
        return data["state"]

    # Support raw dictionary without version wrapper
    return data
