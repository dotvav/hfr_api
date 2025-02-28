"""An HFR Topic"""

import logging
import time
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup
from sortedcontainers import SortedDict

from .message import Message

logger = logging.getLogger()


def date_to_str(some_date: str | date | datetime) -> str:
    if isinstance(some_date, datetime):
        return str(some_date.date())
    elif isinstance(some_date, date):
        return str(some_date)
    elif isinstance(some_date, str):
        return some_date
    return None


class Topic:
    def __init__(
        self,
        cat: int,
        subcat: int,
        post: int,
        title: str = "",
        max_page: int = 0,
        max_date: str = "1970-01-01",
        sticky: bool = False,
    ) -> None:
        self.cat = cat
        self.subcat = subcat
        self.post = post
        self.title = title
        self.max_page = max_page
        self.max_date = max_date
        self.sticky = sticky
        self.messages = dict()

    @property
    def id(self) -> str:
        return f"{self.cat}#{self.subcat}#{self.post}"

    def parse_page_html(self, html: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        self.title = soup.find("h3").text

        # Find highest page number
        pages_block = soup.find("tr", class_="fondForum2PagesHaut")
        page_links = pages_block.find_all("a", class_="cHeader")

        if self.max_page == 0:
            max_page = 1
            for page in page_links:
                href = page.attrs["href"]
                for param in href.split("&"):
                    kv = param.split("=")
                    if kv[0] == "page":
                        if int(kv[1]) > max_page:
                            max_page = int(kv[1])
                        break
            self.max_page = max_page

        ts_min = 0
        ts_max = 0

        # Find all messages in the page
        messages_soup = soup.find_all("table", class_="messagetable")
        for message_block in messages_soup:
            message = Message.from_html(self, message_block)
            if message:
                self.add_message(message)
                if ts_min == 0 or ts_min > message.posted_at:
                    ts_min = message.posted_at
                if ts_max == 0 or ts_max < message.posted_at:
                    ts_max = message.posted_at

        return {"ts_min": ts_min, "ts_max": ts_max}

    def add_message(self, message) -> None:
        msg_date = date_to_str(message.posted_at)

        if msg_date in self.messages:
            messages_for_date = self.messages[msg_date]
        else:
            if msg_date > self.max_date:
                self.max_date = msg_date
            logger.debug(f"Got a message at date {msg_date}")
            messages_for_date = SortedDict()
            self.messages[msg_date] = messages_for_date
        messages_for_date[message.id] = message

    def load_page(self, page: int) -> dict:
        time.sleep(1)

        url = f"https://forum.hardware.fr/forum2.php?config=hfr.inc&cat={self.cat}&subcat={self.subcat}&post={self.post}&print=1&page={page}"

        r = requests.get(
            url,
            headers={
                "Accept": "text/html",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "User-Agent": "HFRTopicSummarizer",
            },
        )
        html = r.text

        return self.parse_page_html(html)

    def has_date(self, msg_date: str | date | datetime) -> bool:
        return date_to_str(msg_date) in self.messages.keys()

    def messages_on_date(self, msg_date: str):
        date_str = str(msg_date)
        if date_str in self.messages:
            return self.messages[date_str].values()
        else:
            return ()

    def to_dict(self) -> dict:
        return {
            "topic_id": f"{self.cat}#{self.subcat}#{self.post}",
            "title": self.title,
            "max_page": self.max_page,
            "max_date": self.max_date,
        }

    @classmethod
    def from_dict(cls, data: dict):
        if "topic_id" in data:
            (cat, subcat, post) = str.split(data["topic_id"], "#")
            return cls(
                cat, subcat, post, data["title"], data["max_page"], data["max_date"]
            )
        else:
            return cls(
                data["cat"],
                data["subcat"],
                data["post"],
                data["title"],
                data["max_page"],
                data["max_date"],
            )
