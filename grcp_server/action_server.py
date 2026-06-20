"""Action Service: Handles all in-game hacker and infiltrator actions."""

import time
from concurrent import futures

import grcp_server.action_pb2 as action_pb2
import grcp_server.action_pb2_grpc as action_pb2_grpc
import grpc
from logger_config import get_logger
from rabbitmq.rabbit_server import publish_event

logger = get_logger(__name__)


class ActionServiceServicer(action_pb2_grpc.ActionServiceServicer):
    """gRPC servicer for in-game actions (hacker + infiltrator)."""

    def __init__(self) -> None:
        """Initializes the ActionServiceServicer with per-lobby game state tracking.
        Format: {"A7X9": {"usb_ready_doors": set(), "opened_doors": set(), "disabled_cameras": set()}}
        """
        self.lobby_state: dict[str, dict] = {}

    def _get_or_create_state(self, lobby_code: str) -> dict:
        """Gets or initializes the game state for a lobby."""
        if lobby_code not in self.lobby_state:
            self.lobby_state[lobby_code] = {
                "usb_ready_doors": set(),
                "opened_doors": set(),
                "disabled_cameras": set(),
            }
        return self.lobby_state[lobby_code]

    def GrantNetworkAccess(
        self, request: action_pb2.AccessRequest, context: grpc.ServicerContext
    ) -> action_pb2.ActionResponse:
        """Handles the Infiltrator plugging in the USB to grant network access for hacking."""
        code = request.lobby_code
        state = self._get_or_create_state(code)

        door_id = request.access_point_id
        logger.info(f"[ACTION | {code}] Infiltrator plugged USB -> enabling hack for {door_id}!")
        state["usb_ready_doors"].add(door_id)

        publish_event("game_events", {"event": "USB_PLUGGED", "lobby_code": code, "door_id": door_id})

        return action_pb2.ActionResponse(success=True, message=f"Network access granted for {door_id}.")

    def UnlockDoor(self, request: action_pb2.TargetRequest, context: grpc.ServicerContext) -> action_pb2.ActionResponse:
        """Handles the Hacker attempting to unlock a door."""
        code = request.lobby_code
        state = self._get_or_create_state(code)
        door_id = request.target_id

        if door_id not in state["usb_ready_doors"]:
            logger.info(f"[ACTION | {code}] Hacker tried to open {door_id} before USB was ready!")
            publish_event(
                "game_events",
                {"event": "ALARM", "lobby_code": code, "message": f"Unauthorized hack attempt on {door_id}!"},
            )
            return action_pb2.ActionResponse(success=False, message=f"USB override required for {door_id}.")

        logger.info(f"[ACTION | {code}] Hacker successfully opened {door_id}!")
        state["opened_doors"].add(door_id)

        publish_event("game_events", {"event": "DOOR_HACKED", "lobby_code": code, "door_id": door_id})

        return action_pb2.ActionResponse(success=True, message="Door unlocked.")

    def DisableCamera(
        self, request: action_pb2.TargetRequest, context: grpc.ServicerContext
    ) -> action_pb2.ActionResponse:
        """Handles the Hacker attempting to disable a camera."""
        code = request.lobby_code
        state = self._get_or_create_state(code)

        state["disabled_cameras"].add(request.target_id)
        logger.info(f"[ACTION | {code}] Camera {request.target_id} disabled.")
        return action_pb2.ActionResponse(success=True, message="Camera disabled.")

    def DisableLaser(
        self, request: action_pb2.TargetRequest, context: grpc.ServicerContext
    ) -> action_pb2.ActionResponse:
        """Handles the Hacker attempting to disable a laser."""
        code = request.lobby_code
        logger.info(f"[ACTION | {code}] Laser {request.target_id} disabled.")
        return action_pb2.ActionResponse(success=True, message="Laser disabled.")


def start_server() -> None:
    """Starts the Action gRPC server on port 50052."""
    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    action_pb2_grpc.add_ActionServiceServicer_to_server(ActionServiceServicer(), grpc_server)
    grpc_server.add_insecure_port("[::]:50052")
    grpc_server.start()
    logger.info("[ACTION] Action Service is running on port 50052...")

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        grpc_server.stop(0)
        logger.info("[ACTION] Action Service has stopped.")


if __name__ == "__main__":
    start_server()
