import json


def get_game_config() -> dict[str, int]:
    """Loads the game configuration from game_config.json.

    Returns:
        dict: The game configuration dictionary containing SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE.
    """
    with open("game_config.json", "r", encoding="utf-8") as file:
        return json.load(file)


def get_levels() -> list[dict[str, any]]:
    """Loads all level definitions from levels.json.

    Returns:
        list[dict]: A list of level dictionaries, each containing id, name, map, and terminal_door_links.
    """
    with open("levels/levels.json", "r", encoding="utf-8") as file:
        data = json.load(file)
    return data["levels"]


def get_level_by_id(level_id: str) -> dict[str, any] | None:
    """Returns a specific level by its id, or None if not found.

    Args:
        level_id (str): The unique level identifier (e.g. "heist_01").

    Returns:
        dict | None: The level dictionary if found, otherwise None.
    """
    levels = get_levels()
    for level in levels:
        if level["id"] == level_id:
            return level
    return None
