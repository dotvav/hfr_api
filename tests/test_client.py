"""Unit tests for HFRClient."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from hfr.client import HFRClient, HFRPrivateMessage, SmileyResult


@pytest.fixture
def mock_session():
    with patch("hfr.client.cffi_requests.Session") as mock_cls:
        session = MagicMock()
        mock_cls.return_value = session
        yield session


def test_hfr_client_initialization(tmp_path: Path):
    cookies_path = tmp_path / "cookies.json"
    client = HFRClient(
        username="test_bot",
        password="secret_password",
        cookies_path=cookies_path,
    )
    assert client.username == "test_bot"
    assert client.password == "secret_password"
    assert client.cookies_path == cookies_path


def test_hfr_client_is_logged_in(mock_session):
    client = HFRClient(username="test_bot", password="secret_password")

    mock_resp_unauth = MagicMock(
        status_code=200,
        text="<html><body>Désolé, vous ne faites pas partie des membres ayant accès à cette catégorie</body></html>",
    )
    mock_session.get.return_value = mock_resp_unauth
    assert client.is_logged_in() is False

    mock_resp_auth = MagicMock(
        status_code=200,
        text="<html><head><title>Messages privés - FORUM HardWare.fr</title></head><body><h1>Messages privés</h1></body></html>",
    )
    mock_session.get.return_value = mock_resp_auth
    assert client.is_logged_in() is True


def test_hfr_client_login_success(mock_session, tmp_path: Path):
    cookies_path = tmp_path / "cookies.json"
    client = HFRClient(
        username="test_bot",
        password="secret_password",
        cookies_path=cookies_path,
    )

    mock_session.post.return_value = MagicMock(
        status_code=200,
        text='<html><head><meta http-equiv="Refresh" content="1; url=login_redirection.php?config=hfr.inc" /></head><body>Vérification de votre identification...</body></html>',
    )
    mock_session.get.side_effect = [
        MagicMock(status_code=200, text="<html><body>Non autorise</body></html>"),  # initial is_logged_in check
        MagicMock(status_code=200, text="Login redirection success"),  # follow redirection
        MagicMock(
            status_code=200,
            text="<html><head><title>Messages privés - FORUM HardWare.fr</title></head><body><h1>Messages privés</h1></body></html>",
        ),  # post-login is_logged_in check
    ]

    assert client.login() is True
    assert cookies_path.exists()


def test_hfr_client_list_mps(mock_session):
    client = HFRClient(username="test_bot", password="secret_password")

    fixtures_dir = Path(__file__).parent / "fixtures"
    fixture_path = fixtures_dir / "mp_inbox.html"
    if fixture_path.exists():
        mp_html = fixture_path.read_text(encoding="utf-8")
    else:
        mp_html = """
        <html>
          <head><title>Messages privés - FORUM HardWare.fr</title></head>
          <body>
            <table class='main'>
              <tr class='sujet ligne_booleen cBackCouleurTab1'>
                <td class='sujetCase1'><img src='https://forum-images.hardware.fr/themes_static/images_forum/1/closedbp.gif' alt='On' /></td>
                <td class='sujetCase3'><a class='cCatTopic' href='/forum2.php?config=hfr.inc&cat=prive&post=3202453'>Salut, c'est un test</a></td>
                <td class='sujetCase6'><a class='Tableau' href='/profilebdd.php'>mycrub</a></td>
                <td class='sujetCase9'><a class='Tableau' href='#'>30-08-2026 à 14:01mycrub</a></td>
              </tr>
            </table>
          </body>
        </html>
        """
    mock_session.get.return_value = MagicMock(status_code=200, text=mp_html)

    mps = client.list_mps(unread_only=True)
    assert len(mps) == 1
    assert mps[0].id == "3202453"
    assert mps[0].sender == "mycrub"
    assert mps[0].subject == "Salut, c'est un test"
    assert mps[0].is_unread is True


def test_hfr_client_get_mp_page_with_fixture(mock_session):
    client = HFRClient(username="test_bot", password="secret_password")
    fixtures_dir = Path(__file__).parent / "fixtures"
    fixture_path = fixtures_dir / "mp_thread_print.html"
    if fixture_path.exists():
        mp_thread_html = fixture_path.read_text(encoding="utf-8")
    else:
        mp_thread_html = "<html><head><title>Test - Messages privés</title></head><body></body></html>"

    mock_session.get.return_value = MagicMock(status_code=200, text=mp_thread_html)
    mp_topic = client.get_mp_page(mp_id=3202453)
    assert mp_topic.title == "Salut, c'est un test"
    assert "2026-08-30" in mp_topic.messages
    messages = list(mp_topic.messages["2026-08-30"].values())
    assert len(messages) == 1
    assert messages[0].author == "MycRub"
    assert "Bonjour, comment ça va ?" in messages[0].text


def test_search_wiki_smilies_by_code_and_keyword():
    client = HFRClient(username="test", password="pwd")
    mock_session = MagicMock()
    client.session = mock_session

    html_resp = """
    <html>
      <body>
        <img src="https://forum-images.hardware.fr/images/perso/1/aloy.gif" alt="[:aloy:1]" title="Aloy 1" />
        <img src="https://forum-images.hardware.fr/images/perso/2/aloy.gif" alt="[:aloy:2]" title="Aloy 2" />
      </body>
    </html>
    """
    mock_session.get.return_value = MagicMock(status_code=200, text=html_resp)

    results = client.search_wiki_smilies(query="[:aloy:2]")
    assert len(results) == 2
    assert results[0].code == "[:aloy:2]"


def test_hfr_client_get_topic_page(mock_session):
    client = HFRClient(username="test", password="pwd")
    mock_html = """
    <html>
      <head><title>HFR</title></head>
      <body>
        <h3>Mon Topic</h3>
        <table class="messagetable">
          <tr>
            <td class="messCase1"><b class="s2">Membre1</b><a rel="nofollow" href="#t12345">#</a></td>
            <td class="messCase2">
              <div class="toolbar"><div class="left">Posté le 29-08-2026 à 12:00:00</div></div>
              <div id="para12345">Message content</div>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """
    mock_session.get.return_value = MagicMock(status_code=200, text=mock_html)
    topic = client.get_topic_page(cat=13, subcat=430, post=100, page=1)
    assert topic.title == "Mon Topic"
    assert topic.post == 100


def test_hfr_client_post_reply_dry_run():
    client = HFRClient(username="test", password="pwd")
    assert client.post_reply(cat=13, subcat=430, post=100, content="Hello", dry_run=True) is True


def test_hfr_client_post_mp_reply_dry_run():
    client = HFRClient(username="test", password="pwd")
    assert client.post_mp_reply(mp_id=999, recipient="Modo", content="Merci :jap:", dry_run=True) is True


def test_hfr_client_get_smiley_keywords(mock_session):
    client = HFRClient(username="test", password="pwd")
    wiki_html = """
    <html>
      <body>
        <form>
          <input type="hidden" name="smiley0" value="[:itm]" />
          <input type="text" name="keywords0" value="itm cynique arrogant mépris" />
        </form>
      </body>
    </html>
    """
    mock_session.post.return_value = MagicMock(status_code=200, text=wiki_html)
    keywords = client.get_smiley_keywords("[:itm]")
    assert "cynique" in keywords
    assert "arrogant" in keywords

