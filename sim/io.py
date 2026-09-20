import json
from pathlib import Path

from sim.state import ObjectState, SceneState


def state_to_dict(state: SceneState) -> dict:
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
    path = Path(path)
    data = json.loads(path.read_text())
    return state_from_dict(data)
