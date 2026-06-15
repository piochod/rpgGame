import json
import queue
import threading
import time

import pika
from logger_config import get_logger

logger = get_logger(__name__)


class GameEventSubscriber:
    """Listens for game events from RabbitMQ in a background thread and provides them to Pygame."""

    def __init__(self, host: str = "localhost", port: int = 5672, exchange_name: str = "game_events") -> None:
        """Initializes the subscriber and starts the background listener thread.

        Args:
            host (str): The RabbitMQ host to connect to.
            port (int): The RabbitMQ AMQP port.
            exchange_name (str): The name of the exchange to listen to.
        """
        self.host: str = host
        self.port: int = port
        self.exchange: str = exchange_name

        self.message_queue: queue.Queue = queue.Queue()

        # Start the background thread instantly
        self.thread: threading.Thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()

    def _listen(self) -> None:
        """Runs invisibly in the background, waiting for server broadcasts. Retries on failure."""
        while True:
            try:
                params = pika.ConnectionParameters(host=self.host, port=self.port)
                connection = pika.BlockingConnection(params)
                channel = connection.channel()

                channel.exchange_declare(exchange=self.exchange, exchange_type="fanout")

                # Create a temporary queue just for this specific player's screen
                result = channel.queue_declare(queue="", exclusive=True)
                queue_name = result.method.queue
                channel.queue_bind(exchange=self.exchange, queue=queue_name)

                def _callback(
                    ch: pika.channel.Channel,
                    method: pika.spec.Basic.Deliver,
                    properties: pika.spec.BasicProperties,
                    body: bytes,
                ) -> None:
                    message = json.loads(body)
                    logger.info(f"Incoming Broadcast: {message}")
                    self.message_queue.put(message)

                logger.info("Connected to RabbitMQ! Listening for Lobby Events...")
                channel.basic_consume(queue=queue_name, on_message_callback=_callback, auto_ack=True)
                channel.start_consuming()

            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ: {e}")
                logger.info("Retrying RabbitMQ connection in 3 seconds...")
                time.sleep(3)

    def get_messages(self) -> list[dict]:
        """Pygame will call this every frame to check its inbox."""
        messages = []
        while not self.message_queue.empty():
            messages.append(self.message_queue.get())
        return messages
