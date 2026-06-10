import sys

import pygame
from assets.character_helper import CharacterManager, Player
from assets.tile_helper import TileManager
from logger_config import get_logger
from utils import get_game_config

logger = get_logger(__name__)

config = get_game_config()
SCREEN_WIDTH = config["SCREEN_WIDTH"]
SCREEN_HEIGHT = config["SCREEN_HEIGHT"]
TILE_SIZE = config["TILE_SIZE"]


def main() -> None:
    """Main function to initialize the game and run the main loop."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Cyberpunk Heist: Graphics Test")
    clock = pygame.time.Clock()

    logger.info("Loading assets...")
    try:
        tile_manager = TileManager("assets/tilesetv1.0.png", "assets/tilesetv1.0_config.json")

        char_manager = CharacterManager(
            "assets/character_maleAdventurer_sheet.png", "assets/character_maleAdventurer_sheet.xml", scale=0.5
        )
    except Exception as e:
        logger.critical(f"Failed to load graphics. {e}")
        sys.exit(1)

    floor_tile = tile_manager.get("floor_plain")
    box_tile = tile_manager.get("door_opened")

    center_x = (SCREEN_WIDTH // 2) - (TILE_SIZE // 2)
    center_y = (SCREEN_HEIGHT // 2) - (TILE_SIZE // 2)
    player = Player(char_manager, center_x, center_y)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        keys = pygame.key.get_pressed()
        player.update(keys)

        screen.fill((0, 0, 0))

        for x in range(0, SCREEN_WIDTH, TILE_SIZE):
            for y in range(0, SCREEN_HEIGHT, TILE_SIZE):
                screen.blit(floor_tile, (x, y))

        screen.blit(box_tile, (center_x + (TILE_SIZE * 2), center_y))

        player.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
