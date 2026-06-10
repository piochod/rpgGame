import json


def get_game_config():
    with open("game_config.json", "r", encoding="utf-8") as file:
        return json.load(file)
