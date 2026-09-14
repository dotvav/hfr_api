"""An HFR Topic"""

import logging
import re
import time
from datetime import date, datetime
from typing import Any, Optional

import requests
from lxml import html as lxml_html
from sortedcontainers import SortedDict

from . import bb
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

    def parse_page_html(
        self,
        html_text: str,
        page: int = 1,
        user_resolver: Optional[bb.UserResolver] = None,
    ) -> dict:
        tree = lxml_html.fromstring(html_text)

        # Get title
        h3 = tree.find(".//h3")
        if h3 is None:
            raise ValueError("Topic not found or access denied")
        self.title = h3.text_content()

        # Find highest page number
        max_page = max(page, self.max_page, 1)
        pages_rows = tree.xpath('//tr[contains(@class, "fondForum2PagesHaut")]')
        if pages_rows:
            for el in pages_rows[0].xpath('.//a | .//b | .//span'):
                text = el.text_content().strip()
                if text.isdigit() and int(text) > max_page:
                    max_page = int(text)

                href = el.get("href", "")
                if href:
                    m_rewritten = re.search(r"sujet_\d+_(\d+)\.htm", href)
                    if m_rewritten and int(m_rewritten.group(1)) > max_page:
                        max_page = int(m_rewritten.group(1))

                    m_query = re.search(r"[?&]page=(\d+)", href)
                    if m_query and int(m_query.group(1)) > max_page:
                        max_page = int(m_query.group(1))

        self.max_page = max_page

        ts_min = 0
        ts_max = 0

        # Find all messages in the page
        message_tables = tree.xpath('//table[contains(@class, "messagetable")]')

        # Pre-scan page to extract local mapping {author: user_id}
        page_users: dict[str, int] = {}
        for block in message_tables:
            author_el = block.xpath('.//td[contains(@class, "messCase1")]//b[contains(@class, "s2")]')
            if not author_el:
                continue
            author_name = author_el[0].text_content().replace("\u200b", "").strip()
            if not author_name or author_name == "Publicité":
                continue
            profil_links = block.xpath('.//a[contains(@href, "profil-")]')
            for pl in profil_links:
                href = pl.get("href", "")
                m = re.search(r"profil-(\d+)\.htm", href)
                if m:
                    try:
                        uid = int(m.group(1))
                        if uid > 0:
                            page_users[author_name] = uid
                            page_users[author_name.lower()] = uid
                            break
                    except ValueError:
                        pass

        def _combined_resolver(pseudo: str) -> Optional[int]:
            if pseudo in page_users:
                return page_users[pseudo]
            if pseudo.lower() in page_users:
                return page_users[pseudo.lower()]
            if user_resolver:
                try:
                    if callable(user_resolver):
                        res = user_resolver(pseudo)
                    elif isinstance(user_resolver, dict):
                        res = user_resolver.get(pseudo) or user_resolver.get(pseudo.lower())
                    else:
                        res = None
                    if res and str(res).isdigit():
                        return int(res)
                except Exception:
                    pass
            return 0

        for idx, message_block in enumerate(message_tables, start=1):
            message = Message.from_lxml(
                self,
                message_block,
                page=page,
                index_on_page=idx,
                user_resolver=_combined_resolver,
            )
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

    def load_page(
        self,
        page: int,
        session: Optional[Any] = None,
        user_resolver: Optional[bb.UserResolver] = None,
    ) -> dict:
        url = f"https://forum.hardware.fr/forum2.php?config=hfr.inc&cat={self.cat}&subcat={self.subcat}&post={self.post}&page={page}"
        headers = {
            "Accept": "text/html",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "User-Agent": "HFRTopicSummarizer",
        }

        if session is not None:
            r = session.get(url)
        else:
            time.sleep(0.5)
            r = requests.get(url, headers=headers)

        if r.status_code != 200:
            raise RuntimeError(
                f"Failed to fetch topic {self.cat}#{self.subcat}#{self.post} page {page}: HTTP {r.status_code}"
            )

        return self.parse_page_html(r.text, page=page, user_resolver=user_resolver)

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
