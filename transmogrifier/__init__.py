import logging
import os

logging.basicConfig(
    format=(
        "%(asctime)s %(levelname)s %(name)s.%(funcName)s() line "
        "%(lineno)d: %(message)s"
    ),
    level=logging.getLevelName(os.getenv("LOGGING_LEVEL", "DEBUG").upper()),
)
