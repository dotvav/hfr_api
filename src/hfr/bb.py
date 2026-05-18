"""BB code handling"""

from lxml import html as lxml_html
from lxml import etree


def convert_inline_tags(element, context: dict | None = None) -> str:
    """Convert an lxml element's children to BB code recursively."""
    if context is None:
        context = {}

    result = []

    # Process the element's text (text before first child)
    if element.text:
        result.append(element.text)

    for child in element:
        tag = child.tag
        if tag == "strong" or tag == "b":
            inner = convert_inline_tags(child, context)
            result.append(f"[b]{inner}[/b]")
        elif tag == "span":
            classes = (child.get("class") or "").split()
            style = child.get("style") or ""
            if "u" in classes:
                inner = convert_inline_tags(child, context)
                result.append(f"[u]{inner}[/u]")
            elif style and len(style) > 7 and style[:7] == "color:#":
                color = style[-6:]
                inner = convert_inline_tags(child, context)
                result.append(f"[#{color}]{inner}[/#{color}]")
            else:
                inner = convert_inline_tags(child, context)
                result.append(inner)
        elif tag == "em" or tag == "i":
            inner = convert_inline_tags(child, context)
            result.append(f"[i]{inner}[/i]")
        elif tag == "strike":
            inner = convert_inline_tags(child, context)
            result.append(f"[strike]{inner}[/strike]")
        elif tag in ("ul", "ol"):
            old_not_first = context.get("not_first_line", False)
            context["not_first_line"] = False
            inner = convert_inline_tags(child, context)
            context["not_first_line"] = old_not_first
            result.append(inner)
        elif tag == "li":
            table_class = context.get("table_class", "")
            bullet_style = "" if table_class == "code" else "[*]"
            new_line = "\n" if context.get("not_first_line", False) else ""
            context["not_first_line"] = True
            inner = convert_inline_tags(child, context)
            result.append(f"{new_line}{bullet_style}{inner}")
        elif tag == "a":
            href = child.get("href") or ""
            if len(href) > 6 and href[:7] == "mailto:":
                result.append(f"[email]{href[7:]}[/email]")
            else:
                inner = convert_inline_tags(child, context)
                result.append(f"[url={href}]{inner}[/url]")
        elif tag == "img":
            src = child.get("src") or ""
            alt = child.get("alt") or ""
            if alt and alt[0] in ("[", ":"):
                # For smileys, just use the alt text
                result.append(alt)
            else:
                # For regular images, convert to BB code format
                result.append(f"[img]{src}[/img]")
        elif tag == "table":
            classes = (child.get("class") or "").split()
            table_class = classes[0] if classes else ""
            new_context = {"table_class": table_class}
            if "citation" in table_class:
                bb_tag = "quotemsg"
                a = child.find(".//a")
                href = (a.get("href") or "") if a is not None else ""
                href_tokens = href.split("#t")
                bb_details = f"={href_tokens[1] if len(href_tokens) > 1 else '0'},0,0"
            else:
                bb_tag = table_class
                bb_details = ""
            # Look for content in <p> or <ol>
            content = child.find(".//p")
            if content is None:
                content = child.find(".//ol")
            if content is not None:
                converted_content = convert_inline_tags(content, new_context)
                if converted_content and converted_content[-1] == "\n":
                    converted_content = converted_content[:-1]
                result.append(
                    f"[{bb_tag}{bb_details}]{converted_content}[/{bb_tag}]"
                )
        elif tag == "div":
            # Recurse into divs (e.g. spoiler content divs, clear divs)
            # Skip "clear" divs that just contain whitespace
            style = child.get("style") or ""
            if "clear" in style:
                pass  # skip clear divs
            else:
                inner = convert_inline_tags(child, context)
                result.append(inner)
        elif tag == "p":
            inner = convert_inline_tags(child, context)
            result.append(inner)
        else:
            # Generic element - recurse into children
            inner = convert_inline_tags(child, context)
            result.append(inner)

        # Process tail text (text after this child, before next sibling)
        if child.tail:
            result.append(child.tail)

    return "".join(result)


def html_to_bb(html_str: str) -> str:
    """Convert HTML string to BB code."""
    cleaned = (
        html_str.replace("&nbsp;", "")
        .replace("\n", "")
        .replace("<br />", "\n")
        .replace("<br/>", "\n")
        .replace("<br>", "\n")
    )
    # Wrap in a root element for lxml parsing
    wrapped = f"<div>{cleaned}</div>"
    root = lxml_html.fragment_fromstring(wrapped, create_parent=False)
    return convert_inline_tags(root).strip()
