"""HFR Client handling authentication, session persistence, posting, PMs, and smiley search."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

from curl_cffi import requests as cffi_requests
from lxml import html as lxml_html

from . import bb
from .message import Message
from .topic import Topic

logger = logging.getLogger(__name__)


@dataclass
class HFRPrivateMessage:
    id: str
    sender: str
    subject: str
    received_at: str
    is_unread: bool


@dataclass
class SmileyResult:
    code: str
    url: str
    name: str
    keywords: list[str] = field(default_factory=list)


class HFRClient:
    """Session-aware client for forum.hardware.fr."""

    def __init__(
        self,
        username: str = "",
        password: str = "",
        cookies_path: Optional[Path] = None,
        base_url: str = "https://forum.hardware.fr",
        user_agent: Optional[str] = None,
    ) -> None:
        self.username = username
        self.password = password
        self.cookies_path = Path(cookies_path) if cookies_path else None
        self.base_url = base_url.rstrip("/")
        self.user_agent = (
            user_agent
            or "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        )
        self.session = cffi_requests.Session(impersonate="chrome124")
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            }
        )
        if self.cookies_path and self.cookies_path.exists():
            self.load_cookies()

    def save_cookies(self) -> None:
        """Save session cookies to disk."""
        if not self.cookies_path:
            return
        self.cookies_path.parent.mkdir(parents=True, exist_ok=True)
        cookie_dict = dict(self.session.cookies)
        with open(self.cookies_path, "w", encoding="utf-8") as f:
            json.dump(cookie_dict, f, indent=2)
        logger.debug("HFR session cookies saved to %s", self.cookies_path)

    def load_cookies(self) -> None:
        """Load session cookies from disk."""
        if not self.cookies_path or not self.cookies_path.exists():
            return
        try:
            with open(self.cookies_path, "r", encoding="utf-8") as f:
                cookie_dict = json.load(f)
                for k, v in cookie_dict.items():
                    self.session.cookies.set(k, v, domain=".hardware.fr")
            logger.debug("HFR session cookies loaded from %s", self.cookies_path)
        except Exception as e:
            logger.warning("Failed to load cookies from %s: %s", self.cookies_path, e)

    def is_logged_in(self) -> bool:
        """Check if current session is authenticated by verifying access to private messages."""
        try:
            resp = self.session.get(f"{self.base_url}/forum1.php?config=hfr.inc&cat=prive")
            if resp.status_code != 200:
                return False
            # Check for title or indicators of successful MP area access vs guest access denied
            has_mp_title = "Messages priv" in resp.text
            has_denied = "ne faites pas partie des membres" in resp.text or "non autoris" in resp.text.lower()
            return has_mp_title and not has_denied
        except Exception as e:
            logger.error("Error verifying login status: %s", e)
            return False

    def login(self, force: bool = False) -> bool:
        """Authenticate to HFR with credentials handling MesDiscussions two-step meta-refresh."""
        if not force and self.is_logged_in():
            logger.info("Existing HFR session is valid.")
            return True

        if not self.username or not self.password:
            logger.warning("HFR credentials not provided; proceeding in read-only mode.")
            return False

        validation_url = f"{self.base_url}/login_validation.php?config=hfr.inc"
        data = {
            "hash_check": "",
            "pseudo": self.username,
            "password": self.password,
            "cat": "",
            "page": "1",
            "config": "hfr.inc",
            "p": "1",
            "sondage": "0",
            "owntopic": "0",
            "post": "",
            "referer": f"{self.base_url}/",
            "Valider": "Valider",
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/login.php?config=hardwarefr.inc",
        }

        # Step 1: Submit credentials to validation endpoint
        resp1 = self.session.post(validation_url, data=data, headers=headers)
        if "login_redirection" not in resp1.text and "Vérification" not in resp1.text:
            logger.error("Failed to authenticate to HFR as %s (validation rejected)", self.username)
            return False

        # Extract redirect URL from <meta http-equiv="Refresh" content="1; url=...">
        import re

        match = re.search(r'url=([^\s"\'>]+)', resp1.text, re.IGNORECASE)
        redirect_path = (
            match.group(1)
            if match
            else "login_redirection.php?config=hfr.inc&referer_page=https%3A%2F%2Fforum.hardware.fr%2F"
        )
        redirect_url = (
            redirect_path
            if redirect_path.startswith("http")
            else f"{self.base_url}/{redirect_path.lstrip('/')}"
        )

        # Step 2: Follow meta-refresh to commit session cookies (md_user, md_passs, md_id)
        self.session.get(redirect_url, headers={"Referer": validation_url})

        if self.is_logged_in():
            logger.info("Successfully authenticated to HFR as %s", self.username)
            self.save_cookies()
            return True

        logger.error("Failed to authenticate to HFR as %s", self.username)
        return False

    def ensure_authenticated(self) -> None:
        """Ensure session is active, auto-relogging if necessary."""
        if not self.is_logged_in():
            logger.info("Session expired or unauthenticated. Attempting login...")
            if not self.login(force=True):
                raise RuntimeError("HFR Authentication failed.")

    def get_topic_page(self, cat: int, subcat: int, post: int, page: int = 1) -> Topic:
        """Fetch and parse a specific topic page."""
        topic = Topic(cat=cat, subcat=subcat, post=post)
        topic.load_page(page=page, session=self.session)
        return topic

    def get_latest_topic_messages(
        self, cat: int, subcat: int, post: int, last_seen_msg_id: Optional[int] = None
    ) -> list[Message]:
        """Fetch latest messages from a topic, optionally filtering by last_seen_msg_id."""
        topic = self.get_topic_page(cat=cat, subcat=subcat, post=post, page=1)
        target_page = topic.max_page if topic.max_page > 0 else 1

        if target_page != 1:
            topic = self.get_topic_page(cat=cat, subcat=subcat, post=post, page=target_page)

        messages: list[Message] = []
        for date_key in sorted(topic.messages.keys()):
            for msg in topic.messages[date_key].values():
                try:
                    int_id = int(msg.id)
                except ValueError:
                    int_id = 0
                if last_seen_msg_id is None or int_id > last_seen_msg_id:
                    messages.append(msg)
        return messages

    def get_post_form_tokens(self, cat: int | str, subcat: int | str, post: int) -> dict[str, str]:
        """Fetch hash_check, numrep, and form metadata required to submit a reply."""
        self.ensure_authenticated()
        cat_str = str(cat)
        subcat_str = str(subcat)
        resp = self.session.get(
            f"{self.base_url}/forum2.php?config=hfr.inc&cat={cat_str}&subcat={subcat_str}&post={post}&page=1"
        )
        tree = lxml_html.fromstring(resp.text)
        form = tree.xpath('//form[contains(@action, "bddpost.php")]')
        tokens: dict[str, str] = {}
        if form:
            for inp in form[0].xpath('.//input'):
                name = inp.get("name")
                if name:
                    tokens[name] = inp.get("value") or ""
        else:
            hash_inputs = tree.xpath('//input[@name="hash_check"]')
            tokens["hash_check"] = hash_inputs[0].get("value") if hash_inputs else ""
        return tokens

    def post_reply(
        self,
        cat: int,
        subcat: int,
        post: int,
        content: str,
        dry_run: bool = False,
    ) -> bool:
        """Submit a reply to a thread."""
        if dry_run:
            logger.info("[DRY_RUN] Would post to topic %s#%s#%s:\n%s", cat, subcat, post, content)
            return True

        self.ensure_authenticated()
        tokens = self.get_post_form_tokens(cat=cat, subcat=subcat, post=post)

        formatted_content = bb.emoji_to_cdn_bb(content)
        post_url = f"{self.base_url}/bddpost.php?config=hfr.inc"
        payload = {
            "action_form": "1",
            "cat": str(cat),
            "subcat": str(subcat),
            "post": str(post),
            "content_form": formatted_content,
            "hash_check": tokens.get("hash_check", ""),
            "numrep": tokens.get("numrep", ""),
            "verifrequet": tokens.get("verifrequet", "1100"),
            "signature": "1",
            "verifform": "1",
        }

        resp = self.session.post(
            post_url,
            data=payload,
            headers={
                "Referer": f"{self.base_url}/forum2.php?config=hfr.inc&cat={cat}&subcat={subcat}&post={post}"
            },
            allow_redirects=True,
        )

        if resp.status_code in (200, 302):
            tree = lxml_html.fromstring(resp.text)
            body_text = tree.xpath("//body")[0].text_content() if tree.xpath("//body") else resp.text
            if "Afin de prevenir les tentatives de flood" in body_text:
                logger.error("Failed to post reply: HFR flood protection triggered (%s)", body_text.strip())
                return False
            if "Une erreur est survenue" in body_text or "Erreur" in body_text and "Retour" in body_text:
                logger.error("Failed to post reply: HFR error page returned (%s)", body_text.strip()[:200])
                return False

            logger.info("Successfully posted reply to topic %s#%s#%s", cat, subcat, post)
            return True

        logger.error("Failed to post reply. Status: %s", resp.status_code)
        return False

    def list_mps(self, page: int = 1, unread_only: bool = False) -> list[HFRPrivateMessage]:
        """Fetch and return private messages from inbox."""
        self.ensure_authenticated()
        url = f"{self.base_url}/forum1.php?config=hfr.inc&cat=prive&page={page}"
        resp = self.session.get(url)
        if resp.status_code != 200:
            logger.error("Failed to fetch private messages: HTTP %s", resp.status_code)
            return []

        tree = lxml_html.fromstring(resp.text)
        # MesDiscussions uses <tr class="sujet ligne_booleen ..."> for each thread/MP row
        mp_rows = tree.xpath(
            '//tr[contains(@class, "sujet") and (contains(@class, "ligne_booleen") or contains(@class, "cBackCouleurTab"))]'
        )
        results: list[HFRPrivateMessage] = []

        for row in mp_rows:
            # 1. Subject & post ID
            links = row.xpath(
                './/td[contains(@class, "sujetCase3")]//a | .//a[contains(@class, "cTopic") or contains(@class, "cCatTopic")]'
            )
            if not links:
                continue
            subject = links[0].text_content().strip()
            href = links[0].get("href", "")

            qs = parse_qs(urlparse(href).query)
            mp_id = qs.get("post", [""])[0]

            # 2. Interlocuteur / Sender (Case 6)
            author_cells = row.xpath('.//td[contains(@class, "sujetCase6")]')
            sender = author_cells[0].text_content().strip() if author_cells else "Unknown"

            # 3. Date of last message (Case 9)
            date_cells = row.xpath('.//td[contains(@class, "sujetCase9")]')
            date_str = date_cells[0].text_content().strip() if date_cells else str(datetime.now())

            # 4. Unread detection via Case 1 icon (closedbp.gif indicates unread / new message)
            case1_imgs = row.xpath('.//td[contains(@class, "sujetCase1")]//img')
            img_src = case1_imgs[0].get("src", "") if case1_imgs else ""
            img_alt = case1_imgs[0].get("alt", "") if case1_imgs else ""
            is_unread = (
                "closedbp" in img_src
                or "new" in img_src
                or img_alt.lower() == "on"
                or "NonLu" in (row.get("class") or "")
            )

            if unread_only and not is_unread:
                continue

            results.append(
                HFRPrivateMessage(
                    id=mp_id,
                    sender=sender,
                    subject=subject,
                    received_at=date_str,
                    is_unread=is_unread,
                )
            )
        return results

    def get_mp_page(self, mp_id: int, page: int = 1) -> Topic:
        """Fetch and parse a private message thread."""
        self.ensure_authenticated()
        url = f"{self.base_url}/forum2.php?config=hfr.inc&cat=prive&post={mp_id}&print=1&page={page}"
        resp = self.session.get(url)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to fetch MP thread {mp_id} page {page}: HTTP {resp.status_code}")

        topic = Topic(cat=0, subcat=0, post=mp_id)
        topic.parse_page_html(resp.text)
        return topic

    def post_mp_reply(
        self,
        mp_id: int,
        recipient: str,
        content: str,
        dry_run: bool = False,
    ) -> bool:
        """Submit a reply to a private message thread."""
        if dry_run:
            logger.info("[DRY_RUN] Would reply to MP %s (to: %s):\n%s", mp_id, recipient, content)
            return True

        self.ensure_authenticated()
        tokens = self.get_post_form_tokens(cat="prive", subcat=0, post=mp_id)

        formatted_content = bb.emoji_to_cdn_bb(content)
        post_url = f"{self.base_url}/bddpost.php?config=hfr.inc"

        # Merge all tokens parsed directly from the live page form
        payload = dict(tokens)
        payload["content_form"] = formatted_content
        payload["action_form"] = "2"
        payload["dest"] = recipient

        resp = self.session.post(
            post_url,
            data=payload,
            headers={
                "Referer": f"{self.base_url}/forum2.php?config=hfr.inc&cat=prive&post={mp_id}"
            },
            allow_redirects=True,
        )

        if resp.status_code in (200, 302):
            tree = lxml_html.fromstring(resp.text)
            body_text = tree.xpath("//body")[0].text_content() if tree.xpath("//body") else resp.text
            if "Afin de prevenir les tentatives de flood" in body_text:
                logger.error("Failed to reply to MP %s: HFR flood protection triggered (%s)", mp_id, body_text.strip())
                return False
            if "Une erreur est survenue" in body_text or "Erreur" in body_text and "Retour" in body_text:
                logger.error("Failed to reply to MP %s: HFR error page returned (%s)", mp_id, body_text.strip()[:200])
                return False

            logger.info("Successfully posted reply to MP %s", mp_id)
            return True

        logger.error("Failed to reply to MP %s. Status: %s", mp_id, resp.status_code)
        return False

    def search_wiki_smilies(
        self, query: str, max_results: int = 15
    ) -> list[SmileyResult]:
        """Search HFR wiki custom smilies matching a keyword or smiley code/ID (e.g. 'koala', '[:aloy:2]', 'aloy:2')."""
        clean_query = query.strip()
        if clean_query.startswith("[:") and clean_query.endswith("]"):
            clean_query = clean_query[2:-1]
        if ":" in clean_query:
            clean_query = clean_query.split(":")[0]

        url = f"{self.base_url}/message-smi-mp-aj.php"
        params = {"config": "hfr.inc", "findsmilies": clean_query}
        resp = self.session.get(url, params=params)
        if resp.status_code != 200:
            return []

        tree = lxml_html.fromstring(resp.text)
        img_nodes = tree.xpath("//img")
        results: list[SmileyResult] = []

        for img in img_nodes:
            src = img.get("src", "")
            alt = img.get("alt", "")
            title = img.get("title", "") or alt
            if alt.startswith("[:") and alt.endswith("]"):
                if query.strip().startswith("[:") and query.strip().endswith("]"):
                    if alt == query.strip():
                        results.insert(0, SmileyResult(code=alt, url=src, name=title))
                        continue
                results.append(SmileyResult(code=alt, url=src, name=title))

        return results[:max_results]

    def get_smiley_keywords(self, smiley_code: str) -> list[str]:
        """Fetch all keywords/tags associated with a specific smiley code (e.g. '[:itm]', 'itm', '[:aloy:2]')."""
        code = smiley_code.strip()
        if not code.startswith("[:"):
            code = f"[:{code}"
        if not code.endswith("]"):
            code = f"{code}]"

        # Query wikismilies.php with the base code
        base_keyword = code[2:-1].split(":")[0]
        url = f"{self.base_url}/wikismilies.php?config=hfr.inc&threecol=0"
        payload = {"findcode": "", "findkeyword": base_keyword, "Submit": "Rechercher"}
        resp = self.session.post(url, data=payload)
        if resp.status_code != 200:
            return []

        tree = lxml_html.fromstring(resp.text)
        inputs = tree.xpath('//input[contains(@name, "keywords")]')
        for inp in inputs:
            idx = inp.get("name", "").replace("keywords", "")
            smiley_input = tree.xpath(f'//input[@name="smiley{idx}"]')
            found_code = smiley_input[0].get("value", "") if smiley_input else ""
            if found_code.lower() == code.lower():
                raw_kw = inp.get("value", "").strip()
                return [k for k in raw_kw.split(" ") if k]

        return []

    def search_wiki_smilies_detailed(
        self, query: str, max_results: int = 15
    ) -> list[SmileyResult]:
        """Search HFR wiki smilies and attach their associated keywords."""
        clean_query = query.strip()
        if clean_query.startswith("[:") and clean_query.endswith("]"):
            clean_query = clean_query[2:-1]
        if ":" in clean_query:
            clean_query = clean_query.split(":")[0]

        url = f"{self.base_url}/wikismilies.php?config=hfr.inc&threecol=0"
        payload = {"findcode": "", "findkeyword": clean_query, "Submit": "Rechercher"}
        resp = self.session.post(url, data=payload)
        if resp.status_code != 200:
            return self.search_wiki_smilies(query=query, max_results=max_results)

        tree = lxml_html.fromstring(resp.text)
        results: list[SmileyResult] = []
        inputs = tree.xpath('//input[contains(@name, "keywords")]')

        for inp in inputs:
            idx = inp.get("name", "").replace("keywords", "")
            smiley_input = tree.xpath(f'//input[@name="smiley{idx}"]')
            code = smiley_input[0].get("value", "") if smiley_input else ""
            if not code:
                continue

            raw_kw = inp.get("value", "").strip()
            keywords = [k for k in raw_kw.split(" ") if k]
            
            # Find image node corresponding to this smiley
            img_nodes = tree.xpath(f'//img[@alt="{code}"]')
            url = img_nodes[0].get("src", "") if img_nodes else ""

            results.append(
                SmileyResult(
                    code=code,
                    url=url,
                    name=code,
                    keywords=keywords,
                )
            )

        # Fallback to fast search if no wiki results found
        if not results:
            return self.search_wiki_smilies(query=query, max_results=max_results)

        return results[:max_results]
