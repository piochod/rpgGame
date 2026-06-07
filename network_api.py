"""Mock network API for simulating gRPC and RabbitMQ interactions in the RPG game context."""
import time


def request_door_unlock(door_id: str, hacker_id: str) -> bool:
    """Mock function: Asks Server A to unlock a door.

    Args:
        door_id (str): Identifier for the door to unlock.
        hacker_id (str): Identifier for the hacker requesting the unlock.

    Returns:
        bool: True if the request is successful, False otherwise.
    """
    print(f"[NETWORK MOCK] Sending gRPC unlock request for {door_id}, {hacker_id}...")
    time.sleep(0.5)
    return True


def request_data_lock(node_id: str) -> bool:
    """Mock function: Initiates Maekawa algorithm to lock the main server.

    Args:
        node_id (str): Identifier for the node to lock.

    Returns:
        bool: True if the request is successful, False otherwise.
    """
    print(f"[NETWORK MOCK] Broadcasting Maekawa lock request to quorum for {node_id}...")
    return True


def broadcast_alarm(level: int, room: str):
    """Mock function: Shouts to all servers that an alarm tripped."""
    print(f"[NETWORK MOCK] RabbitMQ Broadcast: ALARM LEVEL {level} in {room}!")


def send_heartbeat(server_name: str):
    """Mock function: Sends an 'I am alive' ping.

    Args:
        server_name (str): Name of the server sending the heartbeat.
    """
    print(f"[NETWORK MOCK] RabbitMQ Ping: {server_name} is alive.")
