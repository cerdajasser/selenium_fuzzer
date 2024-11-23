import logging
from selenium_fuzzer.config import Config

def get_logger(name: str) -> logging.Logger:
    """Configure and return a logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO))

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    fh = logging.FileHandler(Config.LOG_FILE)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger
