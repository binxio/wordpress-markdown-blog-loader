
import os
import unittest

from wordpress_markdown_blog_loader.blog import Blog

class Test_BlogRender(unittest.TestCase):
    def test_tables(self):
        path = os.path.join(os.path.dirname(__file__), "resources", "tables.md")
        blog = Blog.load(path)
        self.assertIsNotNone(blog.rendered)
        self.assertIn('<table>', blog.rendered)
        self.assertIn('<thead>', blog.rendered)
        self.assertIn('<th>Col B</th>', blog.rendered)
        self.assertIn('<tbody>', blog.rendered)
        self.assertIn('<td style="text-align: left;">Hello</td>', blog.rendered)

if __name__ == '__main__':
    unittest.main()
