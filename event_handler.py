import random

import pygame
from grcp_server import heist_pb2
from logger_config import get_logger

logger = get_logger(__name__)


def handle_menu_events(event, ui_elements, screen):
    """Handles input events for the MENU state.

    Returns:
        str: The new game state ("MENU", "LOBBY", or "JOIN_INPUT").
    """
    if ui_elements["host_btn"].draw(screen):
        return "HOST"

    if ui_elements["join_btn"].draw(screen):
        return "JOIN_INPUT"

    return "MENU"


def handle_host_events(event, grpc_client, player_id):
    """Handles the host lobby creation via gRPC.

    Returns:
        tuple: (new_game_state, lobby_code)
    """
    req = heist_pb2.CreateLobbyRequest(player_id=player_id)
    res = grpc_client.createLobby(req)
    if res.success:
        return "LOBBY", res.lobby_code
    return "MENU", ""


def handle_join_input_events(event, typed_code, grpc_client, player_id):
    """Handles input events for the JOIN_INPUT state (typing lobby code).

    Returns:
        tuple: (new_game_state, lobby_code, typed_code)
    """
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            return "MENU", "", ""

        if event.key == pygame.K_RETURN and len(typed_code) == 4:
            req = heist_pb2.JoinLobbyRequest(lobby_code=typed_code, player_id=player_id)
            res = grpc_client.joinLobby(req)
            if res.success:
                return "HACKER", res.lobby_code, typed_code

        if event.key == pygame.K_BACKSPACE:
            typed_code = typed_code[:-1]
        elif len(typed_code) < 4 and event.unicode.isalnum():
            typed_code += event.unicode.upper()

    return "JOIN_INPUT", "", typed_code


def handle_lobby_events(event):
    """Handles input events for the LOBBY state.

    Returns:
        str: The new game state ("LOBBY" or "MENU").
    """
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        return "MENU"
    return "LOBBY"


def handle_infiltrator_events(event, player, level_manager, grpc_client, player_id, lobby_code):
    """Handles input events for the INFILTRATOR state."""
    if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
        terminal_pos = level_manager.get_terminal_near_player(player.rect)
        if terminal_pos:
            door_id = level_manager.get_door_for_terminal(terminal_pos)
            if door_id:
                req = heist_pb2.AccessRequest(access_point_id=door_id, hacker_id=player_id, lobby_code=lobby_code)
                grpc_client.grantNetworkAccess(req)
                logger.info(f"Terminal at {terminal_pos} activated -> targeting {door_id}")


def handle_hacker_events(
    event, cursor_x, target_x, hack_progress, cursor_dir, grpc_client, player_id, lobby_code, target_door_id
):
    """Handles input events for the HACKER state.

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
                req = heist_pb2.TargetRequest(target_id=target_door_id, hacker_id=player_id, lobby_code=lobby_code)
                grpc_client.unlockDoor(req)
            else:
                target_x = random.randint(120, 250)
                cursor_dir = (abs(cursor_dir) + 1) * (1 if cursor_dir > 0 else -1)
        else:
            logger.info("Missed! Resetting hack progress.")
            hack_progress = 0
            cursor_dir = 4 if cursor_dir > 0 else -4

    return hack_progress, target_x, cursor_dir, has_hacked
