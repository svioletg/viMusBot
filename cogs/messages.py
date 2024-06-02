"""Stores common bot responses for convenience, and in the future, for translation."""

# Standard imports
from dataclasses import dataclass

# External imports
from discord import Embed

# Local imports
from cogs.common import EmojiStr, embedq

@dataclass
class CommonMsg:
    """Common bot responses kept here for convenience."""
    @staticmethod
    def queue_is_empty() -> Embed:
        return embedq(f'{EmojiStr.cancel} Queue is empty.')

    @staticmethod
    def queue_out_of_range(queue_length: int) -> Embed:
        return embedq(f'{EmojiStr.cancel} Out of range. The current queue is {queue_length} items long.')
