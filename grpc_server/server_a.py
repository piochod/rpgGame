"""Server A: The Physical World Server that handles interactions with the physical environment."""

import random
import string
import time
from concurrent import futures

import grpc_server.heist_pb2 as heist_pb2
import grpc_server.heist_pb2_grpc as heist_pb2_grpc
import grpc
from logger_config import get_logger
from rabbitmq.rabbit_server import publish_event

logger = get_logger(__name__)


class HeistGameServicer(heist_pb2_grpc.HeistGameServicer):
    """gRPC server implementation for Server A, handling physical world interactions."""

    def __init__(self) -> None:
        """Initializes the HeistGameServicer."""
        # Format: {"A7X9": {"infiltrator": "p1", "hacker": "p2", "usb_ready_doors": set(), "opened_doors": set()}}
        self.lobbies: dict[str, dict] = {}

    def createLobby(
        self, request: heist_pb2.CreateLobbyRequest, context: grpc.ServicerContext
    ) -> heist_pb2.LobbyResponse:
        """Host creates a new game session.

        Args:
            request (heist_pb2.CreateLobbyRequest): The gRPC request containing the host's player ID.
            context (grpc.ServicerContext): The gRPC context for the request.

        Returns:
            heist_pb2.LobbyResponse: The response containing the lobby code and assigned role.
        """
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))

        self.lobbies[code] = {
            "infiltrator": request.player_id,
            "hacker": None,
            "usb_ready_doors": set(),
            "opened_doors": set(),
            "disabled_cameras": set(),
        }

        logger.info(f"[SERVER A] Lobby {code} created by Infiltrator: {request.player_id}")
        return heist_pb2.LobbyResponse(
            success=True, message="Lobby created.", lobby_code=code, assigned_role="Infiltrator"
        )

    def joinLobby(self, request: heist_pb2.JoinLobbyRequest, context: grpc.ServicerContext) -> heist_pb2.LobbyResponse:
        """Guest joins an existing game session.

        Args:
            request (heist_pb2.JoinLobbyRequest): The gRPC request containing the lobby code and the guest's player ID.
            context (grpc.ServicerContext): The gRPC context for the request.

        Returns:
            heist_pb2.LobbyResponse: The response containing the lobby code and assigned role.
        """
        code = request.lobby_code.upper()

        if code not in self.lobbies:
            logger.warning(f"[SERVER A] Failed join attempt. Lobby {code} does not exist.")
            return heist_pb2.LobbyResponse(
                success=False, message="Invalid lobby code.", lobby_code="", assigned_role=""
            )

        if self.lobbies[code]["hacker"] is not None:
            logger.warning(f"[SERVER A] Failed join attempt. Lobby {code} is full.")
            return heist_pb2.LobbyResponse(success=False, message="Lobby is full.", lobby_code="", assigned_role="")

        self.lobbies[code]["hacker"] = request.player_id
        logger.info(f"[SERVER A] {request.player_id} joined Lobby {code} as Hacker!")

        publish_event("game_events", {"event": "START_GAME", "lobby_code": code})

        return heist_pb2.LobbyResponse(
            success=True, message="Successfully joined.", lobby_code=code, assigned_role="Hacker"
        )

    def grantNetworkAccess(
        self, request: heist_pb2.AccessRequest, context: grpc.ServicerContext
    ) -> heist_pb2.ActionResponse:
        """Handles the Infiltrator plugging USB at a terminal to enable hacking a specific door.

        Args:
            request (heist_pb2.AccessRequest): The gRPC request with the access point ID, hacker ID, and lobby code.
            context (grpc.ServicerContext): The gRPC context for the request.

        Returns:
            heist_pb2.ActionResponse: The response indicating the success or failure of the network access request.
        """
        code = request.lobby_code
        if code not in self.lobbies:
            return heist_pb2.ActionResponse(success=False, message="Lobby not found.")

        door_id = request.access_point_id
        logger.info(f"[SERVER A | {code}] Infiltrator plugged USB -> enabling hack for {door_id}!")
        self.lobbies[code]["usb_ready_doors"].add(door_id)

        publish_event("game_events", {"event": "USB_PLUGGED", "lobby_code": code, "door_id": door_id})

        return heist_pb2.ActionResponse(success=True, message=f"Network access granted for {door_id}.")

    def unlockDoor(self, request: heist_pb2.TargetRequest, context: grpc.ServicerContext) -> heist_pb2.ActionResponse:
        """Handles the Hacker's request to unlock a door.

        Args:
            request (heist_pb2.TargetRequest): The gRPC request containing the target door ID and lobby code.
            context (grpc.ServicerContext): The gRPC context for the request.

        Returns:
            heist_pb2.ActionResponse: The response indicating the success or failure of the door unlock request.
        """
        code = request.lobby_code
        if code not in self.lobbies:
            return heist_pb2.ActionResponse(success=False, message="Lobby not found.")

        door_id = request.target_id

        if door_id not in self.lobbies[code]["usb_ready_doors"]:
            logger.info(f"[SERVER A | {code}] Hacker tried to open {door_id} before USB was ready!")
            publish_event(
                "game_events",
                {"event": "ALARM", "lobby_code": code, "message": f"Unauthorized hack attempt on {door_id}!"},
            )
            return heist_pb2.ActionResponse(success=False, message=f"USB override required for {door_id}.")

        logger.info(f"[SERVER A | {code}] Hacker successfully opened {door_id}!")
        self.lobbies[code]["opened_doors"].add(door_id)

        publish_event("game_events", {"event": "DOOR_HACKED", "lobby_code": code, "door_id": door_id})

        return heist_pb2.ActionResponse(success=True, message="Door unlocked.")

    def disableCamera(
        self, request: heist_pb2.TargetRequest, context: grpc.ServicerContext
    ) -> heist_pb2.ActionResponse:
        """Handles the Hacker's request to disable a camera.

        Args:
            request (heist_pb2.TargetRequest): The gRPC request containing the target camera ID and lobby code.
            context (grpc.ServicerContext): The gRPC context for the request.

        Returns:
            heist_pb2.ActionResponse: The response indicating the success or failure of the camera disable request.
        """
        code = request.lobby_code
        if code not in self.lobbies:
            return heist_pb2.ActionResponse(success=False, message="Lobby not found.")

        self.lobbies[code]["disabled_cameras"].add(request.target_id)
        logger.info(f"[SERVER A | {code}] Camera {request.target_id} disabled.")
        return heist_pb2.ActionResponse(success=True, message="Camera disabled.")

    def requestVote(self, request: heist_pb2.VoteRequest, context: grpc.ServicerContext) -> heist_pb2.VoteResponse:
        logger.info(f"[SERVER A] Received vote request from {request.requesting_node_id}.")
        return heist_pb2.VoteResponse(vote_granted=True)


def start_server() -> None:
    """Starts the gRPC server for Server A."""
    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    heist_pb2_grpc.add_HeistGameServicer_to_server(HeistGameServicer(), grpc_server)
    grpc_server.add_insecure_port("[::]:50051")
    grpc_server.start()
    logger.info("[SERVER A] Physical World Server is running on port 50051...")

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        grpc_server.stop(0)
        logger.info("[SERVER A] Physical World Server has stopped.")


if __name__ == "__main__":
    start_server()
