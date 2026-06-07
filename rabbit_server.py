"""Real RabbitMQ API for broadcasting alarms in the RPG game context."""
import pika
import json
import threading
from logger_config import get_logger

logger = get_logger(__name__)

RABBIT_HOST = "rabbitmq"
EXCHANGE_NAME = "heist_events"

def publish_event(routing_key: str, payload: dict) -> None:
    """Sends an asynchronous event to the RabbitMQ exchange."""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBIT_HOST))
        channel = connection.channel()

        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')

        message_body = json.dumps(payload)

        # Fire and forget!
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=routing_key,
            body=message_body
        )
        logger.info(f"[PUBLISHED] {routing_key}: {message_body}")
        connection.close()
    except Exception as e:
        logger.error(f"Failed to publish message: {e}")

def _listen_for_events() -> None:
    """Infinite loop that listens for messages. Runs in a background thread."""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(RABBIT_HOST))
        channel = connection.channel()

        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic')

        result = channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue

        channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name, routing_key='game.alarm')

        def callback(ch, method, properties, body):
            data = json.loads(body)
            logger.warning(f"\n{'!'*50}\n[URGENT BROADCAST] {data['message']} (Location: {data['location']})\n{'!'*50}\n")

        channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
        
        logger.info("[LISTENER] Background thread is actively listening for alarms...")
        channel.start_consuming()
        
    except Exception as e:
        logger.error(f"Listener crashed: {e}")

def start_background_listener() -> None:
    """Starts the listener in a background daemon thread."""
    listener_thread = threading.Thread(target=_listen_for_events, daemon=True)
    listener_thread.start()
