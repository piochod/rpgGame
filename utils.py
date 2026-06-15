import json


def get_game_config():
    with open("game_config.json", "r", encoding="utf-8") as file:
        return json.load(file)


def get_levels():
    """Loads all level definitions from levels.json."""
    with open("levels.json", "r", encoding="utf-8") as file:
        data = json.load(file)
    return data["levels"]


def get_level_by_id(level_id: str):
    """Returns a specific level by its id, or None if not found."""
    levels = get_levels()
    for level in levels:
        if level["id"] == level_id:
            return level
    return None
