import logging
import time
from concurrent import futures
import grpc
import heist_pb2
import heist_pb2_grpc


logger = logging.getLogger(__name__)


class HeistGameServicer(heist_pb2_grpc.HeistGameServicer):
    """gRPC server implementation for Server A, handling physical world interactions."""

    def unlockDoor(self, request: heist_pb2.DoorRequest, context: grpc.ServicerContext) -> heist_pb2.ActionResponse:
        """Handles door unlock requests from hackers."""
        logger.info(f"[SERVER A] Received hack attempt from {request.hacker_id} for {request.door_id}...")
        # Here is where your Game Logic goes!
        # For now, we just pretend the door unlocks successfully.
        if request.door_id == "door_01":
            logger.info(f"[SERVER A] Access granted to {request.door_id}.")
            return heist_pb2.ActionResponse(success=True, message="Door opened.")
        else:
            logger.info(f"[SERVER A] Access denied to {request.door_id}.")
            return heist_pb2.ActionResponse(success=False, message="Invalid door.")

    def requestVote(self, request: heist_pb2.VoteRequest, context: grpc.ServicerContext) -> heist_pb2.VoteResponse:
        """Handles Maekawa algorithm vote requests for mutual exclusion."""
        # Placeholder for your Maekawa algorithm
        logger.info(f"[SERVER A] Received vote request from {request.hacker_id}.")
        return heist_pb2.VoteResponse(vote_granted=True)


def server() -> None:
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
    server()
