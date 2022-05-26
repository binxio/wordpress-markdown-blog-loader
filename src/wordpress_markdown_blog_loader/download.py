import logging
import os
from pathlib import Path

import click

from wordpress_markdown_blog_loader.api import Wordpress, Post
from wordpress_markdown_blog_loader.blog import Blog


@click.command(name="download")
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
def command(host: str, directory: str, post_id: tuple[str]):
    """
    WordPress posts as markdown.

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
        blog.download_remote_images(wordpress, f"{blog.slug}-" if blog.slug else "")
        logging.info("writing %s", blog.path)
        blog.remove_empty_lines()
        blog.save()

        with open(f"{blog.dir}/index.html", "w") as file:
            file.write(post.content)

        if "</span>" in blog.content:
            os.replace(blog.path, Path(blog.dir).joinpath("index.prespan.md"))
            blog.remove_span_tags()
            blog.save()
