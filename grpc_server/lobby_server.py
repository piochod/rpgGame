"""Lobby Service: Handles matchmaking and session management."""

import random
import string
import time
from concurrent import futures

import grpc_server.lobby_pb2 as lobby_pb2
import grpc_server.lobby_pb2_grpc as lobby_pb2_grpc
import grpc
from logger_config import get_logger
from rabbitmq.rabbit_server import publish_event

logger = get_logger(__name__)


class LobbyServiceServicer(lobby_pb2_grpc.LobbyServiceServicer):
    """gRPC servicer for lobby/session management."""

    def __init__(self) -> None:
        # Shared lobby state: {"A7X9": {"infiltrator": "p1", "hacker": "p2"}}
        self.lobbies: dict[str, dict] = {}

    def CreateLobby(
        self, request: lobby_pb2.CreateLobbyRequest, context: grpc.ServicerContext
    ) -> lobby_pb2.LobbyResponse:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))

        self.lobbies[code] = {
            "infiltrator": request.player_id,
            "hacker": None,
        }

        logger.info(f"[LOBBY] Lobby {code} created by Infiltrator: {request.player_id}")
        return lobby_pb2.LobbyResponse(
            success=True, message="Lobby created.", lobby_code=code, assigned_role="Infiltrator"
        )

    def JoinLobby(self, request: lobby_pb2.JoinLobbyRequest, context: grpc.ServicerContext) -> lobby_pb2.LobbyResponse:
        code = request.lobby_code.upper()

        if code not in self.lobbies:
            logger.warning(f"[LOBBY] Failed join attempt. Lobby {code} does not exist.")
            return lobby_pb2.LobbyResponse(
                success=False, message="Invalid lobby code.", lobby_code="", assigned_role=""
            )

        if self.lobbies[code]["hacker"] is not None:
            logger.warning(f"[LOBBY] Failed join attempt. Lobby {code} is full.")
            return lobby_pb2.LobbyResponse(success=False, message="Lobby is full.", lobby_code="", assigned_role="")

        self.lobbies[code]["hacker"] = request.player_id
        logger.info(f"[LOBBY] {request.player_id} joined Lobby {code} as Hacker!")

        publish_event("game_events", {"event": "START_GAME", "lobby_code": code})

        return lobby_pb2.LobbyResponse(
            success=True, message="Successfully joined.", lobby_code=code, assigned_role="Hacker"
        )


def start_server() -> None:
    """Starts the Lobby gRPC server on port 50051."""
    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    lobby_pb2_grpc.add_LobbyServiceServicer_to_server(LobbyServiceServicer(), grpc_server)
    grpc_server.add_insecure_port("[::]:50051")
    grpc_server.start()
    logger.info("[LOBBY] Lobby Service is running on port 50051...")

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        grpc_server.stop(0)
        logger.info("[LOBBY] Lobby Service has stopped.")


if __name__ == "__main__":
    start_server()
