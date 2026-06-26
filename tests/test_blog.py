
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


class Test_AudioDirective(unittest.TestCase):
    def _blog(self, content):
        blog = Blog()
        blog.title = "Audio post"
        blog.content = content
        return blog

    def test_local_audio_references(self):
        blog = self._blog(
            "## One\n\n::: audio images/clips/a.mp3\n\ntext\n\n"
            "## Two\n\n::: audio images/clips/b.wav\n\nmore\n"
        )
        self.assertEqual(
            blog.local_audio_references,
            {"images/clips/a.mp3", "images/clips/b.wav"},
        )

    def test_remote_audio_not_collected_as_local(self):
        blog = self._blog("::: audio https://cdn.example.com/a.mp3\n")
        self.assertEqual(blog.local_audio_references, set())

    def test_rendered_directive_becomes_audio_block(self):
        # without an uploaded URL it falls back to the raw path (local preview)
        blog = self._blog("## Section\n\n::: audio images/clips/a.mp3\n\ntext\n")
        rendered = blog.rendered
        self.assertIn("<!-- wp:audio -->", rendered)
        self.assertIn('<figure class="wp-block-audio">', rendered)
        self.assertIn('src="images/clips/a.mp3"', rendered)
        # the directive line must not leak through as a paragraph
        self.assertNotIn("::: audio", rendered)


if __name__ == '__main__':
    unittest.main()
