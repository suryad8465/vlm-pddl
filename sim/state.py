from dataclasses import dataclass


@dataclass(frozen=True)
class ObjectState:
    name: str
    location: str
    on: str | None = None
    manipulable: bool = False
    position: tuple[float, float, float] | None = None


@dataclass(frozen=True)
class SceneState:
    robot_at: str
    locations: tuple[str, ...]
    connections: tuple[tuple[str, str], ...]
    objects: tuple[ObjectState, ...]
    robot_position: tuple[float, float, float] | None = None


def baseline_state() -> SceneState:
    return SceneState(
        robot_at="living_room",

        locations=(
            "kitchen",
            "living_room",
        ),

        connections=(
            ("kitchen", "living_room"),
            ("living_room", "kitchen"),
        ),

        objects=(
            ObjectState(
                name="table",
                location="kitchen",
                position=(3.2, 3.5, 0.65),
            ),

            ObjectState(
                name="mug",
                location="kitchen",
                on="table",
                manipulable=True,
                position=(2.65, 3.5, 1.38),
            ),

            ObjectState(
                name="kettle",
                location="kitchen",
                on="table",
                manipulable=True,
                position=(3.65, 3.5, 1.45),
            ),
        ),

        robot_position=(9.0, 3.5, 0.55),
    )
def layout_2_state() -> SceneState:
    return SceneState(
        robot_at="living_room",
        locations=("kitchen", "living_room"),
        connections=(
            ("kitchen", "living_room"),
            ("living_room", "kitchen"),
        ),
        objects=(
            ObjectState(
                name="table",
                location="kitchen",
                position=(4.0, 2.4, 0.65),
            ),
            ObjectState(
                name="mug",
                location="kitchen",
                on="table",
                manipulable=True,
                position=(4.6, 2.4, 1.38),
            ),
            ObjectState(
                name="kettle",
                location="kitchen",
                on="table",
                manipulable=True,
                position=(3.4, 2.4, 1.45),
            ),
        ),
        robot_position=(8.2, 5.0, 0.55),
    )
def layout_3_state() -> SceneState:
    return SceneState(
        robot_at="living_room",
        locations=("kitchen", "living_room"),
        connections=(
            ("kitchen", "living_room"),
            ("living_room", "kitchen"),
        ),
        objects=(
            ObjectState(
                name="table",
                location="kitchen",
                position=(2.4, 4.8, 0.65),
            ),
            ObjectState(
                name="mug",
                location="kitchen",
                on="table",
                manipulable=True,
                position=(1.8, 4.8, 1.38),
            ),
            ObjectState(
                name="kettle",
                location="kitchen",
                on="table",
                manipulable=True,
                position=(3.0, 4.8, 1.45),
            ),
        ),
        robot_position=(10.0, 2.0, 0.55),
    )
