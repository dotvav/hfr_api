"""An HFR message"""

from datetime import datetime
from typing import TYPE_CHECKING

from bs4 import NavigableString

from . import bb

if TYPE_CHECKING:
    from .topic import Topic


class Message:
    def __init__(
        self, topic, id: int, posted_at: datetime, author: str, text: str
    ) -> None:
        self.topic = topic
        self.id = id
        self.posted_at = posted_at
        self.author = author
        self.text = text

    @classmethod
    def from_html(cls, topic: "Topic", html: NavigableString):
        case1 = html.find("td", class_="messCase1")

        author = case1.find("b", class_="s2").string.replace("\u200b", "")
        if author == "Publicité":
            return None

        id = case1.find("a", rel="nofollow").attrs["href"][2:]

        case2 = html.find("td", class_="messCase2")
        posted_at_str = (
            case2.find("div", class_="toolbar").find("div", class_="left").string
        )
        posted_at = Message.parse_timestamp(posted_at_str)

        text_tag = case2.find("div", id=f"para{id}")
        text = bb.html_to_bb(text_tag.decode_contents())

        return cls(topic, id, posted_at, author, text)

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> datetime:
        d = timestamp_str[9:19]
        t = timestamp_str[22:30]
        return datetime.strptime(f"{d} {t}", "%d-%m-%Y %H:%M:%S")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "author": self.author,
            "posted_at": str(self.posted_at),
            "text": self.text,
        }

    @classmethod
    def from_dict(cls, topic, data: dict):
        return cls(
            topic,
            data["id"],
            datetime.fromtimestamp(int(data["posted_at"])),
            data["author"],
            data["text"],
        )
