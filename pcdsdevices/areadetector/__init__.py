import logging

from .cam import *  # noqa: F403 F401
from .plugins import *  # noqa: F403 F401

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
