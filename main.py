import random
import sys

import pygame
from assets.character_helper import Player
from client.event_handler import (
    handle_hacker_events,
    handle_host_events,
    handle_infiltrator_events,
    handle_join_input_events,
    handle_lobby_events,
    handle_menu_events,
)
from client.game_init import init_display, init_grpc_client, load_assets
from client.renderer import render_hacker, render_infiltrator, render_join_input, render_lobby, render_menu
from client.utils import get_game_config, get_levels
from levels.level_manager import LevelManager
from logger_config import get_logger
from rabbitmq.rabbitmq_helper import GameEventSubscriber

logger = get_logger(__name__)

config = get_game_config()
SCREEN_WIDTH = config["SCREEN_WIDTH"]
SCREEN_HEIGHT = config["SCREEN_HEIGHT"]
TILE_SIZE = config["TILE_SIZE"]


def main() -> None:
    screen, clock = init_display()
    grpc_client = init_grpc_client()
    tile_manager, char_manager, ui_elements = load_assets()

    rabbit_subscriber = GameEventSubscriber(host="localhost", exchange_name="game_events")

    fonts = {
        "normal": pygame.font.Font("resources/fonts/Kenney_Future.ttf", 24),
        "narrow": pygame.font.Font("resources/fonts/Kenney_Future_Narrow.ttf", 24),
        "title": pygame.font.Font("resources/fonts/Kenney_Future.ttf", 36),
    }

    tiles = {
        "floor": tile_manager.get("floor_plain"),
        "door_red": tile_manager.get("door_red"),
        "door_green": tile_manager.get("door_green"),
        "door_opened": tile_manager.get("door_opened"),
        "wall": tile_manager.get("wall"),
        "terminal": tile_manager.get("terminal"),
        "vent": tile_manager.get("vent"),
    }

    levels = get_levels()
    current_level_index = 0
    level_data = levels[current_level_index]
    level_map = level_data["map"]

    center_x = (SCREEN_WIDTH // 2) - (TILE_SIZE // 2)
    center_y = (SCREEN_HEIGHT // 2) - (TILE_SIZE // 2)
    player = Player(char_manager, center_x, center_y)
    level_manager = LevelManager(level_map, TILE_SIZE, level_data.get("terminal_door_links", []))

    game_state = "MENU"
    player_id = f"Ghost_{random.randint(100,999)}"
    lobby_code = ""
    typed_code = ""
    is_usb_ready = False

    hack_progress = 0
    cursor_x = 100
    cursor_dir = 4
    target_x = random.randint(120, 250)
    has_hacked = False
    target_door_id = "door_0"

    running = True
    while running:

        for msg in rabbit_subscriber.get_messages():
            if msg.get("lobby_code") == lobby_code:

                if msg.get("event") == "START_GAME" and game_state == "LOBBY":
                    logger.info("Hacker joined! Game starting...")
                    game_state = "INFILTRATOR"

                elif msg.get("event") == "USB_PLUGGED":
                    logger.info("Infiltrator plugged in the USB!")
                    is_usb_ready = True
                    target_door_id = msg.get("door_id", "door_0")
                    if game_state == "INFILTRATOR":
                        level_manager.change_door_state(target_door_id, "G")

                elif msg.get("event") == "DOOR_HACKED":
                    door_id = msg.get("door_id", "door_0")
                    logger.info(f"Hacker opened {door_id}!")
                    if game_state == "INFILTRATOR":
                        level_manager.change_door_state(door_id, "O")
                    is_usb_ready = False
                    hack_progress = 0
                    cursor_x = 100
                    cursor_dir = 4
                    target_x = random.randint(120, 250)
                    has_hacked = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if game_state == "MENU":
                new_state = handle_menu_events(event, ui_elements, screen)
                if new_state == "HOST":
                    new_state, new_lobby = handle_host_events(event, grpc_client, player_id)
                    if new_state == "LOBBY":
                        game_state = "LOBBY"
                        lobby_code = new_lobby
                elif new_state == "JOIN_INPUT":
                    game_state = "JOIN_INPUT"
                    typed_code = ""

            elif game_state == "JOIN_INPUT":
                new_state, new_lobby, typed_code = handle_join_input_events(event, typed_code, grpc_client, player_id)
                if new_state == "HACKER":
                    game_state = "HACKER"
                    lobby_code = new_lobby
                elif new_state == "MENU":
                    game_state = "MENU"

            elif game_state == "LOBBY":
                new_state = handle_lobby_events(event)
                if new_state == "MENU":
                    game_state = "MENU"
                    lobby_code = ""

            elif game_state == "INFILTRATOR":
                handle_infiltrator_events(event, player, level_manager, grpc_client, player_id, lobby_code)

            elif game_state == "HACKER" and is_usb_ready and not has_hacked:
                hack_progress, target_x, cursor_dir, just_hacked = handle_hacker_events(
                    event,
                    cursor_x,
                    target_x,
                    hack_progress,
                    cursor_dir,
                    grpc_client,
                    player_id,
                    lobby_code,
                    target_door_id,
                )
                if just_hacked:
                    has_hacked = True

        if game_state == "MENU":
            render_menu(screen, ui_elements, typed_code, fonts, SCREEN_WIDTH)

        elif game_state == "JOIN_INPUT":
            render_join_input(screen, typed_code, fonts, SCREEN_WIDTH)

        elif game_state == "LOBBY":
            render_lobby(screen, lobby_code, fonts, SCREEN_WIDTH)

        elif game_state == "HACKER":
            if is_usb_ready and not has_hacked:
                cursor_x += cursor_dir
                if cursor_x > 290 or cursor_x < 100:
                    cursor_dir *= -1
            render_hacker(screen, fonts, is_usb_ready, hack_progress, cursor_x, target_x, SCREEN_WIDTH)

        elif game_state == "INFILTRATOR":
            keys = pygame.key.get_pressed()
            player.update(keys, level_manager.solid_blocks)

            if level_manager.check_vent_collision(player.rect):
                current_level_index += 1
                if current_level_index < len(levels):
                    logger.info(
                        f"Entering vent! Loading level: {levels[current_level_index]['name']} " f"(lobby: {lobby_code})"
                    )
                    level_data = levels[current_level_index]
                    level_map = level_data["map"]
                    level_manager = LevelManager(level_map, TILE_SIZE, level_data.get("terminal_door_links", []))
                    player.rect.x = center_x
                    player.rect.y = center_y
                    is_usb_ready = False
                    hack_progress = 0
                    cursor_x = 100
                    cursor_dir = 4
                    target_x = random.randint(120, 250)
                    has_hacked = False
                else:
                    logger.info("All levels complete!")
                    current_level_index -= 1

            render_infiltrator(screen, level_manager, tiles, player)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
