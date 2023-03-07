from bs4 import BeautifulSoup
from bs4.element import NavigableString


def remove_newlines_from_paragraphs(html_document: str) -> str:
    """
    Removes all newlines from text inside paragraphs of the `html_document`.

    Although the HTML specification says that newlines do not constitute line breaks,
    WP interprets them as such :-(

    https://www.w3.org/TR/REC-html40-971218/struct/text.html#whitespace

    >>> remove_newlines_from_paragraphs('<html><body><p>This is a paragraph\\n with some \\n<b>bold</b> and\\n <i>italic</i> text. And\\n it has some\\n <a href="/">links</a> too.\\n</p></body></html>')
    '<html><body><p>This is a paragraph  with some  <b>bold</b> and  <i>italic</i> text. And  it has some  <a href="/">links</a> too. </p></body></html>'
    """
    doc = BeautifulSoup(html_document, "html.parser")
    for paragraph in doc.find_all("p", recursive=True):
        for child in paragraph.children:
            if isinstance(child, NavigableString):
                child.replace_with(child.replace("\n", " "))
    return str(doc)
