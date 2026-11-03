"""Serialisation helpers for SceneState ↔ JSON.

Provides save/load functions that convert the immutable SceneState dataclass
to and from plain JSON-serialisable dicts. Used by the scenario generator to
persist and reload scene state files.
"""

import json
from pathlib import Path

from sim.state import ObjectState, SceneState


def state_to_dict(state: SceneState) -> dict:
    """Convert a SceneState to a plain JSON-serialisable dict.

    Args:
        state: The scene state to serialise.

    Returns:
        A dict with keys matching the SceneState fields, suitable for
        ``json.dumps``.
    """
    return {
        "robot_at": state.robot_at,
        "robot_position": list(state.robot_position)
        if state.robot_position is not None
        else None,
        "locations": list(state.locations),
        "connections": [
            {
                "from": source,
                "to": destination,
            }
            for source, destination in state.connections
        ],
        "objects": [
            {
                "name": obj.name,
                "location": obj.location,
                "on": obj.on,
                "manipulable": obj.manipulable,
                "position": list(obj.position)
                if obj.position is not None
                else None,
            }
            for obj in state.objects
        ],
    }


def save_state(state: SceneState, path: str | Path) -> None:
    """Serialise a SceneState to a JSON file.

    Creates parent directories if they do not exist.

    Args:
        state: The scene state to write.
        path: Destination file path (``str`` or ``Path``).
    """
    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            state_to_dict(state),
            indent=2,
        )
        + "\n"
    )


def state_from_dict(data: dict) -> SceneState:
    """Reconstruct a SceneState from a plain dict.

    Handles optional fields (``robot_position``, ``on``, ``position``) and
    converts lists back to the tuples required by the frozen dataclass.

    Args:
        data: Dict previously produced by ``state_to_dict``.

    Returns:
        The reconstructed SceneState.
    """
    robot_position = data.get("robot_position")

    return SceneState(
        robot_at=data["robot_at"],
        robot_position=(
            tuple(robot_position)
            if robot_position is not None
            else None
        ),
        locations=tuple(data["locations"]),
        connections=tuple(
            (connection["from"], connection["to"])
            for connection in data["connections"]
        ),
        objects=tuple(
            ObjectState(
                name=obj["name"],
                location=obj["location"],
                on=obj.get("on"),
                manipulable=obj.get("manipulable", False),
                position=(
                    tuple(obj["position"])
                    if obj.get("position") is not None
                    else None
                ),
            )
            for obj in data["objects"]
        ),
    )


def load_state(path: str | Path) -> SceneState:
    """Read a JSON file and return the deserialised SceneState.

    Args:
        path: Path to a JSON file previously written by ``save_state``.

    Returns:
        The reconstructed SceneState.
    """
    path = Path(path)
    data = json.loads(path.read_text())
    return state_from_dict(data)
