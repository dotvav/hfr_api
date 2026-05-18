"""An HFR message"""

from datetime import datetime
from typing import TYPE_CHECKING

from lxml import etree

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
    def from_lxml(cls, topic: "Topic", element):
        """Parse a message from an lxml element (table.messagetable)."""
        # Find messCase1 td
        case1_list = element.xpath('.//td[contains(@class, "messCase1")]')
        if not case1_list:
            return None
        case1 = case1_list[0]

        # Get author
        author_el = case1.xpath('.//b[contains(@class, "s2")]')
        if not author_el:
            return None
        author = author_el[0].text_content().replace("\u200b", "")
        if author == "Publicité":
            return None

        # Get message id
        nofollow_links = case1.xpath('.//a[@rel="nofollow"]')
        if not nofollow_links:
            return None
        id = nofollow_links[0].get("href", "")[2:]

        # Find messCase2 td
        case2_list = element.xpath('.//td[contains(@class, "messCase2")]')
        if not case2_list:
            return None
        case2 = case2_list[0]

        # Get timestamp
        toolbar = case2.xpath('.//div[contains(@class, "toolbar")]')
        if not toolbar:
            return None
        left_div = toolbar[0].xpath('.//div[contains(@class, "left")]')
        if not left_div:
            return None
        posted_at_str = left_div[0].text_content()
        posted_at = Message.parse_timestamp(posted_at_str)

        # Get message text - extract inner HTML of the para div
        text_divs = case2.xpath(f'.//div[@id="para{id}"]')
        if not text_divs:
            return None
        # Get inner HTML of the div
        text_html = etree.tostring(text_divs[0], encoding="unicode", method="html")
        # Strip the outer div tags
        inner_start = text_html.find(">") + 1
        inner_end = text_html.rfind("</div>")
        inner_html = text_html[inner_start:inner_end] if inner_end > inner_start else ""

        text = bb.html_to_bb(inner_html)

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
