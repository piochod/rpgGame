import pygame


class Button:
    def __init__(self, x: int, y: int, image_path: str, scale: float = 1.0):
        """A simple clickable button using a Pygame Surface (PNG image)."""
        # Load the image and preserve its transparent background
        img = pygame.image.load(image_path).convert_alpha()

        # Scale the image if needed (default is 1.0 / 100%)
        width = int(img.get_width() * scale)
        height = int(img.get_height() * scale)
        self.image = pygame.transform.scale(img, (width, height))

        # Create the physical hitbox for the mouse
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

        # Prevent the button from firing 60 times a second if you hold the mouse down
        self.clicked = False

    def draw(self, screen: pygame.Surface) -> bool:
        """Draws the button to the screen and returns True exactly once per click."""
        action = False

        # 1. Get the current mouse coordinates
        pos = pygame.mouse.get_pos()

        # 2. Check if the mouse is hovering over the button's hitbox
        if self.rect.collidepoint(pos):
            # 3. Check if Left Mouse Button (index 0) is pressed down
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                self.clicked = True
                action = True  # FIRE THE ACTION!

        # 4. Reset the click state when the player lets go of the mouse button
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        # 5. Draw the button image to the screen
        screen.blit(self.image, (self.rect.x, self.rect.y))

        return action
