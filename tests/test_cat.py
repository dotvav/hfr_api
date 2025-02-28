from hfr import Category

from unittest.mock import patch

import datetime


def cat_response(cat: int = 13, page: int = 1):
    with open(f"./tests/samples/cat-{cat}-page-{page}.html") as f:
        return f.read()


class MockResponse:
    def __init__(self, status, text):
        self.status = status
        self.text = text


def test_load_page():
    with patch(
        "requests.get",
        return_value=MockResponse(status=200, text=cat_response(cat=13, page=1)),
    ):
        cat13 = Category(13)
        res = cat13.load_page(1)

    assert len(cat13.topics) == 53

    assert cat13.topics[0].post == 73768
    assert cat13.topics[0].cat == 13
    assert cat13.topics[0].subcat == 432
    assert cat13.topics[0].max_page == 1
    assert cat13.topics[0].max_date == "2025-02-25"
    assert cat13.topics[0].sticky

    assert cat13.topics[-1].post == 98351
    assert cat13.topics[-1].cat == 13
    assert cat13.topics[-1].subcat == 423
    assert cat13.topics[-1].max_page == 206
    assert cat13.topics[-1].max_date == "2025-02-27"
    assert not cat13.topics[-1].sticky

    assert res["ts_min"] == datetime.datetime(2025, 2, 27, 12, 25)
    assert res["ts_max"] == datetime.datetime(2025, 2, 27, 12, 45)