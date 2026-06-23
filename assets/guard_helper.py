"""Guard robot that patrols the map with a directional field-of-view cone."""

import math
import random

import pygame
from assets.tile_helper import SpriteSheet

ROBOT_NATIVE_SIZE = 16
ROBOT_SHEET_COL = 10
ROBOT_SHEET_ROWS = (1, 2, 3)


class Guard:
    """A patrolling guard robot that detects the player within a line-of-sight cone."""

    def __init__(
        self,
        sheet_path: str,
        start_x: int,
        start_y: int,
        tile_size: int,
        fov_range: int | None = None,
        fov_half_angle: int = 35,
        speed: int = 1,
    ) -> None:
        """Creates a guard at the given pixel position.

        Args:
            sheet_path (str): Path to the sprite sheet containing the robot frames.
            start_x (int): Starting x pixel coordinate.
            start_y (int): Starting y pixel coordinate.
            tile_size (int): The game tile size; the robot is scaled to this size.
            fov_range (int | None): Vision range in pixels. Defaults to 4 tiles.
            fov_half_angle (int): Half-width of the vision cone in degrees.
            speed (int): Movement speed in pixels per frame.
        """
        self.tile_size = tile_size
        self.speed = speed
        self.fov_range = fov_range if fov_range is not None else tile_size * 4
        self.fov_half_angle = fov_half_angle

        sheet = SpriteSheet(sheet_path)
        self.frames: list[pygame.Surface] = []
        for row in ROBOT_SHEET_ROWS:
            tile = sheet.get_tile(ROBOT_SHEET_COL, row, ROBOT_NATIVE_SIZE, ROBOT_NATIVE_SIZE)
            self.frames.append(pygame.transform.scale(tile, (tile_size, tile_size)))

        self.frame_index = 0
        self.anim_timer = 0
        self.anim_speed = 8

        self.x = float(start_x)
        self.y = float(start_y)
        self.rect = pygame.Rect(start_x, start_y, tile_size, tile_size)

        self._directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        self.direction = random.choice(self._directions)
        self._steps_until_turn = random.randint(30, 90)

    def _is_blocked(self, rect: pygame.Rect, solid_blocks: list[pygame.Rect]) -> bool:
        """Returns True if the rect overlaps any solid block."""
        return any(rect.colliderect(block) for block in solid_blocks)

    def _pick_new_direction(self, solid_blocks: list[pygame.Rect]) -> None:
        """Chooses a new movement direction that is not immediately blocked."""
        options = []
        for d in self._directions:
            test_rect = self.rect.move(d[0] * self.speed, d[1] * self.speed)
            if not self._is_blocked(test_rect, solid_blocks):
                options.append(d)

        reverse = (-self.direction[0], -self.direction[1])
        non_reverse = [d for d in options if d != reverse]

        if non_reverse:
            self.direction = random.choice(non_reverse)
        elif options:
            self.direction = random.choice(options)

    def update(self, solid_blocks: list[pygame.Rect]) -> None:
        """Advances the guard's patrol movement and animation by one frame.

        Args:
            solid_blocks (list[pygame.Rect]): Solid map tiles used for collision.
        """
        self.anim_timer += 1
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)

        self._steps_until_turn -= 1
        if self._steps_until_turn <= 0:
            self._pick_new_direction(solid_blocks)
            self._steps_until_turn = random.randint(30, 90)

        dx = self.direction[0] * self.speed
        dy = self.direction[1] * self.speed
        new_rect = self.rect.move(dx, dy)

        if self._is_blocked(new_rect, solid_blocks):
            self._pick_new_direction(solid_blocks)
        else:
            self.x += dx
            self.y += dy
            self.rect.x = round(self.x)
            self.rect.y = round(self.y)

    def get_fov_polygon(self, num_points: int = 14) -> list[tuple[float, float]]:
        """Returns the polygon points describing the vision cone for rendering.

        Args:
            num_points (int): Number of arc samples along the far edge of the cone.

        Returns:
            list[tuple[float, float]]: Polygon vertices, apex first.
        """
        cx, cy = self.rect.center
        center_angle = math.atan2(self.direction[1], self.direction[0])
        half = math.radians(self.fov_half_angle)

        points: list[tuple[float, float]] = [(cx, cy)]
        for i in range(num_points + 1):
            angle = center_angle - half + (2 * half) * (i / num_points)
            px = cx + math.cos(angle) * self.fov_range
            py = cy + math.sin(angle) * self.fov_range
            points.append((px, py))
        return points

    def sees_player(self, player_rect: pygame.Rect, solid_blocks: list[pygame.Rect]) -> bool:
        """Returns True if the player is inside the cone with an unobstructed line of sight.

        Args:
            player_rect (pygame.Rect): The player's collision rectangle.
            solid_blocks (list[pygame.Rect]): Solid map tiles that block line of sight.

        Returns:
            bool: True if the player is currently spotted.
        """
        cx, cy = self.rect.center
        px, py = player_rect.center
        dx, dy = px - cx, py - cy
        dist = math.hypot(dx, dy)

        if dist == 0 or dist > self.fov_range:
            return False

        center_angle = math.atan2(self.direction[1], self.direction[0])
        target_angle = math.atan2(dy, dx)
        diff = abs((target_angle - center_angle + math.pi) % (2 * math.pi) - math.pi)
        if diff > math.radians(self.fov_half_angle):
            return False

        steps = max(1, int(dist // (self.tile_size / 4)))
        for i in range(1, steps):
            t = i / steps
            sample = (cx + dx * t, cy + dy * t)
            for block in solid_blocks:
                if block.collidepoint(sample):
                    return False
        return True

    def draw(self, screen: pygame.Surface, alerted: bool = False) -> None:
        """Draws the vision cone and the robot sprite.

        Args:
            screen (pygame.Surface): The surface to draw on.
            alerted (bool): When True, the cone is rendered red to signal detection.
        """
        cone_color = (255, 40, 40, 90) if alerted else (255, 230, 90, 60)
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(overlay, cone_color, self.get_fov_polygon())
        screen.blit(overlay, (0, 0))

        screen.blit(self.frames[self.frame_index], (self.rect.x, self.rect.y))
