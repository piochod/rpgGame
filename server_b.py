import logging
import grpc

import heist_pb2
import heist_pb2_grpc

logger = logging.getLogger(__name__)


def attempt_hack(door_id: str, hacker_id: str) -> None:
    """Attempts to hack a door by communicating with the Physical World Server."""
    logger.info(f"[SERVER B] Connecting to Physical World Server...")
    with grpc.insecure_channel('localhost:50051') as channel:
        # Create a "stub" (the client that knows how to call the server)
        stub = heist_pb2_grpc.HeistGameStub(channel)

        # Create the data payload matching the .proto file
        request = heist_pb2.DoorRequest(door_id=door_id, hacker_id=hacker_id)

        # Make the synchronous call and wait for the response
        logger.info(f"[SERVER B] Executing hack on {door_id}...")
        response = stub.UnlockDoor(request)

        # Handle the response
        if response.success:
            logger.info(f"[SERVER B] SUCCESS: {response.message}")
        else:
            logger.info(f"[SERVER B] FAILED: {response.message}")


if __name__ == '__main__':
    # Simulate the Hacker finishing a mini-game and calling the function
    attempt_hack(door_id="door_01", hacker_id="neo_99")
    logger.info("-" * 30)
    attempt_hack(door_id="door_fake", hacker_id="neo_99")
