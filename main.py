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


def main() -> None:
    """Main function to initialize the game and run the main loop."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Cyberpunk Heist: Graphics Test")
    clock = pygame.time.Clock()

    logger.info("Initializing gRPC client...")
    try:
        channel = grpc.insecure_channel("localhost:50051")
        grpc_client = heist_pb2_grpc.HeistGameStub(channel)
        logger.info("Successfully connected to gRPC server at localhost:50051")
    except Exception as e:
        logger.critical(f"Failed to connect to gRPC server. {e}")
        sys.exit(1)

    logger.info("Loading assets...")
    try:
        tile_manager = TileManager("assets/tilesetv1.0.png", "assets/tilesetv1.0_config.json")

        char_manager = CharacterManager(
            "assets/character_maleAdventurer_sheet.png", "assets/character_maleAdventurer_sheet.xml"
        )
        logger.info("Assets loaded successfully.")
    except Exception as e:
        logger.critical(f"Failed to load graphics. {e}")
        sys.exit(1)

    floor_tile = tile_manager.get("floor_plain")
    door_closed_tile = tile_manager.get("door_closed")
    wall_tile = tile_manager.get("wall")
    terminal_tile = tile_manager.get("terminal")

    center_x = (SCREEN_WIDTH // 2) - (TILE_SIZE // 2)
    center_y = (SCREEN_HEIGHT // 2) - (TILE_SIZE // 2)
    player = Player(char_manager, center_x, center_y)

    solid_blocks = []
    terminals = []

    for row_index, row_string in enumerate(LEVEL_MAP):
        for col_index, tile_char in enumerate(row_string):
            if tile_char in ["W", "D", "T"]:
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE
                solid_blocks.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))

            if tile_char == "T":
                terminals.append(pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
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

        keys = pygame.key.get_pressed()
        player.update(keys, solid_blocks)

        screen.fill((0, 0, 0))

        for row_index, row_string in enumerate(LEVEL_MAP):
            for col_index, tile_char in enumerate(row_string):
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE
                screen.blit(floor_tile, (x, y))

                if tile_char == "W":
                    screen.blit(wall_tile, (x, y))
                elif tile_char == "D":
                    screen.blit(door_closed_tile, (x, y))
                elif tile_char == "T":
                    screen.blit(terminal_tile, (x, y))

        player.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
