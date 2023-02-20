import logging
import os
from difflib import diff_bytes, unified_diff

import click

from wordpress_markdown_blog_loader.api import Wordpress, Post
from wordpress_markdown_blog_loader.blog import Blog
import sys


@click.command(name="change-guid")
@click.option(
    "--host", type=str, required=True, nargs=1, help="wordpress host to change to"
)
@click.argument(
    "blog", type=click.Path(exists=True, file_okay=False, readable=True), required=True
)
def command(host: str, blog):
    """
    change the guid of the blog.

    """
    wordpress = Wordpress(host)
    wordpress.connect()

    blogs = []
    for (root, dirs, files) in os.walk(blog, topdown=True):
        if "index.md" in files:
            blogs.append(os.path.join(blog, root))

    if not blogs:
        click.echo(f"no blogs found in {blog}", err=True)

    for blog in blogs:
        blog = Blog.load(os.path.join(blog, "index.md"))
        post = wordpress.get_post_by_slug(blog.slug)
        if post:
            logging.info("blog with slug %s has guid %s", blog.slug, post.guid)
            blog.guid = post.guid
            blog.save()
        else:
            logging.warning("blog with slug %s NOT found on %s", blog.slug, host)
