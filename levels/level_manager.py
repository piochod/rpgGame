import pygame
from logger_config import get_logger

logger = get_logger(__name__)


class LevelManager:
    """Manages the game map, including dynamic elements like doors and terminals."""

    def __init__(self, raw_map: list[str], tile_size: int, terminal_door_links: list[dict] | None = None) -> None:
        """Initializes the level manager with a raw map and tile size.

        Args:
            raw_map (list[str]): The level map represented as a list of strings.
            tile_size (int): The size of each tile in pixels.
            terminal_door_links (list): List of {"terminal": [row,col], "door": [row,col]} mappings.
        """
        self.tile_size = tile_size

        self.game_map = [list(row) for row in raw_map]

        self.doors = {}
        self.terminals = {}
        self.vents = {}

        self.solid_blocks = []
        self.terminal_rects = {}
        self.vent_rects = {}

        self._terminal_to_door_pos = {}
        if terminal_door_links:
            for link in terminal_door_links:
                t_pos = tuple(link["terminal"])
                d_pos = tuple(link["door"])
                self._terminal_to_door_pos[t_pos] = d_pos

        self._pos_to_door_id = {}
        self._build_initial_level()

    def _build_initial_level(self) -> None:
        """Scans the map ONCE at startup to populate our O(1) trackers."""
        door_counter = 0
        term_counter = 0
        vent_counter = 0

        for row_index, row_list in enumerate(self.game_map):
            for col_index, tile_char in enumerate(row_list):
                x = col_index * self.tile_size
                y = row_index * self.tile_size

                if tile_char == "T":
                    term_id = f"terminal_{term_counter}"
                    self.terminals[term_id] = (row_index, col_index)
                    self.terminal_rects[(row_index, col_index)] = pygame.Rect(x, y, self.tile_size, self.tile_size)
                    term_counter += 1

                if tile_char in ["D", "G"]:
                    door_id = f"door_{door_counter}"
                    self.doors[door_id] = (row_index, col_index)
                    self._pos_to_door_id[(row_index, col_index)] = door_id
                    door_counter += 1

                if tile_char == "V":
                    vent_id = f"vent_{vent_counter}"
                    self.vents[vent_id] = (row_index, col_index)
                    self.vent_rects[(row_index, col_index)] = pygame.Rect(x, y, self.tile_size, self.tile_size)
                    vent_counter += 1

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

    def check_vent_collision(self, player_rect: pygame.Rect) -> bool:
        """O(1) grid-based check if the player is overlapping any vent tile.

        Args:
            player_rect (pygame.Rect): The player's collision rectangle.

        Returns:
            bool: True if the player's center is on a vent tile.
        """
        row = player_rect.centery // self.tile_size
        col = player_rect.centerx // self.tile_size
        return (row, col) in self.vent_rects

    def check_terminal_collision(self, player_rect: pygame.Rect) -> bool:
        """O(1) grid-based check if the player is near any terminal tile.

        Args:
            player_rect (pygame.Rect): The player's collision rectangle.

        Returns:
            bool: True if a terminal is within the player's reach (3x3 neighborhood).
        """
        reach_box = player_rect.inflate(16, 16)
        row = reach_box.centery // self.tile_size
        col = reach_box.centerx // self.tile_size
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (row + dr, col + dc) in self.terminal_rects:
                    return True
        return False

    def get_terminal_near_player(self, player_rect: pygame.Rect) -> tuple[int, int] | None:
        """Returns the (row, col) of the terminal near the player, or None.

        Args:
            player_rect (pygame.Rect): The player's collision rectangle.

        Returns:
            tuple[int, int] | None: Grid position of the nearby terminal, or None.
        """
        reach_box = player_rect.inflate(16, 16)
        row = reach_box.centery // self.tile_size
        col = reach_box.centerx // self.tile_size
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                check = (row + dr, col + dc)
                if check in self.terminal_rects:
                    return check
        return None

    def get_door_for_terminal(self, terminal_pos: tuple[int, int]) -> str | None:
        """O(1) lookup: returns the door_id that the terminal at this position unlocks.

        Args:
            terminal_pos (tuple[int, int]): The (row, col) grid position of the terminal.

        Returns:
            str | None: The door_id string (e.g. "door_0"), or None if not mapped.
        """
        door_pos = self._terminal_to_door_pos.get(terminal_pos)
        if door_pos is None:
            return None
        return self._pos_to_door_id.get(door_pos)
