import logging
import os
import sys
from pathlib import Path

import click
from wordpress_markdown_blog_loader.api import Wordpress, Post
from wordpress_markdown_blog_loader.blog import Blog
from wordpress_markdown_blog_loader.upload import upsert_post


@click.group()
def main():
    """
    Wordpress CLI
    """
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"), format="%(levelname)s: %(message)s"
    )


@main.group()
def posts():
    """
    Wordpress posts up- and download
    """
    pass


@posts.command()
@click.option(
    "--host", type=str, required=True, nargs=1, help="wordpress host to upload to"
)
@click.argument(
    "blog", type=click.Path(exists=True, file_okay=False, readable=True), required=True
)
def upload(host: str, blog: str):
    """
    the wordpress blog post to Wordpress.

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


@posts.command()
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
@click.argument(
    "post-id",
    type=int,
    nargs=-1,
)
def download(host: str, directory: str, post_id: tuple[str]):
    """
    all posts as markdown.

    Reads all the posts from a Wordpress installation and writes each post as frontmatter
    document. If posts id's are specified, the selected posts are downloaded.
    """
    wordpress = Wordpress(host)
    wordpress.connect()

    if post_id:
        posts = list(
            map(
                lambda p: Post(p) if p else None,
                map(
                    lambda p: wordpress.get("posts", p, ({"context": "edit"})), post_id
                ),
            )
        )

        for i, post in enumerate(posts):
            if not post:
                logging.error("post with id %d was not found", post_id[i])
                exit(1)
    else:
        posts = wordpress.posts({"context": "edit"})

    for post in posts:
        blog = Blog.from_wordpress(post, directory, wordpress)
        blog.download_remote_images(wordpress)
        logging.info("writing %s", blog.path)
        blog.remove_empty_lines()
        blog.save()

        with open(f"{blog.dir}/index.html", "w") as file:
            file.write(post.content)

        if "</span>" in blog.content:
            os.replace(blog.path, Path(blog.dir).joinpath("index.prespan.md"))
            blog.remove_span_tags()
            blog.save()


if __name__ == "__main__":
    main()
