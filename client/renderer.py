import pygame
from assets.character_helper import Player
from assets.guard_helper import Guard
from levels.level_manager import LevelManager


def _draw_button_with_text(screen: pygame.Surface, button, text: str, font: pygame.font.Font) -> None:
    """Draws a button and centers text on its blue (top) portion.

    Args:
        screen (pygame.Surface): The surface to draw on.
        button: The Button object to draw.
        text (str): The text to render on the button.
        font (pygame.font.Font): The font to use for rendering the text.
    """
    button.draw(screen)
    btn_rect = button.rect
    # Blue portion is roughly the top 55% of the button
    blue_center_y = btn_rect.y + int(btn_rect.height * 0.28)
    rendered = font.render(text, True, (255, 255, 255))
    screen.blit(rendered, (btn_rect.centerx - rendered.get_width() // 2, blue_center_y - rendered.get_height() // 2))


def render_menu(screen: pygame.Surface, ui_elements: dict, typed_code: str, fonts: dict, screen_width: int) -> None:
    """Renders the main menu screen.

    Args:
        screen (pygame.Surface): The Pygame screen surface.
        ui_elements (dict): Dictionary of UI Button objects.
        typed_code (str): Currently unused on this screen.
        fonts (dict): Dictionary of font objects keyed by name.
        screen_width (int): The width of the screen in pixels.
    """
    screen.fill((20, 20, 30))
    title = fonts["title"].render("CYBERPUNK HEIST", True, (0, 255, 255))
    screen.blit(title, (screen_width // 2 - title.get_width() // 2, 100))

    _draw_button_with_text(screen, ui_elements["host_btn"], "HOST GAME", fonts["normal"])
    _draw_button_with_text(screen, ui_elements["join_btn"], "JOIN GAME", fonts["normal"])


def render_join_input(screen: pygame.Surface, typed_code: str, fonts: dict, screen_width: int) -> None:
    """Renders the join game code input screen.

    Args:
        screen (pygame.Surface): The Pygame screen surface.
        typed_code (str): The lobby code typed so far by the user.
        fonts (dict): Dictionary of font objects keyed by name.
        screen_width (int): The width of the screen in pixels.
    """
    screen.fill((20, 20, 30))
    title = fonts["title"].render("JOIN GAME", True, (0, 255, 255))
    screen.blit(title, (screen_width // 2 - title.get_width() // 2, 100))

    prompt = fonts["normal"].render("ENTER LOBBY CODE:", True, (255, 255, 255))
    screen.blit(prompt, (screen_width // 2 - prompt.get_width() // 2, 220))

    code_text = fonts["normal"].render(f"{typed_code}_", True, (255, 255, 0))
    screen.blit(code_text, (screen_width // 2 - code_text.get_width() // 2, 280))

    hint = fonts["normal"].render("[ENTER] TO JOIN  |  [ESC] TO GO BACK", True, (150, 150, 150))
    screen.blit(hint, (screen_width // 2 - hint.get_width() // 2, 380))


def render_lobby(screen: pygame.Surface, lobby_code: str, fonts: dict, screen_width: int) -> None:
    """Renders the lobby waiting screen.

    Args:
        screen (pygame.Surface): The Pygame screen surface.
        lobby_code (str): The lobby code to display.
        fonts (dict): Dictionary of font objects keyed by name.
        screen_width (int): The width of the screen in pixels.
    """
    screen.fill((20, 20, 30))
    label = fonts["normal"].render("LOBBY CODE", True, (0, 255, 0))
    screen.blit(label, (screen_width // 2 - label.get_width() // 2, 170))

    code = fonts["code"].render(lobby_code, True, (0, 255, 0))
    screen.blit(code, (screen_width // 2 - code.get_width() // 2, 210))

    sub = fonts["normal"].render("WAITING FOR HACKER...", True, (255, 150, 0))
    screen.blit(sub, (screen_width // 2 - sub.get_width() // 2, 300))

    hint = fonts["normal"].render("[ESC] TO GO BACK", True, (150, 150, 150))
    screen.blit(hint, (screen_width // 2 - hint.get_width() // 2, 420))


def render_hacker(
    screen: pygame.Surface,
    fonts: dict,
    is_usb_ready: bool,
    hack_progress: int,
    cursor_x: int,
    target_x: int,
    screen_width: int,
    alarm_active: bool = False,
) -> None:
    """Renders the hacker mini-game screen.

    Args:
        screen (pygame.Surface): The Pygame screen surface.
        fonts (dict): Dictionary of font objects keyed by name.
        is_usb_ready (bool): Whether the USB has been plugged by the infiltrator.
        hack_progress (int): Number of nodes successfully decrypted (0-3).
        cursor_x (int): Current x-position of the moving cursor.
        target_x (int): x-position of the green target zone.
        screen_width (int): The width of the screen in pixels.
        alarm_active (bool): Whether a guard alarm is currently disrupting the hack.
    """
    screen.fill((10, 20, 10))
    title = fonts["normal"].render("CYBER LINK ACTIVE", True, (0, 255, 0))
    screen.blit(title, (screen_width // 2 - title.get_width() // 2, 100))

    if is_usb_ready:
        if hack_progress < 3:
            status = fonts["normal"].render("STATUS: USB CONNECTED - OVERRIDE REQUIRED", True, (0, 255, 255))
            screen.blit(status, (screen_width // 2 - status.get_width() // 2, 180))

            instructions = fonts["normal"].render("PRESS [SPACE] IN THE GREEN ZONE", True, (255, 255, 255))
            screen.blit(instructions, (screen_width // 2 - instructions.get_width() // 2, 230))

            track_rect = pygame.Rect(100, 300, 200, 40)
            pygame.draw.rect(screen, (50, 50, 50), track_rect)

            target_rect = pygame.Rect(target_x, 300, 40, 40)
            pygame.draw.rect(screen, (0, 200, 0), target_rect)

            cursor_rect = pygame.Rect(cursor_x, 290, 10, 60)
            pygame.draw.rect(screen, (255, 255, 255), cursor_rect)

            prog_text = fonts["normal"].render(f"NODES DECRYPTED: {hack_progress} / 3", True, (255, 255, 0))
            screen.blit(prog_text, (screen_width // 2 - prog_text.get_width() // 2, 400))
        else:
            status = fonts["normal"].render("STATUS: ACCESS GRANTED", True, (0, 255, 0))
            screen.blit(status, (screen_width // 2 - status.get_width() // 2, 200))

            door_open_text = fonts["normal"].render("DOOR UNLOCKED", True, (0, 255, 0))
            screen.blit(door_open_text, (screen_width // 2 - door_open_text.get_width() // 2, 300))
    else:
        status = fonts["normal"].render("STATUS: WAITING FOR INFILTRATOR USB...", True, (255, 0, 0))
        screen.blit(status, (screen_width // 2 - status.get_width() // 2, 200))

    if alarm_active:
        alarm_text = fonts["normal"].render("!! ALARM - SIGNAL DISRUPTED !!", True, (255, 40, 40))
        screen.blit(alarm_text, (screen_width // 2 - alarm_text.get_width() // 2, 500))


def render_infiltrator(
    screen: pygame.Surface,
    level_manager: LevelManager,
    tiles: dict,
    player: Player,
    guards: list[Guard] | None = None,
    guard_alerted: bool = False,
    detection_count: int = 0,
    max_detections: int = 3,
    fonts: dict | None = None,
) -> None:
    """Renders the infiltrator screen.

    Args:
        screen (pygame.Surface): The Pygame screen surface.
        level_manager (LevelManager): The current level's manager instance.
        tiles (dict): Dictionary of tile surfaces keyed by name.
        player (Player): The player object to draw.
        guards (list[Guard] | None): The patrolling guards to draw, if any.
        guard_alerted (bool): Whether a guard has recently spotted the player.
        detection_count (int): How many times the player has been detected.
        max_detections (int): Detections allowed before game over.
        fonts (dict | None): Font objects used to draw the detection counter.
    """
    screen.fill((0, 0, 0))
    for row_index, row_list in enumerate(level_manager.game_map):
        for col_index, tile_char in enumerate(row_list):
            x = col_index * level_manager.tile_size
            y = row_index * level_manager.tile_size
            screen.blit(tiles["floor"], (x, y))

            if tile_char == "W":
                screen.blit(tiles["wall"], (x, y))
            elif tile_char == "T":
                screen.blit(tiles["terminal"], (x, y))
            elif tile_char == "V":
                screen.blit(tiles["vent"], (x, y))
            elif tile_char == "D":
                screen.blit(tiles["door_red"], (x, y))
            elif tile_char == "G":
                screen.blit(tiles["door_green"], (x, y))
            elif tile_char == "O":
                screen.blit(tiles["door_opened"], (x, y))

    if guards:
        for guard in guards:
            guard.draw(screen, alerted=guard_alerted)

    player.draw(screen)

    if fonts is not None:
        color = (255, 60, 60) if detection_count >= max_detections - 1 else (255, 255, 255)
        counter = fonts["normal"].render(f"DETECTED: {detection_count} / {max_detections}", True, color)
        screen.blit(counter, (42, 42))


def render_game_over(screen: pygame.Surface, fonts: dict, screen_width: int, screen_height: int) -> None:
    """Renders the game over screen.

    Args:
        screen (pygame.Surface): The Pygame screen surface.
        fonts (dict): Dictionary of font objects keyed by name.
        screen_width (int): The width of the screen in pixels.
        screen_height (int): The height of the screen in pixels.
    """
    screen.fill((25, 0, 0))
    title = fonts["title"].render("GAME OVER", True, (255, 40, 40))
    screen.blit(title, (screen_width // 2 - title.get_width() // 2, screen_height // 2 - 60))

    sub = fonts["normal"].render("THE INFILTRATOR WAS CAUGHT", True, (255, 150, 150))
    screen.blit(sub, (screen_width // 2 - sub.get_width() // 2, screen_height // 2 + 10))

    hint = fonts["normal"].render("[ESC] MAIN MENU", True, (200, 200, 200))
    screen.blit(hint, (screen_width // 2 - hint.get_width() // 2, screen_height // 2 + 70))


def render_game_won(screen: pygame.Surface, fonts: dict, screen_width: int, screen_height: int) -> None:
    """Renders the victory screen.

    Args:
        screen (pygame.Surface): The Pygame screen surface.
        fonts (dict): Dictionary of font objects keyed by name.
        screen_width (int): The width of the screen in pixels.
        screen_height (int): The height of the screen in pixels.
    """
    screen.fill((0, 25, 10))
    title = fonts["title"].render("HEIST COMPLETE", True, (0, 255, 120))
    screen.blit(title, (screen_width // 2 - title.get_width() // 2, screen_height // 2 - 60))

    sub = fonts["normal"].render("YOU ESCAPED WITH THE LOOT", True, (150, 255, 180))
    screen.blit(sub, (screen_width // 2 - sub.get_width() // 2, screen_height // 2 + 10))

    hint = fonts["normal"].render("[ESC] MAIN MENU", True, (200, 200, 200))
    screen.blit(hint, (screen_width // 2 - hint.get_width() // 2, screen_height // 2 + 70))

