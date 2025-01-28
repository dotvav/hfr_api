"""HFR"""

from datetime import date, datetime
from bs4 import BeautifulSoup, NavigableString
from sortedcontainers import SortedList
import logging
import requests
import time


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
    
    def __init__(self, cat: int, subcat: int, post: int) -> None:
        self.cat = cat
        self.subcat = subcat
        self.post = post
        self.messages = dict()
        self.max_page = 0
        self.max_date = "1970-01-01"

    def first_messages(self, limit: int = 40) -> list[datetime]:
        return self.messages[0:limit-1]

    def last_messages(self, limit: int = 40) -> list[datetime]:
        return self.messages[-limit:0]

    def last_update_date(self) -> datetime:
        return self.messages[-1].timestamp

    def parse_page_html(self, html: str) -> None:
        soup = BeautifulSoup(html, 'html.parser')
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

        # Find all messages in the page
        messages_soup = soup.find_all("table", class_="messagetable")
        for message_block in messages_soup:
            message = Message.parse_html(self, message_block)
            if message:
                self.add_message(message)
    
    def add_message(self, message) -> None:
        date = date_to_str(datetime.fromtimestamp(message.timestamp)) # Truncated date 
        
        if date in self.messages:
            messages_for_date = self.messages[date]
        else:
            if date > self.max_date:
                self.max_date = date
            logger.debug(f"Got a message at date {date}")
            messages_for_date = SortedList([], key=lambda m: m.timestamp)
            self.messages[date] = messages_for_date
        messages_for_date.add(message)

    def load_page(self, page: int) -> None:
        # Wait a second
        # TODO check when was the last load, and wait a second before loading this one
        time.sleep(1)

        url = f"https://forum.hardware.fr/forum2.php?config=hfr.inc&cat={self.cat}&subcat={self.subcat}&post={self.post}&print=1&page={page}"

        r = requests.get(url, headers={"Accept": "text/html", "Accept-Encoding": "gzip, deflate, br, zstd", "User-Agent": "HFRTopicSummarizer"})
        html = r.text

        self.parse_page_html(html)

    def has_date(self, msg_date: str | date | datetime) -> bool:
        return date_to_str(msg_date) in self.messages.keys()
    
    def messages_on_date(self, msg_date: str):
        return self.messages[date_to_str(msg_date)]



class Message:
    def __init__(self, topic: Topic, id: int, timestamp: datetime, author:str, text: str) -> None:
        self.topic = topic
        self.id = id
        self.timestamp = timestamp
        self.author = author
        self.text = text
    
    @classmethod
    def parse_html(cls, topic: Topic, html: NavigableString):
        case1 = html.find("td", class_="messCase1")

        author = case1.find("b", class_="s2").string
        if author == "Publicité":
            return None
        
        id = case1.find("a", rel="nofollow").attrs["href"][2:]

        case2 = html.find("td", class_="messCase2")
        timestamp_str = case2.find("div", class_="toolbar").find("div", class_="left").string
        timestamp = Message.parse_timestamp(timestamp_str).timestamp()

        text = case2.find("div", id=f"para{id}").string

        return cls(topic, id, timestamp, author, text)
    
    @staticmethod
    def parse_timestamp(timestamp_str: str) -> datetime:
        d = timestamp_str[9:19]
        t = timestamp_str[22:30]
        return datetime.strptime(f"{d} {t}", "%d-%m-%Y %H:%M:%S")

