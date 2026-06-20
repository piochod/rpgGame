import random

import pygame
from assets.character_helper import Player
from grcp_server import action_pb2, lobby_pb2
from levels.level_manager import LevelManager
from logger_config import get_logger

logger = get_logger(__name__)


def handle_menu_events(event: pygame.event.Event, ui_elements: dict, screen: pygame.Surface) -> str:
    """Handles input events for the MENU state.

    Args:
        event (pygame.event.Event): The Pygame event to handle.
        ui_elements (dict): The dictionary of UI elements (buttons) to check for interactions.
        screen (pygame.Surface): The Pygame surface to draw on (used for button rendering

    Returns:
        str: The new game state ("MENU", "LOBBY", or "JOIN_INPUT").
    """
    if ui_elements["host_btn"].draw(screen):
        return "HOST"

    if ui_elements["join_btn"].draw(screen):
        return "JOIN_INPUT"

    return "MENU"


def handle_host_events(event: pygame.event.Event, grpc_client, player_id: str) -> tuple[str, str]:
    """Handles the host lobby creation via gRPC.

    Args:
        event (pygame.event.Event): The Pygame event to handle.
        grpc_client: The gRPC client stub for making RPC calls.
        player_id (str): The unique identifier for the player hosting the game.

    Returns:
        tuple: (new_game_state, lobby_code)
    """
    req = lobby_pb2.CreateLobbyRequest(player_id=player_id)
    res = grpc_client.lobby.CreateLobby(req)
    if res.success:
        return "LOBBY", res.lobby_code
    return "MENU", ""


def handle_join_input_events(
    event: pygame.event.Event, typed_code: str, grpc_client, player_id: str
) -> tuple[str, str, str]:
    """Handles input events for the JOIN_INPUT state (typing lobby code).

    Args:
        event (pygame.event.Event): The Pygame event to handle.
        typed_code (str): The current lobby code being typed by the player.
        grpc_client: The gRPC client stub for making RPC calls.
        player_id (str): The unique identifier for the player trying to join.

    Returns:
        tuple: (new_game_state, lobby_code, typed_code)
    """
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            return "MENU", "", ""

        if event.key == pygame.K_RETURN and len(typed_code) == 4:
            req = lobby_pb2.JoinLobbyRequest(lobby_code=typed_code, player_id=player_id)
            res = grpc_client.lobby.JoinLobby(req)
            if res.success:
                return "HACKER", res.lobby_code, typed_code

        if event.key == pygame.K_BACKSPACE:
            typed_code = typed_code[:-1]
        elif len(typed_code) < 4 and event.unicode.isalnum():
            typed_code += event.unicode.upper()

    return "JOIN_INPUT", "", typed_code


def handle_lobby_events(event: pygame.event.Event) -> str:
    """Handles input events for the LOBBY state.

    Args:
        event (pygame.event.Event): The Pygame event to handle.

    Returns:
        str: The new game state ("LOBBY" or "MENU").
    """
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        return "MENU"
    return "LOBBY"


def handle_infiltrator_events(
    event: pygame.event.Event, player: Player, level_manager: LevelManager, grpc_client, player_id: str, lobby_code: str
) -> None:
    """Handles input events for the INFILTRATOR state.

    Args:
        event (pygame.event.Event): The Pygame event to handle.
        player (Player): The player object representing the infiltrator.
        level_manager (LevelManager): The manager for the current level, used for collision and interaction checks.
        grpc_client: The gRPC client stub for making RPC calls.
        player_id (str): The unique identifier for the infiltrator player.
        lobby_code (str): The code of the lobby the player is in.
    """
    if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
        terminal_pos = level_manager.get_terminal_near_player(player.rect)
        if terminal_pos:
            door_id = level_manager.get_door_for_terminal(terminal_pos)
            if door_id:
                req = action_pb2.AccessRequest(access_point_id=door_id, hacker_id=player_id, lobby_code=lobby_code)
                grpc_client.action.GrantNetworkAccess(req)
                logger.info(f"Terminal at {terminal_pos} activated -> targeting {door_id}")


def handle_hacker_events(
    event: pygame.event.Event,
    cursor_x: int,
    target_x: int,
    hack_progress: int,
    cursor_dir: int,
    grpc_client,
    player_id: str,
    lobby_code: str,
    target_door_id: str,
) -> tuple[int, int, int, bool]:
    """Handles input events for the HACKER state.

    Args:
        event (pygame.event.Event): The Pygame event to handle.
        cursor_x (int): The current x-position of the hacking cursor.
        target_x (int): The x-position of the current hack node target.
        hack_progress (int): The current progress of the hack (number of nodes secured).
        cursor_dir (int): The current direction/speed of the cursor movement.
        grpc_client: The gRPC client stub for making RPC calls.
        player_id (str): The unique identifier for the hacker player.
        lobby_code (str): The code of the lobby the player is in.
        target_door_id (str): The ID of the door being targeted for unlocking.

    Returns:
        tuple: (hack_progress, target_x, cursor_dir, has_hacked)
    """
    has_hacked = False

    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
        if target_x <= (cursor_x + 5) <= (target_x + 40):
            logger.info("Hack Node Secured!")
            hack_progress += 1

            if hack_progress >= 3:
                logger.info(f"Hack Complete! Unlocking {target_door_id}...")
                has_hacked = True
                req = action_pb2.TargetRequest(target_id=target_door_id, hacker_id=player_id, lobby_code=lobby_code)
                grpc_client.action.UnlockDoor(req)
            else:
                target_x = random.randint(120, 250)
                cursor_dir = (abs(cursor_dir) + 1) * (1 if cursor_dir > 0 else -1)
        else:
            logger.info("Missed! Resetting hack progress.")
            hack_progress = 0
            cursor_dir = 4 if cursor_dir > 0 else -4

    return hack_progress, target_x, cursor_dir, has_hacked
