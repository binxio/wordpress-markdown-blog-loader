import unittest
from bs4 import BeautifulSoup
from wordpress_markdown_blog_loader.html_to_gutenberg import _wrap_quote

class TestQuoteWrapping(unittest.TestCase):
    def test_wrap_quote_nested_elements(self):
        html = "<blockquote><p>Quote line 1</p><p>Quote line 2</p></blockquote>"
        soup = BeautifulSoup(html, "html.parser")
        elem = soup.blockquote
        result = _wrap_quote(elem)
        
        # Expected behavior: child paragraphs should be wrapped in Gutenberg comments
        self.assertIn("<!-- wp:paragraph -->", result)
        self.assertIn("<p>Quote line 1</p>", result)
        self.assertIn("<p>Quote line 2</p>", result)
        self.assertTrue(result.startswith("<!-- wp:quote -->"))
        self.assertTrue(result.endswith("<!-- /wp:quote -->"))

    def test_wrap_quote_mixed_content(self):
        html = "<blockquote>Just text<p>A paragraph</p></blockquote>"
        soup = BeautifulSoup(html, "html.parser")
        elem = soup.blockquote
        result = _wrap_quote(elem)
        
        self.assertIn("Just text", result)
        self.assertIn("<!-- wp:paragraph -->", result)
        self.assertIn("<p>A paragraph</p>", result)

if __name__ == "__main__":
    unittest.main()
