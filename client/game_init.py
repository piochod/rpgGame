import sys
from dataclasses import dataclass

import grpc
import pygame
from assets.character_helper import CharacterManager
from assets.tile_helper import TileManager
from assets.ui_helper import Button
from client.utils import get_game_config
from grpc_server import action_pb2_grpc, lobby_pb2_grpc
from logger_config import get_logger

logger = get_logger(__name__)
config = get_game_config()

SCREEN_WIDTH = config["SCREEN_WIDTH"]
SCREEN_HEIGHT = config["SCREEN_HEIGHT"]


@dataclass
class GrpcClients:
    """Container for all gRPC service stubs."""

    lobby: lobby_pb2_grpc.LobbyServiceStub
    action: action_pb2_grpc.ActionServiceStub


def init_display() -> tuple[pygame.Surface, pygame.time.Clock]:
    """Initializes the Pygame display and returns the screen surface and clock object.

    Returns:
        tuple: A tuple containing the Pygame screen surface and clock object.
    """
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Cyberpunk Heist: Universal Client")
    clock = pygame.time.Clock()
    return screen, clock


def init_grpc_client() -> GrpcClients:
    """Initializes gRPC channels and returns stubs for all microservices.

    Returns:
        GrpcClients: Container with stubs for lobby and action services.
    """
    logger.info("Initializing gRPC clients...")
    try:
        lobby_channel = grpc.insecure_channel("localhost:50051")
        action_channel = grpc.insecure_channel("localhost:50052")

        return GrpcClients(
            lobby=lobby_pb2_grpc.LobbyServiceStub(lobby_channel),
            action=action_pb2_grpc.ActionServiceStub(action_channel),
        )
    except Exception as e:
        logger.critical(f"Failed to connect to gRPC servers. {e}")
        sys.exit(1)


def load_assets() -> tuple[TileManager, CharacterManager, dict]:
    """Loads game assets and returns the managers and UI elements.

    Returns:
        tuple: A tuple containing the TileManager, CharacterManager, and a dictionary of UI elements.
    """
    logger.info("Loading assets...")
    try:
        tile_manager = TileManager("resources/tilesetv1.0.png", "resources/tilesetv1.0_config.json")
        char_manager = CharacterManager(
            "resources/character_maleAdventurer_sheet.png", "resources/character_maleAdventurer_sheet.xml"
        )

        btn_path = "resources/ui_textures/button_square_header_large_rectangle.png"
        ui_elements = {
            "host_btn": Button(SCREEN_WIDTH // 2 - 95, 250, btn_path),
            "join_btn": Button(SCREEN_WIDTH // 2 - 95, 350, btn_path),
            "hack_btn": Button(SCREEN_WIDTH // 2 - 95, 300, btn_path),
        }

        return tile_manager, char_manager, ui_elements
    except Exception as e:
        logger.critical(f"Failed to load assets. {e}")
        sys.exit(1)
