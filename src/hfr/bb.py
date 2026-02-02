"""BB code handling"""

from bs4 import BeautifulSoup, NavigableString


def convert_inline_tags(html: str, context: dict = {}) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for element in soup.find_all(True, recursive=False):
        if element.name == "strong":
            element.replace_with(
                NavigableString(
                    f"[b]{convert_inline_tags(element.decode_contents(), context)}[/b]"
                )
            )
        elif element.name == "span" and "u" in element.get("class", []):
            element.replace_with(
                NavigableString(
                    f"[u]{convert_inline_tags(element.decode_contents(), context)}[/u]"
                )
            )
        elif element.name == "span" and element.get("style"):
            style = element.get("style")
            if len(style) > 7 and style[:7] == "color:#":
                color = style[-6:]
                element.replace_with(
                    NavigableString(
                        f"[#{color}]{convert_inline_tags(element.decode_contents(), context)}[/#{color}]"
                    )
                )
        elif element.name == "em":
            element.replace_with(
                NavigableString(
                    f"[i]{convert_inline_tags(element.decode_contents(), context)}[/i]"
                )
            )
        elif element.name == "strike":
            element.replace_with(
                NavigableString(
                    f"[strike]{convert_inline_tags(element.decode_contents(), context)}[/strike]"
                )
            )
        elif element.name in ("ul", "ol"):
            context["not_first_line"] = False
            element.replace_with(
                NavigableString(
                    f"{convert_inline_tags(element.decode_contents(), context)}"
                )
            )
            context["not_first_line"] = True
        elif element.name == "li":
            table_class = context.get("table_class", "")
            bullet_style = "" if table_class == "code" else "[*]"
            new_line = "\n" if context.get("not_first_line", False) else ""
            context["not_first_line"] = True
            element.replace_with(
                NavigableString(
                    f"{new_line}{bullet_style}{convert_inline_tags(element.decode_contents(), context)}"
                )
            )
        elif element.name == "a":
            href = element.get("href", "")
            if len(href) > 6 and href[:7] == "mailto:":
                element.replace_with(NavigableString(f"[email]{href[7:]}[/email]"))
            else:
                element.replace_with(
                    NavigableString(
                        f"[url={href}]{convert_inline_tags(element.decode_contents(), context)}[/url]"
                    )
                )
        elif element.name == "img":
            src = element.get("src", "")
            alt = element.get("alt", "")
            if alt[0] in ("[", ":"):
                # For smileys, just use the alt text
                element.replace_with(NavigableString(alt))
            else:
                # For regular images, convert to BB code format
                element.replace_with(NavigableString(f"[img]{src}[/img]"))
        elif element.name == "table":
            table_class = element.get("class")[0] if element.get("class") else ""
            new_context = {"table_class": table_class}
            if "citation" in table_class:
                bb_tag = "quotemsg"
                a = element.find("a")
                href = a.get("href") if a else ""
                href_tokens = href.split('#t')
                bb_details = f"={href_tokens[1] if len(href_tokens) > 1 else "0"},0,0"  # TODO create reference =msgid,?,userid
            else:
                bb_tag = table_class
                bb_details = ""
            content = element.find(["p", "ol"])
            if content:
                converted_content = convert_inline_tags(
                    content.decode_contents(), new_context
                )
                if len(converted_content) and converted_content[-1] == "\n":
                    converted_content = converted_content[
                        :-1
                    ]  # remove stupid trailing "\n"
                element.replace_with(
                    NavigableString(
                        f"[{bb_tag}{bb_details}]{converted_content}[/{bb_tag}]"
                    )
                )
        else:
            if not isinstance(element, NavigableString):
                element.replace_with(
                    NavigableString(
                        convert_inline_tags(element.decode_contents(), context)
                    )
                )

    return soup.get_text()


def html_to_bb(html: str) -> str:
    return convert_inline_tags(
        html.replace("&nbsp;", "").replace("\n", "").replace("<br />", "\n")
    ).strip()
