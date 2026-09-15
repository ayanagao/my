"""Track what is in your boxes and how much room is left."""

from .model import Box, BoxError
from .store import BoxStore

__all__ = ["Box", "BoxError", "BoxStore"]
__version__ = "0.1.0"
