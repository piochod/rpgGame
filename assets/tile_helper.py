import json

import pygame
from logger_config import get_logger

logger = get_logger(__name__)


class SpriteSheet:
    """Handles loading and extracting tiles from a sprite sheet."""

    def __init__(self, filename: str) -> None:
        """Loads the sprite sheet image from the specified filename.

        Args:
            filename (str): The file path to the sprite sheet image.
        """
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
    """Manages tile extraction and retrieval from a sprite sheet."""

    def __init__(self, image_path: str, json_path: str) -> None:
        """Initializes the manager and pre-loads all tiles from the JSON config.

        Args:
            image_path (str): The file path to the sprite sheet image.
            json_path (str): The file path to the JSON configuration for tile definitions.
        """
        self.sprite_sheet = SpriteSheet(image_path)
        self.tiles = {}
        self._load_config(json_path)

    def _load_config(self, json_path: str) -> None:
        """Reads the JSON and cuts out the surfaces.

        Args:
            json_path (str): The file path to the JSON configuration for tile definitions."""
        with open(json_path, "r", encoding="utf-8") as file:
            config = json.load(file)

        default_size = config["TILE_SIZE"]
        render_size = config.get("RENDER_SIZE")

        for name, data in config["tiles"].items():
            w = data.get("width", default_size)
            h = data.get("height", default_size)

            tile = self.sprite_sheet.get_tile(data["col"], data["row"], w, h)

            # Sprite sheets authored at a smaller native size (e.g. 16px) can be
            # upscaled to the in-game render size so they fill the tile grid.
            if render_size is not None and (w, h) != (render_size, render_size):
                tile = pygame.transform.scale(tile, (render_size, render_size))

            self.tiles[name] = tile

    def get(self, tile_name: str) -> pygame.Surface:
        """Safely retrieves a tile surface by its name.
        Args:
            tile_name (str): The name of the tile to retrieve.

        Returns:
            pygame.Surface: The surface of the requested tile, or a placeholder if not found.
        """
        if tile_name not in self.tiles:
            logger.warning(f"[WARNING] Tile '{tile_name}' not found in JSON config!")
            error_surf = pygame.Surface((32, 32))
            error_surf.fill((255, 0, 255))
            return error_surf

        return self.tiles[tile_name]
