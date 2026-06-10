import xml.etree.ElementTree as ET

import pygame


class CharacterManager:
    def __init__(self, image_path: str, xml_path: str, scale: float = 0.5):
        """Loads the sprite sheet and uses the XML to extract all named frames."""
        self.sheet = pygame.image.load(image_path).convert_alpha()
        self.frames = {}

        tree = ET.parse(xml_path)
        root = tree.getroot()

        self._generate_frames(scale, root)

    def _generate_frames(self, scale: float, root: ET.Element) -> None:
        """Cuts out all frames from the sprite sheet based on the XML data."""
        for sub in root.findall("SubTexture"):
            name = sub.get("name")
            x = int(sub.get("x"))
            y = int(sub.get("y"))
            w = int(sub.get("width"))
            h = int(sub.get("height"))

            rect = pygame.Rect(x, y, w, h)
            image = pygame.Surface((w, h), pygame.SRCALPHA)
            image.blit(self.sheet, (0, 0), rect)

            if scale != 1.0:
                new_w, new_h = int(w * scale), int(h * scale)
                image = pygame.transform.scale(image, (new_w, new_h))

            self.frames[name] = image


class Player:
    def __init__(self, char_manager: CharacterManager, start_x: int, start_y: int):
        self.manager = char_manager
        self.x = start_x
        self.y = start_y
        self.speed = 4

        self.walk_frames = [f"walk{i}" for i in range(8)]  # walk0 to walk7
        self.current_frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 5  # Higher = slower animation

        self.is_moving = False
        self.facing_left = False

    def update(self, keys):
        """Handles WASD input and updates animation frames."""
        self.is_moving = False
        dx, dy = 0, 0

        if keys[pygame.K_w]:
            dy -= self.speed
        if keys[pygame.K_s]:
            dy += self.speed
        if keys[pygame.K_a]:
            dx -= self.speed
            self.facing_left = True
        if keys[pygame.K_d]:
            dx += self.speed
            self.facing_left = False

        if dx != 0 or dy != 0:
            self.is_moving = True
            self.x += dx
            self.y += dy

            self.animation_timer += 1
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame_index = (self.current_frame_index + 1) % len(self.walk_frames)
        else:
            self.current_frame_index = 0  # Reset to standing straight

    def draw(self, screen):
        """Draws the current frame of the player onto the screen."""
        if self.is_moving:
            frame_name = self.walk_frames[self.current_frame_index]
        else:
            frame_name = "idle"

        img = self.manager.frames[frame_name]

        if self.facing_left:
            img = pygame.transform.flip(img, True, False)

        screen.blit(img, (self.x, self.y))
