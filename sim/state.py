"""Immutable data model for scene state.

Defines the canonical representation of a household scene used throughout
the simulation and pipeline. Three pre-configured factory functions
(baseline_state, layout_2_state, layout_3_state) return SceneState instances
corresponding to the three dataset layouts.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ObjectState:
    """Represents one physical object's symbolic and spatial state.

    Attributes:
        name: Identifier for the object (e.g. "mug", "kettle").
        location: Room the object currently occupies (e.g. "kitchen").
        on: Name of the surface/object this object rests on, or None.
        manipulable: Whether the robot can pick up this object.
        position: (x, y, z) world-space position in metres, or None.
    """
    name: str
    location: str
    on: str | None = None
    manipulable: bool = False
    position: tuple[float, float, float] | None = None


@dataclass(frozen=True)
class SceneState:
    """Complete symbolic and spatial state of the household scene.

    Attributes:
        robot_at: Identifier of the location the robot currently occupies.
        locations: All known room/location identifiers in the scene.
        connections: Pairs of (from, to) location identifiers that are
            directly navigable without doors.
        objects: Tuple of all objects present in the scene.
        robot_position: (x, y, z) world-space position of the robot, or None.
    """

    robot_at: str
    locations: tuple[str, ...]
    connections: tuple[tuple[str, str], ...]
    objects: tuple[ObjectState, ...]
    robot_position: tuple[float, float, float] | None = None


def baseline_state() -> SceneState:
    """Return the baseline dataset layout.

    Robot starts in the living room. Table, mug, and kettle are in the
    kitchen at canonical centred positions.

    Returns:
        A fully populated SceneState for layout baseline.
    """
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
    """Return layout 2 with the table/mug/kettle shifted toward the front-right.

    Robot starts in the living room. Object positions differ from baseline to
    test VLM sensitivity to spatial variation.

    Returns:
        A fully populated SceneState for layout 2.
    """
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
    """Return layout 3 with the table/mug/kettle moved to the upper-left kitchen area.

    Robot starts in the living room at a different position to layout 2.

    Returns:
        A fully populated SceneState for layout 3.
    """
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
