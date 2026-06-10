import json

import pygame
from logger_config import get_logger

logger = get_logger(__name__)


class SpriteSheet:
    def __init__(self, filename: str) -> None:
        """Loads the sprite sheet image from the specified filename."""
        self.sheet = pygame.image.load(filename).convert_alpha()

    def get_tile(self, col: int, row: int, width: int, height: int) -> pygame.Surface:
        """Extracts a tile from the sprite sheet based on column, row, width, and height.

        Args:
            col (int): The column index of the tile in the sprite sheet.
            row (int): The row index of the tile in the sprite sheet.
            width (int): The width of the tile in pixels.
            height (int): The height of the tile in pixels.

        Returns:
            pygame.Surface: A new surface containing the extracted tile.
        """
        image = pygame.Surface((width, height), pygame.SRCALPHA)

        x = col * width
        y = row * height
        rect = pygame.Rect(x, y, width, height)

        image.blit(self.sheet, (0, 0), rect)
        return image


class TileManager:
    def __init__(self, image_path: str, json_path: str):
        """Initializes the manager and pre-loads all tiles from the JSON config."""
        self.sprite_sheet = SpriteSheet(image_path)
        self.tiles = {}
        self._load_config(json_path)

    def _load_config(self, json_path: str) -> None:
        """Reads the JSON and cuts out the surfaces."""
        with open(json_path, "r") as file:
            config = json.load(file)

        default_size = config["TILE_SIZE"]

        # Loop through every tile in the JSON
        for name, data in config["tiles"].items():
            # Use specific width/height if provided, otherwise use default
            w = data.get("width", default_size)
            h = data.get("height", default_size)

            # Cut it out and save it in the dictionary
            self.tiles[name] = self.sprite_sheet.get_tile(data["col"], data["row"], w, h)

    def get(self, tile_name: str) -> pygame.Surface:
        """Safely retrieves a tile surface by its name."""
        if tile_name not in self.tiles:
            logger.warning(f"[WARNING] Tile '{tile_name}' not found in JSON config!")
            # Return a blank pink square so you instantly know a texture is missing
            error_surf = pygame.Surface((32, 32))
            error_surf.fill((255, 0, 255))
            return error_surf

        return self.tiles[tile_name]
