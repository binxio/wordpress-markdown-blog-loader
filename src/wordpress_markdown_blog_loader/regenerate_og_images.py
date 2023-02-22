import logging
import os
from difflib import diff_bytes, unified_diff

import click

from wordpress_markdown_blog_loader.api import Wordpress, Post
from wordpress_markdown_blog_loader.blog import Blog
import sys


@click.command(name="regenerate-og-images")
@click.argument(
    "blog", type=click.Path(exists=True, file_okay=False, readable=True), required=True
)
def command(blog):
    """
    regenerate og images
    """

    blogs = []
    for (root, dirs, files) in os.walk(blog, topdown=True):
        if "index.md" in files:
            blogs.append(os.path.join(blog, root))

    if not blogs:
        click.echo(f"no blogs found in {blog}", err=True)

    for blog in blogs:
        blog = Blog.load(os.path.join(blog, "index.md"))
        blog.generate_og_image()
        blog.save()
