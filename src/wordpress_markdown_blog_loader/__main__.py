import os
import logging

import click
from wordpress_markdown_blog_loader.api import Wordpress
from wordpress_markdown_blog_loader.load import upsert_post, Blog


@click.group()
def main():
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"), format="%(levelname)s: %(message)s"
    )


@main.command()
@click.option(
    "--host", type=str, required=True, nargs=1, help="wordpress host to upload to"
)
@click.argument(
    "blog", type=click.Path(exists=True, file_okay=False, readable=True), required=True
)
def upload(host: str, blog: str):
    """
    the wordpress blog post.

    Reads the frontmatter describing the blog from the file index.md in the `blog` directory.
    """
    blog = Blog.load(os.path.join(blog, "index.md"))
    if not blog.og_banner:
        blog.generate_og_banner()

    wordpress = Wordpress(host)
    wordpress.connect()

    upsert_post(wordpress, blog)


if __name__ == "__main__":
    main()
