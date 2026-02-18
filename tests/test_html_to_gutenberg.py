import unittest
from bs4 import BeautifulSoup, NavigableString, Comment

from wordpress_markdown_blog_loader.html_to_gutenberg import (
    _wrap_paragraph,
    _wrap_heading,
    _wrap_pre,
    _wrap_list,
    _wrap_image,
    _wrap_in_gutenberg_comments,
    convert,
)


class TestGutenbergWrapFunctions(unittest.TestCase):
    def test_wrap_paragraph(self):
        soup = BeautifulSoup("<p>This is a paragraph.</p>", "html.parser")
        p_elem = soup.p
        expected = (
            "<!-- wp:paragraph -->\n<p>This is a paragraph.</p>\n<!-- /wp:paragraph -->"
        )
        self.assertEqual(_wrap_paragraph(p_elem), expected)

    def test_wrap_heading(self):
        soup = BeautifulSoup("<h2>Heading</h2>", "html.parser")
        h_elem = soup.h2
        result = _wrap_heading(h_elem)
        self.assertIn('class="wp-block-heading"', result)
        self.assertTrue(result.startswith("<!-- wp:heading -->"))
        self.assertTrue(result.endswith("<!-- /wp:heading -->"))

    def test_wrap_pre(self):
        # pre with code and both have classes
        html = '<pre class="wp-block-code hljs"><code class="language-hcl">terraform code</code></pre>'
        soup = BeautifulSoup(html, "html.parser")
        pre_elem = soup.pre
        result = _wrap_pre(pre_elem)
        self.assertTrue(result.startswith("<!-- wp:code -->"))
        self.assertIn('<pre class="wp-block-code">', result)
        self.assertIn("<code>terraform code</code>", result)
        self.assertTrue(result.endswith("<!-- /wp:code -->"))

        # pre with no code class
        html = "<pre><code>no class code</code></pre>"
        soup = BeautifulSoup(html, "html.parser")
        pre_elem = soup.pre
        result = _wrap_pre(pre_elem)
        self.assertIn("<pre>", result)
        self.assertIn("<code>no class code</code>", result)

    def test_wrap_ul_list(self):
        html = '<ul class="wp-block-list"><li>item1</li><li>item2</li></ul>'
        soup = BeautifulSoup(html, "html.parser")
        ul_elem = soup.ul
        result = _wrap_list(ul_elem)
        self.assertTrue(result.startswith("<!-- wp:list"))
        self.assertIn('class="wp-block-list"', result)
        self.assertIn("<!-- wp:list-item -->", result)
        self.assertIn("<!-- /wp:list-item -->", result)
        self.assertTrue(result.endswith("<!-- /wp:list -->"))

    def test_wrap_ol_list(self):
        html = "<ol><li>first</li><li>second</li></ol>"
        soup = BeautifulSoup(html, "html.parser")
        ol_elem = soup.ol
        result = _wrap_list(ol_elem)
        self.assertIn('"ordered":true', result)
        self.assertIn("<!-- wp:list-item -->", result)

    def test_wrap_image(self):
        soup = BeautifulSoup('<img src="img.png" alt="desc"/>', "html.parser")
        img_elem = soup.img
        res = _wrap_image(img_elem)
        self.assertTrue(res.startswith("<!-- wp:image -->"))
        self.assertIn('<img alt="desc" src="img.png"/>', res)
        self.assertTrue(res.endswith("<!-- /wp:image -->"))

    def test_wrap_in_gutenberg_comments_with_comment(self):
        comment = Comment(" a comment ")
        res = _wrap_in_gutenberg_comments(comment)
        self.assertEqual(res, str(comment))

    def test_wrap_in_gutenberg_comments_with_navigablestring(self):
        ns = NavigableString("just text")
        res = _wrap_in_gutenberg_comments(ns)
        self.assertEqual(res, "just text")

    def test_wrap_in_gutenberg_comments_fallback(self):
        soup = BeautifulSoup("<span>custom</span>", "html.parser")
        span_elem = soup.span
        res = _wrap_in_gutenberg_comments(span_elem)
        self.assertEqual(res, "<span>custom</span>")


import unittest


class TestConvertFunction(unittest.TestCase):
    def test_convert_minimal(self):
        title = 'My "special" Blog'
        html_body = "<p>Hello world</p>"
        expected_hero = '<!-- wp:xebia/blog-hero {"blogHeroTitle":"My \\"special\\" Blog","lock":{"move":true,"remove":true}} /-->\n\n'
        expected_para = (
            "<!-- wp:paragraph -->\n<p>Hello world</p>\n<!-- /wp:paragraph -->"
        )

        result = convert(title, html_body)

        # Check hero block present and title correctly escaped
        self.assertIn(expected_hero, result)
        # Check main content start/end blocks present
        self.assertIn("<!-- wp:xebia/content-section -->", result)
        self.assertIn("<!-- /wp:xebia/content-section -->", result)
        # Check block content wrapped appropriately
        self.assertIn('<div class="wp-block-xebia-content-section">', result)
        self.assertIn(expected_para, result)

    def test_convert_with_list_and_image(self):
        title = "List and Image"
        html_body = '<ul><li>One</li></ul><img src="a.png" />'
        result = convert(title, html_body)
        # Check both the list and image blocks are present in Gutenberg comments
        self.assertIn("<!-- wp:list", result)
        self.assertIn("<li>One</li>", result)
        self.assertIn("<!-- wp:image -->", result)
        self.assertIn('<img src="a.png"/>', result)

    def test_convert_handles_multiple_elements(self):
        title = "Test"
        html_body = "<p>First</p><h2>Second</h2><pre><code>Code</code></pre>"
        result = convert(title, html_body)
        self.assertIn("<!-- wp:paragraph -->", result)
        self.assertIn("<!-- wp:heading -->", result)
        self.assertIn("<!-- wp:code -->", result)


if __name__ == "__main__":
    unittest.main()
