"""BB code handling"""

from bs4 import BeautifulSoup, NavigableString


def html_to_bb(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # TODO save links, smileys, images, quotes, code
    # I think I need to find all the "img", "a", "b", "u", "i" elements and replace them inline with their equivalent bb code tags.
    # Can do the same bullet "lists", "pre", "code", text coloring etc...
    # In v0, for the need of summarization, stick to "img", "a", and try to get to quotes

    return soup.get_text(strip=False)
