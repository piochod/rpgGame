"""Real RabbitMQ API for broadcasting alarms in the RPG game context."""
import pika
import json


def broadcast_alarm_real(level: int, room: str) -> None:
    """Real function: Shouts to all servers that an alarm tripped."""
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare the exchange
    channel.exchange_declare(exchange='heist_events', exchange_type='topic')

    # Package the data
    payload = json.dumps({"level": level, "room": room})

    # Fire the message into the void
    channel.basic_publish(
        exchange='heist_events',
        routing_key='event.alarm',
        body=payload
    )
    connection.close()
