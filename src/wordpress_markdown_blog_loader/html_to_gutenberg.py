from bs4 import BeautifulSoup, NavigableString, Comment


def _wrap_in_gutenberg_comments(element):
    if isinstance(element, (NavigableString, Comment)):
        return str(element)
    if element.name == "p":
        return _wrap_paragraph(element)
    if element.name.startswith("h"):
        return _wrap_heading(element)
    if element.name == "pre":
        return _wrap_pre(element)
    if element.name in ("ul", "ol"):
        return _wrap_list(element)
    if element.name == "img":
        return _wrap_image(element)
    return str(element)


def _wrap_paragraph(element):
    return f"<!-- wp:paragraph -->\n{str(element)}\n<!-- /wp:paragraph -->"


def _wrap_heading(element):
    element["class"] = ["wp-block-heading"]
    return f"<!-- wp:heading -->\n{str(element)}\n<!-- /wp:heading -->"


def _wrap_pre(element):
    code_elem = element.find("code")
    language = None
    # Handle pre class logic
    classes = element.get("class", [])
    if "wp-block-code" in classes:
        element["class"] = ["wp-block-code"]
    elif "class" in element.attrs:
        del element["class"]
    # Extract language from code if available
    if code_elem:
        code_classes = code_elem.get("class", [])
        for cls in code_classes:
            if cls.startswith("language-"):
                language = cls.split("-", 1)[1]
        if "class" in code_elem.attrs:
            del code_elem["class"]
    # it is unclear how to specify the language in Wordpress the language
    return f"<!-- wp:code -->\n{str(element)}\n<!-- /wp:code -->"


def _wrap_list(element):
    ordered = element.name == "ol"
    class_attr = element.get("class", [None])[0]
    params = []
    if ordered:
        params.append('"ordered":true')
    if class_attr:
        params.append(f'"className":"{class_attr}"')
    wp_list_type = f" {{ {', '.join(params)} }}" if params else ""
    # Wrap <li> in wp:list-item comments
    soup = BeautifulSoup(str(element), "html.parser")
    for li in soup.find_all("li"):
        li.insert_before(Comment(" wp:list-item "))
        li.insert_after(Comment(" /wp:list-item "))
    return f"<!-- wp:list{wp_list_type} -->\n{soup}\n<!-- /wp:list -->"


def _wrap_image(element):
    return f"<!-- wp:image -->\n{str(element)}\n<!-- /wp:image -->"


def convert(title, html_body):
    soup = BeautifulSoup(html_body, "html.parser")
    blocks = []

    for element in soup.body.contents if soup.body else soup.contents:
        blocks.append(_wrap_in_gutenberg_comments(element))

    title = title.replace('"', '\\"')
    hero_block = f'<!-- wp:xebia/blog-hero {{"blogHeroTitle":"{title}","lock":{{"move":true,"remove":true}}}} /-->\n\n'
    content_section_start = "<!-- wp:xebia/content-section -->\n"
    content_section_end = "\n<!-- /wp:xebia/content-section -->"
    content_section = (
        '<div class="wp-block-xebia-content-section">' + "\n".join(blocks) + "</div>"
    )

    return hero_block + content_section_start + content_section + content_section_end


def main():
    with open("input.html") as f:
        html_body = f.read()
    title = "A piece of yaml"
    gutenberg_html = convert(title, html_body)
    with open("converted.html", "w") as f:
        f.write(gutenberg_html)


if __name__ == "__main__":
    main()
