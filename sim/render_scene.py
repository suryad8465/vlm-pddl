import numpy as np
import pybullet as p
from PIL import Image

from sim.state import SceneState


HOUSE_WIDTH = 12
HOUSE_DEPTH = 7

WALL_HEIGHT = 0.7
WALL_THICKNESS = 0.15

FLOOR = [0.75, 0.75, 0.75, 1]
KITCHEN = [0.75, 0.85, 0.95, 1]
LIVING = [0.95, 0.82, 0.65, 1]
WALL = [0.15, 0.15, 0.15, 1]

TABLE = [0.45, 0.22, 0.08, 1]
MUG = [1.0, 1.0, 1.0, 1]
KETTLE = [0.08, 0.08, 0.08, 1]
ROBOT = [0.05, 0.25, 0.85, 1]


def box(position, size, color):
    sx, sy, sz = size

    collision = p.createCollisionShape(
        p.GEOM_BOX,
        halfExtents=[sx / 2, sy / 2, sz / 2],
    )

    visual = p.createVisualShape(
        p.GEOM_BOX,
        halfExtents=[sx / 2, sy / 2, sz / 2],
        rgbaColor=color,
    )

    return p.createMultiBody(
        baseMass=0,
        baseCollisionShapeIndex=collision,
        baseVisualShapeIndex=visual,
        basePosition=position,
    )


def cylinder(position, radius, height, color):
    collision = p.createCollisionShape(
        p.GEOM_CYLINDER,
        radius=radius,
        height=height,
    )

    visual = p.createVisualShape(
        p.GEOM_CYLINDER,
        radius=radius,
        length=height,
        rgbaColor=color,
    )

    return p.createMultiBody(
        baseMass=0,
        baseCollisionShapeIndex=collision,
        baseVisualShapeIndex=visual,
        basePosition=position,
    )


def render_scene(state: SceneState, output_path: str = "scene.png") -> None:
    """Render a SceneState using the established Phase 1 house geometry."""

    p.connect(p.DIRECT)
    p.resetSimulation()
    p.setGravity(0, 0, -9.81)

    # Floor
    box(
        position=(6, 3.5, -0.1),
        size=(12, 7, 0.2),
        color=FLOOR,
    )

    # Kitchen
    if "kitchen" in state.locations:
        box(
            position=(3, 3.5, 0.02),
            size=(5.8, 6.6, 0.04),
            color=KITCHEN,
        )

    # Living room
    if "living_room" in state.locations:
        box(
            position=(9, 3.5, 0.025),
            size=(5.8, 6.6, 0.04),
            color=LIVING,
        )

    # Outer walls
    box(
        position=(0, 3.5, WALL_HEIGHT / 2),
        size=(WALL_THICKNESS, 7, WALL_HEIGHT),
        color=WALL,
    )

    box(
        position=(12, 3.5, WALL_HEIGHT / 2),
        size=(WALL_THICKNESS, 7, WALL_HEIGHT),
        color=WALL,
    )

    box(
        position=(6, 7, WALL_HEIGHT / 2),
        size=(12, WALL_THICKNESS, WALL_HEIGHT),
        color=WALL,
    )

    box(
        position=(6, 0, WALL_HEIGHT / 2),
        size=(12, WALL_THICKNESS, WALL_HEIGHT),
        color=WALL,
    )

    # Kitchen/living divider
    if "kitchen" in state.locations and "living_room" in state.locations:
        box(
            position=(6, 5.8, WALL_HEIGHT / 2),
            size=(WALL_THICKNESS, 2.4, WALL_HEIGHT),
            color=WALL,
        )

        box(
            position=(6, 1.2, WALL_HEIGHT / 2),
            size=(WALL_THICKNESS, 2.4, WALL_HEIGHT),
            color=WALL,
        )

    # Semantic objects
    for obj in state.objects:
        if obj.name == "table":
            position = obj.position or (3.2, 3.5, 0.65)

            box(
                position,
                (2.3, 1.5, 1.3),
                TABLE,
            )

        elif obj.name == "mug":
            position = obj.position or (2.65, 3.5, 1.38)

            cylinder(
                position,
                0.20,
                0.35,
                MUG,
            )

        elif obj.name == "kettle":
            position = obj.position or (3.65, 3.5, 1.45)

            cylinder(
                position,
                0.32,
                0.55,
                KETTLE,
            )
    # Robot
    robot_positions = {
        "kitchen": (3.2, 5.0, 0.55),
        "living_room": (9.0, 3.5, 0.55),
    }

    robot_position = state.robot_position or robot_positions.get(
        state.robot_at,
        (9.0, 3.5, 0.55),
    )
    box(
        position=robot_position,
        size=(0.9, 0.9, 1.1),
        color=ROBOT,
    )

    # Top-down camera
    view_matrix = p.computeViewMatrix(
        cameraEyePosition=(6, 3.5, 16),
        cameraTargetPosition=(6, 3.5, 0),
        cameraUpVector=(0, 1, 0),
    )

    projection_matrix = p.computeProjectionMatrixFOV(
        fov=55,
        aspect=1200 / 800,
        nearVal=0.1,
        farVal=50,
    )

    width, height, rgba, _, _ = p.getCameraImage(
        width=1200,
        height=800,
        viewMatrix=view_matrix,
        projectionMatrix=projection_matrix,
        renderer=p.ER_TINY_RENDERER,
    )

    image = Image.fromarray(np.asarray(rgba, dtype=np.uint8).reshape(height, width, 4), "RGBA")
    image.save(output_path)

    p.disconnect()
