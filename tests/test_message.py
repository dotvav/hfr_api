from datetime import datetime
from lxml import html
from hfr.message import Message


def test_message_from_lxml_with_user_id():
    snippet = """
    <table class="messagetable">
        <tr>
            <td class="messCase1">
                <b class="s2">Julian33</b>
                <a rel="nofollow" href="#t48334">#48334</a>
            </td>
            <td class="messCase2">
                <div class="toolbar">
                    <div class="left">Posté le 08-09-2026 à 23:45:10</div>
                    <div class="right">
                        <a href="/hfr/profil-301689.htm"><img src="/profil.gif" alt="Profil" /></a>
                        <a href="/user/addflag.php?config=hfr.inc&cat=32&post=19&numreponse=48334&page=32&ref=5"><img src="/flag.gif" /></a>
                    </div>
                </div>
                <div id="para48334">
                    Bonsoir [:golemini]
                </div>
            </td>
        </tr>
    </table>
    """
    element = html.fragment_fromstring(snippet)
    msg = Message.from_lxml(None, element)
    assert msg is not None
    assert str(msg.id) == "48334"
    assert msg.author == "Julian33"
    assert msg.user_id == 301689
    assert msg.ref == 1245
    assert msg.text == "Bonsoir [:golemini]"
    assert msg.quote() == "[quotemsg=48334,1245,301689]Bonsoir [:golemini][/quotemsg]"
    assert msg.quote("Extrait court") == "[quotemsg=48334,1245,301689]Extrait court[/quotemsg]"


def test_message_from_lxml_with_signature_and_author_title():
    snippet = """
    <table class="messagetable">
        <tr>
            <td class="messCase1">
                <b class="s2">memaster</b>
                <p>pilote officiel</p>
                <a rel="nofollow" href="#t48422">#48422</a>
            </td>
            <td class="messCase2">
                <div class="toolbar">
                    <div class="left">Posté le 09-09-2026 à 18:45:00</div>
                    <div class="right">
                        <a href="/hfr/profil-241619.htm"><img src="/profil.gif" alt="Profil" /></a>
                    </div>
                </div>
                <div id="para48422">
                    <p>mais iel peut changer d'avis aussi.</p>
                    <div style="clear: both;"> </div>
                    <div class="edited"><a href="#">Message cité 1 fois</a></div>
                    <br><span class="signature"> ---------------
                        <br><a href="http://youtube.com">ma conduite</a> | zéro tracas
                    </span>
                </div>
            </td>
        </tr>
    </table>
    """
    element = html.fragment_fromstring(snippet)
    msg = Message.from_lxml(None, element, page=32, index_on_page=18)
    assert msg is not None
    assert str(msg.id) == "48422"
    assert msg.author == "memaster"
    assert msg.author_title == "pilote officiel"
    assert msg.user_id == 241619
    assert msg.ref == (32 - 1) * 40 + 18
    assert msg.text == "mais iel peut changer d'avis aussi."
    assert "ma conduite" in msg.signature
    assert "zéro tracas" in msg.signature
    assert "---------------" not in msg.text
    assert "Message cité" not in msg.text


def test_message_serialization():
    dt = datetime(2026, 9, 8, 23, 45, 10)
    msg = Message(
        topic=None,
        id=48334,
        posted_at=dt,
        author="Julian33",
        text="Hello",
        user_id=301689,
        ref=1245,
        signature="My Signature",
        author_title="Member",
    )
    d = msg.to_dict()
    assert d["user_id"] == 301689
    assert d["ref"] == 1245
    assert d["signature"] == "My Signature"
    assert d["author_title"] == "Member"

    restored = Message.from_dict(None, {
        "id": 48334,
        "posted_at": int(dt.timestamp()),
        "author": "Julian33",
        "text": "Hello",
        "user_id": 301689,
        "ref": 1245,
        "signature": "My Signature",
        "author_title": "Member",
    })
    assert restored.user_id == 301689
    assert restored.ref == 1245
    assert restored.signature == "My Signature"
    assert restored.author_title == "Member"
    assert restored.quote() == "[quotemsg=48334,1245,301689]Hello[/quotemsg]"

