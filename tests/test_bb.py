from hfr import bb

def test_html_to_bb_basic():
    assert bb.html_to_bb("<strong>x</strong>") == "[b]x[/b]"
    assert bb.html_to_bb("<em>x</em>") == "[i]x[/i]"
    assert bb.html_to_bb("<span class=\"u\">x</span>") == "[u]x[/u]"
    assert bb.html_to_bb("<strike>x</strike>") == "[strike]x[/strike]"
    assert bb.html_to_bb("<a href=\"x\">y</a>") == "[url=x]y[/url]"
    assert bb.html_to_bb("<img src=\"x\" alt=\"y\"/>") == "[img]x[/img]"
    assert bb.html_to_bb("<img src=\"x\" alt=\":o\"/>") == ":o"
    assert bb.html_to_bb("<img src=\"x\" alt=\"[:y]\"/>") == "[:y]"
    assert bb.html_to_bb("<ul><li> x</li></ul>") == "[*] x"
    assert bb.html_to_bb("<a href=\"mailto:lolcat@lol.cat\">") == "[email]lolcat@lol.cat[/email]"


def test_html_to_bb_advanced():
    input = """<p>Un test avec du <strong>gras et de <em>l'italique</em> dans le gras</strong>. Du <span class="u">souligné</span> et du <strike>barré</strike>. Aussi, un smiley perso <img src="https://forum-images.hardware.fr/images/perso/mycrub.gif" alt="[:mycrub]" title="[:mycrub]" /> et un smiley de base <img src="https://forum-images.hardware.fr/icones/redface.gif" alt=":o" title=":o" /> ainsi que
<br /></p><ul><li> une image <img src="https://forum-images.hardware.fr/images/perso/1/mycrub.gif" alt="https://forum-images.hardware.fr/images/perso/1/mycrub.gif" title="https://forum-images.hardware.fr/images/perso/1/mycrub.gif" onload="md_verif_size(this,'Cliquez pour agrandir','2','250')" style="margin: 5px"/>
</li><li> <a rel="nofollow" href="https://lolcat.lol.cat" target="_blank" class="cLink">un lien</a></li></ul><p><div style="clear: both;"> </div></p></div>"""
    expected = """Un test avec du [b]gras et de [i]l'italique[/i] dans le gras[/b]. Du [u]souligné[/u] et du [strike]barré[/strike]. Aussi, un smiley perso [:mycrub] et un smiley de base :o ainsi que
[*] une image [img]https://forum-images.hardware.fr/images/perso/1/mycrub.gif[/img]
[*] [url=https://lolcat.lol.cat]un lien[/url]"""
    output = bb.html_to_bb(input)
    assert expected == output

    input = """<div id="para1980038934"><p>Un quote qui contient du souligné:
<br /></p><div class="container"><table class="citation"><tr class="none"><td><b class="s1"><a href="/forum2.php?config=hfr.inc&amp;cat=prive&amp;post=3042031&amp;page=1&amp;p=1&amp;sondage=0&amp;owntopic=0&amp;trash=0&amp;trash_post=0&amp;print=0&amp;numreponse=0&amp;quote_only=0&amp;new=0&amp;nojs=0#t1980038387" class="Topic">MycRub a écrit :</a></b><br /><br /><p><span class="u">souligné</span><br /></p></td></tr></table></div><p>
<br />&nbsp;<br />Une citation :
<br /></p><div class="container"><table class="quote"><tr class="none"><td><b class="s1">Citation :</b><br /><br /><p>Il fait chaud.<br /></p></td></tr></table></div><p>
<br />&nbsp;<br />Un spoiler :
<br /></p><div class="container"><table class="spoiler" onclick="javascript:swap_spoiler_states(this)" style="cursor:pointer;"><tr class="none"><td><b class="s1Topic">Spoiler :</b><br /><br /><div class="Topic masque"><p>Coucou</p></div></td></tr></table></div><p>
<br />&nbsp;<br />Un bloc fx :
<br /></p><table class="fixed"><tr class="none"><td><p>Monospace ?</p></td></tr></table><p>
<br />&nbsp;<br />Du code :
<br /></p><table class="code"><tr class="none"><td><b class="s1" style="font-family: Verdana, Helvetica, Arial, Sans-serif;">Code :</b><br /><ol id="code1" class="olcode"><li>toto=1;</li><li>tata=2;</li></ol></td></tr></table><p>
<br />&nbsp;<br />Un email :
<br /><a rel="nofollow" href="mailto:lolcat@lol.cat" class="cLink">lolcat@lol.cat</a>
<br />&nbsp;<br />De la couleur :
<br />Texte <span style="color:#0000FF">bleu</span> et <span style="color:#FF0000">rouge</span><div style="clear: both;"> </div></p></div>"""
    expected = """Un quote qui contient du souligné:
[quotemsg=1980038387,1,0][u]souligné[/u][/quotemsg]

Une citation :
[quote]Il fait chaud.[/quote]

Un spoiler :
[spoiler]Coucou[/spoiler]

Un bloc fx :
[fixed]Monospace ?[/fixed]

Du code :
[code]toto=1;
tata=2;[/code]

Un email :
[email]lolcat@lol.cat[/email]

De la couleur :
Texte [#0000FF]bleu[/#0000FF] et [#FF0000]rouge[/#FF0000]"""
    output = bb.html_to_bb(input)
    assert expected == output


