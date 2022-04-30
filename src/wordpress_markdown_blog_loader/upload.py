import datetime
import logging
from datetime import datetime

from api import Wordpress
from urllib.parse import urlparse
from wordpress_markdown_blog_loader.blog import Blog


def upsert_post(wp: Wordpress, blog: Blog) -> int:

    if blog.guid:
        if not wp.is_host_for(blog.guid):
            raise ValueError(f"blog {blog.guid} is not stored on {wp.endpoint.host}")

        post = wp.get_resource_by_url(blog.guid)
        if not post:
            raise ValueError(
                "blogs has a guid %s which is not available at %s", blog.guid, wp.host
            )
        post = wp.update_post(blog.guid, blog.to_wordpress(wp))
        logging.info("updated blog '%s' %s", blog.title, post.link)
    else:
        existing_post = wp.get_post_by_slug(blog.slug)
        if existing_post:
            logging.error(
                "a post with the same slug already exists, %s", existing_post.link
            )
            return 1

        post = wp.create_post(blog.to_wordpress(wp))
        blog.guid = post.guid
        blog.save()
        logging.info("uploaded blog '%s' as post %s", blog.title, post.link)

    if blog.og_banner:
        og_banner = wp.upload_media(f"{blog.slug}-og-image", blog.og_banner)
        post_og_banners = post.get("yoast_head_json", {}).get("og_image", [])
        if not next(
            filter(lambda b: b.get("url") == og_banner.url, post_og_banners), None
        ):
            logging.info("updating opengraph image to %s", og_banner.url)
            updated_post = wp.update_post(
                blog.guid,
                {
                    "meta": {
                        "yoast_wpseo_opengraph-image": og_banner.url,
                    }
                },
            )

    if blog.banner:
        banner = wp.upload_media(f"{blog.slug}-image", blog.banner)
        if post.featured_media != banner.medium_id:
            wp.update_post(blog.guid, {"featured_media": banner.medium_id})

    return 0
