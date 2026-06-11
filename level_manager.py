import pygame
from logger_config import get_logger

logger = get_logger(__name__)


class LevelManager:
    """Manages the game map, including dynamic elements like doors and terminals."""

    def __init__(self, raw_map: list[str], tile_size: int) -> None:
        """Initializes the level manager with a raw map and tile size.

        Args:
            raw_map (list[str]): The level map represented as a list of strings.
            tile_size (int): The size of each tile in pixels.
        """
        self.tile_size = tile_size

        self.game_map = [list(row) for row in raw_map]

        self.doors = {}
        self.terminals = {}

        self.solid_blocks = []
        self.terminal_hitboxes = []
        self.vent_hitboxes = []

        self._build_initial_level()

    def _build_initial_level(self) -> None:
        """Scans the map ONCE at startup to populate our O(1) trackers."""
        door_counter = 0
        term_counter = 0

        for row_index, row_list in enumerate(self.game_map):
            for col_index, tile_char in enumerate(row_list):
                x = col_index * self.tile_size
                y = row_index * self.tile_size

                if tile_char == "T":
                    term_id = f"terminal_{term_counter}"
                    self.terminals[term_id] = (row_index, col_index)
                    self.terminal_hitboxes.append(pygame.Rect(x, y, self.tile_size, self.tile_size))
                    term_counter += 1

                if tile_char in ["D", "G"]:
                    door_id = f"door_{door_counter}"
                    self.doors[door_id] = (row_index, col_index)
                    door_counter += 1

                if tile_char == "V":
                    self.vent_hitboxes.append(pygame.Rect(x, y, self.tile_size, self.tile_size))

        self.update_collision_blocks()

    def update_collision_blocks(self) -> None:
        """Rebuilds the collision list. Call this ONLY when the map changes!"""
        self.solid_blocks.clear()
        for row_index, row_list in enumerate(self.game_map):
            for col_index, tile_char in enumerate(row_list):
                if tile_char in ["W", "D", "G", "T"]:
                    x = col_index * self.tile_size
                    y = row_index * self.tile_size
                    self.solid_blocks.append(pygame.Rect(x, y, self.tile_size, self.tile_size))

    def change_door_state(self, door_id: str, new_state: str) -> None:
        """O(1) update! Instantly changes a door's state without scanning the map.

        Args:
            door_id (str): The unique ID of the door to change (e.g., "door_0").
            new_state (str): The new tile character for the door ("D", "G", or "O").
        """
        if door_id in self.doors:
            row, col = self.doors[door_id]

            self.game_map[row][col] = new_state

            self.update_collision_blocks()
        else:
            logger.error(f"Door {door_id} not found!")
