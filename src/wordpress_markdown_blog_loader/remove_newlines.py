from bs4 import BeautifulSoup
def remove_newlines_from_paragraphs(document: str) -> str:
    """
    removes all newlines from the text inside html paragraph sections.

    >>> remove_newlines_from_paragraphs('<html><body><p>This is a paragraph\\n with some \\n<b>bold</b> and\\n <i>italic</i> text. And\\n it has some\\n <a href="/">links</a> too.\\n</p></body></html>')
    '<html><body><p>This is a paragraph  with some  <b>bold</b> and  <i>italic</i> text. And  it has some  <a href="/">links</a> too. </p></body></html>'
    """
    doc = BeautifulSoup(document, 'html.parser')
    for paragraph in doc.find_all('p', recursive=True):
        for child in paragraph.children:
            if not child.name:
                child.replace_with(child.replace("\n", " "))
    return str(doc)