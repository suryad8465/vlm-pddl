"""
Simple PyBullet top-down floor-plan render.

Semantic components:
    Kitchen
    Living room
    Table
    Mug
    Kettle
    Robot

"""

import pybullet as p
import numpy as np
from PIL import Image


# ============================================================
# HELPERS
# ============================================================

def box(position, size, color):
    sx, sy, sz = size

    collision = p.createCollisionShape(
        p.GEOM_BOX,
        halfExtents=[sx / 2, sy / 2, sz / 2]
    )

    visual = p.createVisualShape(
        p.GEOM_BOX,
        halfExtents=[sx / 2, sy / 2, sz / 2],
        rgbaColor=color
    )

    return p.createMultiBody(
        baseMass=0,
        baseCollisionShapeIndex=collision,
        baseVisualShapeIndex=visual,
        basePosition=position
    )


def cylinder(position, radius, height, color):
    collision = p.createCollisionShape(
        p.GEOM_CYLINDER,
        radius=radius,
        height=height
    )

    visual = p.createVisualShape(
        p.GEOM_CYLINDER,
        radius=radius,
        length=height,
        rgbaColor=color
    )

    return p.createMultiBody(
        baseMass=0,
        baseCollisionShapeIndex=collision,
        baseVisualShapeIndex=visual,
        basePosition=position
    )


# ============================================================
# PYBULLET
# ============================================================

p.connect(p.DIRECT)
p.resetSimulation()
p.setGravity(0, 0, -9.81)


# ============================================================
# HOUSE
# ============================================================

HOUSE_WIDTH = 12
HOUSE_DEPTH = 7

WALL_HEIGHT = 0.7
WALL_THICKNESS = 0.15


# ============================================================
# COLORS
# ============================================================

FLOOR = [0.75, 0.75, 0.75, 1]

KITCHEN = [0.75, 0.85, 0.95, 1]
LIVING = [0.95, 0.82, 0.65, 1]

WALL = [0.15, 0.15, 0.15, 1]

TABLE = [0.45, 0.22, 0.08, 1]
MUG = [1.0, 1.0, 1.0, 1]
KETTLE = [0.08, 0.08, 0.08, 1]
ROBOT = [0.05, 0.25, 0.85, 1]


# ============================================================
# FLOOR
# ============================================================

box(
    position=(6, 3.5, -0.1),
    size=(12, 7, 0.2),
    color=FLOOR
)


# ============================================================
# KITCHEN FLOOR
# ============================================================

box(
    position=(3, 3.5, 0.02),
    size=(5.8, 6.6, 0.04),
    color=KITCHEN
)


# ============================================================
# LIVING ROOM FLOOR
# ============================================================

box(
    position=(9, 3.5, 0.025),
    size=(5.8, 6.6, 0.04),
    color=LIVING
)


# ============================================================
# OUTER WALLS
# ============================================================

# Left
box(
    position=(0, 3.5, WALL_HEIGHT / 2),
    size=(WALL_THICKNESS, 7, WALL_HEIGHT),
    color=WALL
)

# Right
box(
    position=(12, 3.5, WALL_HEIGHT / 2),
    size=(WALL_THICKNESS, 7, WALL_HEIGHT),
    color=WALL
)

# Top
box(
    position=(6, 7, WALL_HEIGHT / 2),
    size=(12, WALL_THICKNESS, WALL_HEIGHT),
    color=WALL
)

# Bottom
box(
    position=(6, 0, WALL_HEIGHT / 2),
    size=(12, WALL_THICKNESS, WALL_HEIGHT),
    color=WALL
)


# ============================================================
# KITCHEN / LIVING ROOM DIVIDER
# ============================================================

# Kitchen side of divider
box(
    position=(6, 5.8, WALL_HEIGHT / 2),
    size=(WALL_THICKNESS, 2.4, WALL_HEIGHT),
    color=WALL
)

# Living side of divider
box(
    position=(6, 1.2, WALL_HEIGHT / 2),
    size=(WALL_THICKNESS, 2.4, WALL_HEIGHT),
    color=WALL
)

# ------------------------------------------------------------
# OPENING
#
# The opening is between:
#
#       y = 2.4
#       y = 4.6
#
# There is NO wall here.
# ------------------------------------------------------------


# ============================================================
# TABLE
# ============================================================

# One single body.

box(
    position=(3.2, 3.5, 0.65),
    size=(2.3, 1.5, 1.3),
    color=TABLE
)


# ============================================================
# MUG
# ============================================================

# One single body.

cylinder(
    position=(2.65, 3.5, 1.38),
    radius=0.20,
    height=0.35,
    color=MUG
)


# ============================================================
# KETTLE
# ============================================================

# One single body.

cylinder(
    position=(3.65, 3.5, 1.45),
    radius=0.32,
    height=0.55,
    color=KETTLE
)


# ============================================================
# ROBOT
# ============================================================

# One single body.

box(
    position=(9.0, 3.5, 0.55),
    size=(0.9, 0.9, 1.1),
    color=ROBOT
)


# ============================================================
# CAMERA
# ============================================================

# Slightly angled top-down view.
#
# This is more reliable than an exactly vertical camera because
# PyBullet can otherwise make the thin geometry difficult to see.

camera_position = (6, 3.5, 16)

camera_target = (6, 3.5, 0)

view_matrix = p.computeViewMatrix(
    cameraEyePosition=camera_position,
    cameraTargetPosition=camera_target,
    cameraUpVector=(0, 1, 0)
)


# ============================================================
# PERSPECTIVE PROJECTION
# ============================================================

WIDTH = 1200
HEIGHT = 800

projection_matrix = p.computeProjectionMatrixFOV(
    fov=55,
    aspect=WIDTH / HEIGHT,
    nearVal=0.1,
    farVal=50
)


# ============================================================
# RENDER
# ============================================================

result = p.getCameraImage(
    width=WIDTH,
    height=HEIGHT,
    viewMatrix=view_matrix,
    projectionMatrix=projection_matrix,
    renderer=p.ER_TINY_RENDERER
)


# ============================================================
# SAVE
# ============================================================

rgba = np.array(
    result[2],
    dtype=np.uint8
).reshape(HEIGHT, WIDTH, 4)

image = Image.fromarray(
    rgba,
    "RGBA"
)

image.save("household_floorplan.png")

p.disconnect()

print("Saved: household_floorplan.png")
