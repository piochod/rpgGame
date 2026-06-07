"""Server A: The Physical World Server that handles interactions with the physical environment."""
import time
from concurrent import futures
import grpc
import heist_pb2
import heist_pb2_grpc
from logger_config import get_logger


logger = get_logger(__name__)


class HeistGameServicer(heist_pb2_grpc.HeistGameServicer):
    """gRPC server implementation for Server A, handling physical world interactions."""
    def __init__(self) -> None:
        """Initializes the HeistGameServicer."""
        self._door_zones = {
            "door_01": "lobby",
            "door_02": "lobby",
            "door_server_room": "basement",
            "door_vault": "vault_level"
        }
        self._zone_usb_status = {
            "lobby": False,
            "basement": False,
            "vault_level": False
        }
        self._disabled_cameras: set[str] = set()
        self._opened_doors: set[str] = set()

    def unlockDoor(self, request: heist_pb2.TargetRequest, context: grpc.ServicerContext) -> heist_pb2.ActionResponse:
        """Handles door unlock requests from hackers."""
        logger.info(f"[SERVER A] Received hack attempt from {request.hacker_id} for {request.target_id}...")

        if request.target_id not in self._door_zones:
            logger.warning(f"[SERVER A] Door {request.target_id} does not exist.")
            return heist_pb2.ActionResponse(success=False, message="Invalid door ID.")

        target_zone = self._door_zones[request.target_id]

        if not self._zone_usb_status[target_zone]:
            logger.info(f"[SERVER A] USB not plugged in for {target_zone}. Access denied to {request.target_id}.")
            return heist_pb2.ActionResponse(success=False, message=f"USB override required for {target_zone}.")

        logger.info(f"[SERVER A] USB is plugged in for {target_zone}. Unlocking {request.target_id}...")
        self._opened_doors.add(request.target_id)
        return heist_pb2.ActionResponse(success=True, message="Door unlocked.")

    def disableCamera(self, request: heist_pb2.TargetRequest, context: grpc.ServicerContext) -> heist_pb2.ActionResponse:
        """Handles camera disable requests from hackers."""
        logger.info(f"[SERVER A] Received camera disable request from {request.hacker_id} for {request.target_id}...")
        self._disabled_cameras.add(request.target_id)
        logger.info(f"[SERVER A] Camera {request.target_id} disabled.")
        return heist_pb2.ActionResponse(success=True, message="Camera disabled.")

    def grantNetworkAccess(self, request: heist_pb2.AccessRequest, context: grpc.ServicerContext) -> heist_pb2.ActionResponse:
        """Handles network access grant requests from hackers."""
        target_zone = request.access_point_id

        if target_zone not in self._zone_usb_status:
            return heist_pb2.ActionResponse(success=False, message="Invalid access point.")

        logger.info(f"[SERVER A] Infiltrator plugged USB into {target_zone}!")

        self._zone_usb_status[target_zone] = True
        return heist_pb2.ActionResponse(success=True, message=f"Network access granted for {target_zone}.")

    def requestVote(self, request: heist_pb2.VoteRequest, context: grpc.ServicerContext) -> heist_pb2.VoteResponse:
        """Handles Maekawa algorithm vote requests for mutual exclusion."""
        # Placeholder for your Maekawa algorithm
        logger.info(f"[SERVER A] Received vote request from {request.hacker_id}.")
        return heist_pb2.VoteResponse(vote_granted=True)


def start_server() -> None:
    """Starts the gRPC server for Server A."""
    # Set up a gRPC server with 10 worker threads
    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Attach our HeistGame implementation to the server
    heist_pb2_grpc.add_HeistGameServicer_to_server(HeistGameServicer(), grpc_server)

    # Tell the server to listen on port 50051
    grpc_server.add_insecure_port('[::]:50051')
    grpc_server.start()
    logger.info("[SERVER A] Physical World Server is running on port 50051...")

    # Keep the server running
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        grpc_server.stop(0)
        logger.info("[SERVER A] Physical World Server has stopped.")


if __name__ == '__main__':
    start_server()
