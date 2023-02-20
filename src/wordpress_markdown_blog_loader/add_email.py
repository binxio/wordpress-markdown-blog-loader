import logging
import os
from difflib import diff_bytes, unified_diff

import click

from wordpress_markdown_blog_loader.api import Wordpress, Post
from wordpress_markdown_blog_loader.blog import Blog
import sys


def name_to_email(name: str) -> str:
    """
    name to email Xebia style.

    >>> name_to_email("Mark van Holsteijn")
    'mark.vanholsteijn@xebia.com'
    >>> name_to_email("Jorge Liauw-a-joe")
    'jorge.liauwajoe@xebia.com'
    >>> name_to_email("Jan-Justin van Tonder")
    'janjustin.vantonder@xebia.com'
    """
    email_name_exceptions = {}
    parts = name.replace("-", "").split()
    email = f'{parts[0]}{"." if len(parts) > 1 else ""}{"".join(parts[1:])}@xebia.com'.lower()
    return email_name_exceptions.get(email, email)


@click.command(name="add-email")
@click.argument(
    "blog", type=click.Path(exists=True, file_okay=False, readable=True), required=True
)
def command(blog):
    """
    add email and brand to the metadata
    """

    blogs = []
    for (root, dirs, files) in os.walk(blog, topdown=True):
        if "index.md" in files:
            blogs.append(os.path.join(blog, root))

    if not blogs:
        click.echo(f"no blogs found in {blog}", err=True)

    for blog in blogs:
        blog = Blog.load(os.path.join(blog, "index.md"))
        if blog.author:
            blog.email = name_to_email(blog.author)
        blog.brand = "xebia.com"
        blog.save()
