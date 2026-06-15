import pygame


class Button:
    def __init__(self, x: int, y: int, image_path: str, scale: float = 1.0):
        """A simple clickable button using a Pygame Surface (PNG image).

        Args:
            x (int): The x-coordinate of the button's top-left corner.
            y (int): The y-coordinate of the button's top-left corner.
            image_path (str): The file path to the button's image (PNG).
            scale (float): The scaling factor for the button image. Default is 1.0 (no scaling).
        """
        img = pygame.image.load(image_path).convert_alpha()

        width = int(img.get_width() * scale)
        height = int(img.get_height() * scale)
        self.image = pygame.transform.scale(img, (width, height))

        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

        self.clicked = False

    def draw(self, screen: pygame.Surface) -> bool:
        """Draws the button to the screen and returns True exactly once per click."""
        action = False

        pos = pygame.mouse.get_pos()

        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                self.clicked = True
                action = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        screen.blit(self.image, (self.rect.x, self.rect.y))

        return action
