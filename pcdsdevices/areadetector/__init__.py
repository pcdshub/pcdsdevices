import logging

from .cam import *
from .plugins import *

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
