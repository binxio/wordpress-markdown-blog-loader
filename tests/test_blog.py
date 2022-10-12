
import os
import unittest

from wordpress_markdown_blog_loader.blog import Blog

class Test_BlogRender(unittest.TestCase):

    def test_katex(self):
        path = os.path.join(os.path.dirname(__file__), "resources", "katex.md")
        blog = Blog.load(path)
        self.assertIsNotNone(blog.rendered)

        self.assertIn('<span class="katex-display"><span class="katex">', blog.rendered)


    def test_footnote(self):
        path = os.path.join(os.path.dirname(__file__), "resources", "footnotes.md")
        blog = Blog.load(path)
        self.assertIsNotNone(blog.rendered)

        self.assertIn('<a class="footnote-backref" href="#fnref:1"', blog.rendered)
        self.assertIn('<sup id="fnref:1">', blog.rendered)

if __name__ == '__main__':
    unittest.main()
