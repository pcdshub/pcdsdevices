import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

from .cam import *
from .plugins import *
