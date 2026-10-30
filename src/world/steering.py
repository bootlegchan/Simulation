"""
Continuous Spatial Steering, Collision Avoidance, and Vision Cones.
"""
import math
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Vector2D:
    x: float
    y: float

    def distance_to(self, other: "Vector2D") -> float:
        return math.hypot(other.x - self.x, other.y - self.y)

    def normalize(self) -> "Vector2D":
        dist = math.hypot(self.x, self.y)
        if dist == 0.0:
            return Vector2D(0.0, 0.0)
        return Vector2D(self.x / dist, self.y / dist)

    def dot(self, other: "Vector2D") -> float:
        return self.x * other.x + self.y * other.y

class SteeringAgent:
    """2D steering movement and directional vision cone perception."""

    def __init__(
        self,
        agent_id: str,
        position: Vector2D,
        facing_angle_deg: float = 0.0,
        vision_radius: float = 15.0,
        fov_degrees: float = 120.0
    ):
        self.agent_id = agent_id
        self.position = position
        self.velocity = Vector2D(0.0, 0.0)
        self.facing_angle_deg = facing_angle_deg  # 0 deg = East, 90 deg = North
        self.vision_radius = vision_radius
        self.fov_degrees = fov_degrees

    def is_in_perception_cone(self, target_pos: Vector2D) -> bool:
        """Check if target position lies within distance and field-of-view cone."""
        dist = self.position.distance_to(target_pos)
        if dist > self.vision_radius or dist == 0.0:
            return False

        # Vector to target
        vec_to_target = Vector2D(target_pos.x - self.position.x, target_pos.y - self.position.y).normalize()

        # Agent facing direction vector
        facing_rad = math.radians(self.facing_angle_deg)
        facing_vec = Vector2D(math.cos(facing_rad), math.sin(facing_rad)).normalize()

        # Cosine angle via dot product
        cos_angle = max(-1.0, min(1.0, facing_vec.dot(vec_to_target)))
        angle_diff_deg = math.degrees(math.acos(cos_angle))

        return angle_diff_deg <= (self.fov_degrees / 2.0)

    def seek_and_steer(self, target_pos: Vector2D, max_speed: float = 2.0) -> Vector2D:
        """Compute smooth arrival steering velocity towards target position."""
        dist = self.position.distance_to(target_pos)
        if dist < 0.1:
            self.velocity = Vector2D(0.0, 0.0)
            return self.position

        # Desired velocity
        desired_vec = Vector2D(target_pos.x - self.position.x, target_pos.y - self.position.y).normalize()
        speed = min(max_speed, dist)

        self.velocity = Vector2D(desired_vec.x * speed, desired_vec.y * speed)
        self.position = Vector2D(self.position.x + self.velocity.x, self.position.y + self.velocity.y)

        # Update facing angle
        self.facing_angle_deg = math.degrees(math.atan2(desired_vec.y, desired_vec.x)) % 360.0
        return self.position

    def apply_separation(self, neighbor_positions: List[Vector2D], min_dist: float = 2.0) -> Vector2D:
        """Apply separation force to prevent agent stacking."""
        separation_x = 0.0
        separation_y = 0.0

        for n_pos in neighbor_positions:
            dist = self.position.distance_to(n_pos)
            if 0.0 < dist < min_dist:
                push = (min_dist - dist) / dist
                separation_x += (self.position.x - n_pos.x) * push
                separation_y += (self.position.y - n_pos.y) * push

        self.position = Vector2D(self.position.x + separation_x, self.position.y + separation_y)
        return self.position
