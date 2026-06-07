"""Server B: The Hacker's Server that communicates with the Physical World Server."""
import time
import grpc
import grcp_server.heist_pb2 as heist_pb2
import grcp_server.heist_pb2_grpc as heist_pb2_grpc
from logger_config import get_logger
from rabbit_server import start_background_listener

logger = get_logger(__name__)


def run_integration_test() -> None:
    logger.info("[SERVER B] Connecting to Physical World Server...")

    with grpc.insecure_channel('server_a:50051') as channel:
        stub = heist_pb2_grpc.HeistGameStub(channel)

        # --- TEST 1: Disable a camera (Should ALWAYS work) ---
        logger.info("="*10 + "TEST 1: Disabling Camera" + "="*10)
        cam_req = heist_pb2.TargetRequest(target_id="cam_lobby_01", hacker_id="neo_99")
        response = stub.disableCamera(cam_req)
        logger.info(f"Result: {response.success} | {response.message}")
        time.sleep(2)

        # --- TEST 2: Hack Door WITHOUT USB (Should FAIL) ---
        logger.info("="*10 + "TEST 2: Hacking door_01 WITHOUT USB" + "="*10)
        door_req = heist_pb2.TargetRequest(target_id="door_01", hacker_id="neo_99")
        response = stub.unlockDoor(door_req)
        logger.info(f"Result: {response.success} | {response.message}")
        time.sleep(2)

        # --- TEST 3: Infiltrator plugs in USB in Lobby ---
        logger.info("="*10 + "TEST 3: Infiltrator plugs USB into Lobby" + "="*10)
        net_req = heist_pb2.AccessRequest(access_point_id="lobby", hacker_id="ghost_1") 
        response = stub.grantNetworkAccess(net_req)
        logger.info(f"Result: {response.success} | {response.message}")
        time.sleep(2)

        # --- TEST 4: Hack Door WITH USB (Should SUCCEED) ---
        logger.info("="*10 + "TEST 4: Hacking door_01 WITH USB" + "="*10)
        response = stub.unlockDoor(door_req)
        logger.info(f"Result: {response.success} | {response.message}")
        time.sleep(2)

        # --- TEST 5: Hack Vault Door (Should FAIL) ---
        logger.info("="*10 + "TEST 5: Hacking Vault Door (Wrong Zone)" + "="*10)
        vault_req = heist_pb2.TargetRequest(target_id="door_vault", hacker_id="neo_99")
        response = stub.unlockDoor(vault_req)
        logger.info(f"Result: {response.success} | {response.message}")


if __name__ == '__main__':
    start_background_listener()  # Start RabbitMQ listener in the background

    logger.info("Waiting for RabbitMQ listener to initialize...")
    time.sleep(2)  # Give some time for the listener to initialize

    logger.info("Starting integration tests...")
    run_integration_test()
