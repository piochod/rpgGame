"""RabbitMQ Publisher for Server A to broadcast game events to Pygame clients."""

import json

import pika
from logger_config import get_logger

logger = get_logger(__name__)

RABBIT_HOST = "rabbitmq"


def publish_event(exchange_name: str, payload: dict) -> None:
    """Sends an asynchronous JSON event to the RabbitMQ fanout exchange."""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBIT_HOST))
        channel = connection.channel()

        channel.exchange_declare(exchange=exchange_name, exchange_type="fanout")

        message_body = json.dumps(payload)

        channel.basic_publish(exchange=exchange_name, routing_key="", body=message_body)
        logger.info(f"[PUBLISHED] {exchange_name}: {message_body}")

        connection.close()
    except Exception as e:
        logger.error(f"Failed to publish message: {e}")
