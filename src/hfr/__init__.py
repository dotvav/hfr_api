"""hfr_api: A Python library to interface with forum.hardware.fr"""

from . import bb
from .message import Message
from .topic import Topic
from .category import Category
from .client import HFRClient, HFRPrivateMessage, SmileyResult, extract_user_id_from_html

__all__ = [
    "bb",
    "Message",
    "Topic",
    "Category",
    "HFRClient",
    "HFRPrivateMessage",
    "SmileyResult",
    "extract_user_id_from_html",
]