import logging
import os
from difflib import diff_bytes, unified_diff

import click

from wordpress_markdown_blog_loader.api import Wordpress, Post
from wordpress_markdown_blog_loader.blog import Blog
import sys


def upsert_post(wp: Wordpress, blog: Blog) -> int:

    if blog.guid:
        if not wp.is_host_for(blog.guid):
            raise ValueError(f"blog {blog.guid} is not stored on {wp.endpoint.host}")

        post = Post(wp.get_resource_by_url(blog.guid, {"context": "edit"}))
        if not post:
            raise ValueError(
                "blogs has a guid %s which is not available at %s", blog.guid, wp.host
            )
        wp_post = blog.to_wordpress(wp)
        logging.info("updating blog '%s' %s", blog.title, post.link)
        post = wp.update_post(blog.guid, wp_post)
    else:
        existing_post = wp.get_post_by_slug(blog.slug)
        if existing_post:
            logging.error(
                "a post with the same slug already exists, %s", existing_post.guid
            )
            return 1

        post = wp.create_post(blog.to_wordpress(wp))
        blog.guid = post.guid
        blog.save()
        logging.info("uploaded blog '%s' as post %s", blog.title, post.link)

    if blog.og_image:
        og_image = wp.upload_media(f"{blog.slug}-og-banner", blog.og_image_path)
        post_og_images = post.get("yoast_head_json", {}).get("og_image", [])
        if not next(
            filter(lambda b: b.get("url") == og_image.url, post_og_images), None
        ):
            logging.info("updating opengraph image to %s", og_image.url)
            updated_post = wp.update_post(
                blog.guid,
                {
                    "meta": {
                        "yoast_wpseo_opengraph-image": og_image.url,
                    }
                },
            )

    if blog.image:
        banner = wp.upload_media(f"{blog.slug}-banner", blog.image_path)
        if post.featured_media != banner.medium_id:
            wp.update_post(blog.guid, {"featured_media": banner.medium_id})

    logging.info("post available at %s", post.link)

    return 0


@click.command(name="update-canonical")
@click.option(
    "--host",
    type=str,
    required=True,
    nargs=1,
    help="wordpress host to update the post of",
)
@click.argument(
    "post-id",
    type=int,
    nargs=-1,
)
def command(host: str, post_id: tuple[str]):
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
                    lambda p: wordpress.get("blogs", p, ({"context": "edit"})), post_id
                ),
            )
        )

        for i, post in enumerate(posts):
            if not post:
                logging.error("post with id %d was not found", post_id[i])
                exit(1)
    else:
        posts = wordpress.posts({"context": "edit", "post_type": "blogposts"})

    for post in posts:
        canonical = f"https://xebia.com/blog/{post.slug}"
        properties = {"meta": {"yoast_wpseo_canonical": canonical}}

        if post.get("yoast_head_json", {}).get("canonical") == canonical:
            logging.info("canonical set on '%s'", post.title)
        else:
            logging.info("updating canonical on '%s'", post.title)
            wordpress.update_post(post.guid, properties)
