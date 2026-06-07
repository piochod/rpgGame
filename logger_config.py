"""Basic logger configuration to use."""
import logging


def get_logger(module_name: str) -> logging.Logger:
    """Sets up the universal logging configuration and returns a logger instance."""
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s][%(levelname)s]%(message)s',
        datefmt='%H:%M:%S'
    )

    logging.getLogger("pika").setLevel(logging.WARNING)
    logging.getLogger("grpc").setLevel(logging.WARNING)

    return logging.getLogger(module_name)
