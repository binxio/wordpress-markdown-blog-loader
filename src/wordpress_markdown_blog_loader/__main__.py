import os
import sys
import logging
from pathlib import Path

import click
import markdownify
from wordpress_markdown_blog_loader.api import Wordpress
from wordpress_markdown_blog_loader.upload import upsert_post
from wordpress_markdown_blog_loader.blog import Blog


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
    if blog.banner and not blog.og_banner:
        logging.info("generating og:image based on %s", blog.banner)
        blog.generate_og_banner()

    wordpress = Wordpress(host)
    wordpress.connect()

    try:
        upsert_post(wordpress, blog)
    except ValueError as exception:
        logging.error(exception)
        sys.exit(1)


@main.command()
@click.option(
    "--host", type=str, required=True, nargs=1, help="wordpress host to upload to"
)
@click.option(
    "--directory",
    type=click.Path(file_okay=False, exists=True),
    required=True,
    nargs=1,
    help="to download to",
)
def download(host: str, directory: str):

    wordpress = Wordpress(host)
    wordpress.connect()

    for post in wordpress.posts({}):
        blog = Blog.from_wordpress(post, directory, wordpress)
        blog.download_remote_images(wordpress)
        logging.info("writing %s", blog.path)
        blog.save()

        with open(f"{blog.dir}/index.html", "w") as file:
            file.write(post.content)

        if "</span>" in blog.content:
            os.replace(blog.path, Path(blog.dir).joinpath("index.prespan.md"))
            blog.remove_span_tags()
            blog.save()


if __name__ == "__main__":
    main()