def test_format_quote():
    q = bb.format_quote(message_id=75205063, text="Test message", ref=1252, user_id=256366)
    assert q == "[quotemsg=75205063,1252,256366]Test message[/quotemsg]"

    q_simple = bb.format_quote(message_id="12345", text="Coucou")
    assert q_simple == "[quotemsg=12345,1,0]Coucou[/quotemsg]"


def test_format_author_quote():
    q = bb.format_author_quote(author="MycRub", text="Hello world")
    assert q == "[quote=MycRub]Hello world[/quote]"


def test_emoji_to_cdn_bb():
    # Simple emoji
    assert bb.emoji_to_cdn_bb("Super ! 🚀") == "Super ! [img]https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/1f680.png[/img]"
    # Modifier / Skin tone
    assert bb.emoji_to_cdn_bb("👍🏽") == "[img]https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/1f44d-1f3fd.png[/img]"
    # Zero Width Joiner sequence
    assert bb.emoji_to_cdn_bb("👨‍💻") == "[img]https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/1f468-200d-1f4bb.png[/img]"
    # Plain text untouched
    assert bb.emoji_to_cdn_bb("Texte sans emoji") == "Texte sans emoji"


def test_html_to_bb_with_user_resolver():
    html_input = """<div class="container"><table class="citation"><tr class="none"><td><b class="s1"><a href="/forum2.php?...#t1980038387" class="Topic">Golemini a écrit :</a></b><br /><br /><p>Coucou robot<br /></p></td></tr></table></div>"""

    # 1. Dict resolver
    res1 = bb.html_to_bb(html_input, user_resolver={"Golemini": 1215586})
    assert res1 == "[quotemsg=1980038387,1,1215586]Coucou robot[/quotemsg]"

    # 2. Callable resolver
    def my_resolver(pseudo: str):
        if pseudo.lower() == "golemini":
            return 1215586
        return 0

    res2 = bb.html_to_bb(html_input, user_resolver=my_resolver)
    assert res2 == "[quotemsg=1980038387,1,1215586]Coucou robot[/quotemsg]"

    # 3. Unknown user defaults to 0
    res3 = bb.html_to_bb(html_input, user_resolver={"Other": 999})
    assert res3 == "[quotemsg=1980038387,1,0]Coucou robot[/quotemsg]"


def test_html_to_bb_author_quote_without_msg_id():
    html_input = """<div class="container"><table class="citation"><tr class="none"><td><b class="s1">Golemini a écrit :</b><br /><br /><p>Citation nommée manuelle</p></td></tr></table></div>"""
    res = bb.html_to_bb(html_input)
    assert res == "[quote=Golemini]Citation nommée manuelle[/quote]"

