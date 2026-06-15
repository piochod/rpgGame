"""Helper classes for managing character sprites and player behavior."""

import xml.etree.ElementTree as ET

import pygame


class CharacterManager:
    """Manages character sprites and animations."""

    def __init__(self, image_path: str, xml_path: str, target_size: tuple[int, int] = (32, 32)) -> None:
        """Loads the sprite sheet and uses the XML to extract all named frames.

        Args:
            image_path (str): Path to the character sprite sheet (PNG).
            xml_path (str): Path to the XML file that defines frame names and positions.
            target_size (tuple[int, int]): The desired size for each frame (width, height). Default is (32, 32).
        """
        self.sheet = pygame.image.load(image_path).convert_alpha()
        self.frames = {}
        self.target_size = target_size

        tree = ET.parse(xml_path)
        root = tree.getroot()

        self._generate_frames(target_size, root)

    def _generate_frames(self, target_size: tuple[int, int], root: ET.Element) -> None:
        """Cuts out all frames from the sprite sheet based on the XML data.

        Args:
            target_size (tuple[int, int]): The desired size for each frame (width, height).
            root (ET.Element): The root element of the parsed XML containing frame data.
        """
        for sub in root.findall("SubTexture"):
            name = sub.get("name")
            x = int(sub.get("x"))
            y = int(sub.get("y"))
            w = int(sub.get("width"))
            h = int(sub.get("height"))

            # Cut the original frame out
            rect = pygame.Rect(x, y, w, h)
            image = pygame.Surface((w, h), pygame.SRCALPHA)
            image.blit(self.sheet, (0, 0), rect)

            # --- CHANGED: Force the image to be exactly the target size (32x32) ---
            image = pygame.transform.scale(image, self.target_size)

            self.frames[name] = image


class Player:
    """Represents the player character, handling movement and animation."""

    def __init__(self, char_manager: CharacterManager, start_x: int, start_y: int) -> None:
        """Represents the player character, handling movement and animation.

        Args:
            char_manager (CharacterManager): The manager that holds all character frames.
            start_x (int): The starting x-coordinate of the player.
            start_y (int): The starting y-coordinate of the player.
        """
        self.manager = char_manager
        self.x = start_x
        self.y = start_y
        self.speed = 4
        self.rect = pygame.Rect(start_x, start_y, char_manager.target_size[0], char_manager.target_size[1])

        self.walk_frames = [f"walk{i}" for i in range(8)]  # walk0 to walk7
        self.current_frame_index = 0
        self.animation_timer = 0
        self.animation_speed = 5  # Higher = slower animation

        self.is_moving = False
        self.facing_left = False

    def update(self, keys: pygame.key.ScancodeWrapper, solid_blocks: list[pygame.Rect]) -> None:
        """Updates the player's position and animation based on input and collisions.

        Args:
            keys (pygame.key.ScancodeWrapper): The current state of keyboard keys.
            solid_blocks (list[pygame.Rect]): A list of rectangles representing solid objects for collision.
        """
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

        if dx != 0:
            self.is_moving = True
            self.rect.x += dx
            for block in solid_blocks:
                if self.rect.colliderect(block):
                    if dx > 0:
                        self.rect.right = block.left
                    if dx < 0:
                        self.rect.left = block.right

        if dy != 0:
            self.is_moving = True
            self.rect.y += dy
            for block in solid_blocks:
                if self.rect.colliderect(block):
                    if dy > 0:
                        self.rect.bottom = block.top
                    if dy < 0:
                        self.rect.top = block.bottom

        if self.is_moving:
            self.animation_timer += 1
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame_index = (self.current_frame_index + 1) % len(self.walk_frames)
        else:
            self.current_frame_index = 0

    def draw(self, screen: pygame.Surface) -> None:
        """Draws the player on the screen based on the current animation frame and direction.

        Args:
            screen (pygame.Surface): The surface to draw the player on.
        """
        if self.is_moving:
            frame_name = self.walk_frames[self.current_frame_index]
        else:
            frame_name = "idle"

        img = self.manager.frames[frame_name]
        if self.facing_left:
            img = pygame.transform.flip(img, True, False)

        screen.blit(img, (self.rect.x, self.rect.y))
