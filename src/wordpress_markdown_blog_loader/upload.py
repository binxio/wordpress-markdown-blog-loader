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


@click.command(name="upload")
@click.option(
    "--host", type=str, required=True, nargs=1, help="wordpress host to upload to"
)
@click.option(
    "--regenerate-og-image", is_flag=True, default=False, help="regenerates the og image for the targeted host"
)
@click.argument(
    "blog", type=click.Path(exists=True, file_okay=False, readable=True), required=True
)
def command(host: str, blog: str, regenerate_og_image: bool):
    """
    the blog to Wordpress

    Reads the frontmatter describing the blog from the file index.md in the `blog` directory.
    """
    blog = Blog.load(os.path.join(blog, "index.md"))
    if blog.image and (regenerate_og_image or not blog.og_image):
        logging.info("generating og:image based on %s", blog.image)
        if not blog.brand:
            logging.info("blog brand set to %s", host)
        elif blog.brand != host:
            logging.warning("change brand from %s to %s", blog.brand, host)

        blog.brand = host
        blog.generate_og_image()
        blog.save()

    wordpress = Wordpress(host)
    wordpress.connect()

    try:
        upsert_post(wordpress, blog)
    except ValueError as exception:
        logging.error(exception)
        sys.exit(1)
