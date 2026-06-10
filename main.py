import sys

import grpc
import pygame
from assets.character_helper import CharacterManager, Player
from assets.tile_helper import TileManager
from grcp_server import heist_pb2, heist_pb2_grpc
from logger_config import get_logger
from utils import get_game_config

logger = get_logger(__name__)

config = get_game_config()
SCREEN_WIDTH = config["SCREEN_WIDTH"]
SCREEN_HEIGHT = config["SCREEN_HEIGHT"]
TILE_SIZE = config["TILE_SIZE"]


LEVEL_MAP = [
    "WWWWWWWWWWWWWWWWWWWWWWWWW",
    "W.......................W",
    "W.......WWWWWWWW........W",
    "W.......W......W........W",
    "W.......W......D........W",
    "W.......W......W........W",
    "W.......WWWWWWWW........W",
    "W.......................W",
    "W.......................W",
    "W.......................W",
    "W.......................W",
    "W...................T...W",
    "W.......................W",
    "W...................WWWWW",
    "W.......................W",
    "W.......................W",
    "W.......................W",
    "W.......................W",
    "WWWWWWWWWWWWWWWWWWWWWWWWW",
]


def init_display() -> tuple[pygame.Surface, pygame.time.Clock]:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Cyberpunk Heist: Graphics Test")
    clock = pygame.time.Clock()
    return screen, clock


def init_grpc_client() -> heist_pb2_grpc.HeistGameStub:
    logger.info("Initializing gRPC client...")
    try:
        channel = grpc.insecure_channel("localhost:50051")
        grpc_client = heist_pb2_grpc.HeistGameStub(channel)
        logger.info("Successfully connected to gRPC server at localhost:50051")
        return grpc_client
    except Exception as e:
        logger.critical(f"Failed to connect to gRPC server. {e}")
        sys.exit(1)


def load_assets() -> tuple[TileManager, CharacterManager]:
    """Load game assets and return the managers.

    Returns:
       tuple[TileManager, CharacterManager]: The tile and character managers with loaded assets.
    """
    logger.info("Loading assets...")
    try:
        tile_manager = TileManager("assets/tilesetv1.0.png", "assets/tilesetv1.0_config.json")
        char_manager = CharacterManager(
            "assets/character_maleAdventurer_sheet.png", "assets/character_maleAdventurer_sheet.xml"
        )
        logger.info("Assets loaded successfully.")
        return tile_manager, char_manager
    except Exception as e:
        logger.critical(f"Failed to load graphics. {e}")
        sys.exit(1)


def build_level(level_map) -> tuple[list[pygame.Rect], list[pygame.Rect]]:
    """Parses the level map and returns lists of solid blocks and terminal positions.

    Args:
        level_map (list[str]): The level map represented as a list of strings.

    Returns:
        tuple[list[pygame.Rect], list[pygame.Rect]]: A tuple containing a list of solid blocks and terminal positions.
    """
    solid_blocks = []
    terminals = []
    for row_index, row_string in enumerate(level_map):
        for col_index, tile_char in enumerate(row_string):
            if tile_char in ("W", "D", "T"):
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE
                solid_blocks.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
                if tile_char == "T":
                    terminals.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
    return solid_blocks, terminals


def handle_events(player: Player, terminals: list[pygame.Rect], grpc_client: heist_pb2_grpc.HeistGameStub) -> bool:
    """Process pygame events. Returns False when the game should quit.

    Args:
        player (Player): The player object to check interactions with.
        terminals (list[pygame.Rect]): A list of terminal positions to check for interactions.
        grpc_client (heist_pb2_grpc.HeistGameStub): The gRPC client to send requests when interacting with terminals.

    Returns:
        bool: False if the game should quit, True otherwise.
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            reach_box = player.rect.inflate(16, 16)
            terminal_index = reach_box.collidelist(terminals)
            if terminal_index != -1:
                logger.info("Player pressed E next to the terminal!")
                try:
                    net_req = heist_pb2.AccessRequest(access_point_id="lobby", hacker_id="ghost_1")
                    response = grpc_client.grantNetworkAccess(net_req)
                    logger.info(f"Server Responded: {response.success} | {response.message}")
                except Exception as e:
                    logger.error(f"gRPC Call Failed. Error: {e}")
    return True


def render(screen: pygame.Surface, level_map: list[str], tiles: dict[str, pygame.Surface], player: Player) -> None:
    """Render the game screen.

    Args:
        screen (pygame.Surface): The screen surface to draw on.
        level_map (list[str]): The level map represented as a list of strings.
        tiles (dict[str, pygame.Surface]): A dictionary of tile surfaces.
        player (Player): The player object to draw.
    """
    screen.fill((0, 0, 0))
    for row_index, row_string in enumerate(level_map):
        for col_index, tile_char in enumerate(row_string):
            x = col_index * TILE_SIZE
            y = row_index * TILE_SIZE
            screen.blit(tiles["floor"], (x, y))
            if tile_char == "W":
                screen.blit(tiles["wall"], (x, y))
            elif tile_char == "D":
                screen.blit(tiles["door_closed"], (x, y))
            elif tile_char == "T":
                screen.blit(tiles["terminal"], (x, y))
    player.draw(screen)
    pygame.display.flip()


def main() -> None:
    screen, clock = init_display()
    grpc_client = init_grpc_client()

    tile_manager, char_manager = load_assets()
    tiles = {
        "floor": tile_manager.get("floor_plain"),
        "door_closed": tile_manager.get("door_closed"),
        "wall": tile_manager.get("wall"),
        "terminal": tile_manager.get("terminal"),
    }

    center_x = (SCREEN_WIDTH // 2) - (TILE_SIZE // 2)
    center_y = (SCREEN_HEIGHT // 2) - (TILE_SIZE // 2)
    player = Player(char_manager, center_x, center_y)

    solid_blocks, terminals = build_level(LEVEL_MAP)

    running = True
    while running:
        running = handle_events(player, terminals, grpc_client)
        keys = pygame.key.get_pressed()
        player.update(keys, solid_blocks)
        render(screen, LEVEL_MAP, tiles, player)
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
