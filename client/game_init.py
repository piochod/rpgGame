import sys

import grpc
import pygame
from assets.character_helper import CharacterManager
from assets.tile_helper import TileManager
from assets.ui_helper import Button
from client.utils import get_game_config
from grcp_server import heist_pb2_grpc
from logger_config import get_logger

logger = get_logger(__name__)
config = get_game_config()

SCREEN_WIDTH = config["SCREEN_WIDTH"]
SCREEN_HEIGHT = config["SCREEN_HEIGHT"]


def init_display() -> tuple[pygame.Surface, pygame.time.Clock]:
    """Initializes the Pygame display and returns the screen surface and clock object."""
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Cyberpunk Heist: Universal Client")
    clock = pygame.time.Clock()
    return screen, clock


def init_grpc_client() -> heist_pb2_grpc.HeistGameStub:
    """Initializes the gRPC client and returns a stub for making RPC calls to the server."""
    logger.info("Initializing gRPC client...")
    try:
        channel = grpc.insecure_channel("localhost:50051")
        return heist_pb2_grpc.HeistGameStub(channel)
    except Exception as e:
        logger.critical(f"Failed to connect to gRPC server. {e}")
        sys.exit(1)


def load_assets() -> tuple[TileManager, CharacterManager, dict]:
    """Loads game assets and returns the managers and UI elements."""
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
