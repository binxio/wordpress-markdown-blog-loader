import logging
from difflib import diff_bytes, unified_diff
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
        if wp_post.get("content") != post.raw_content:
            logging.info("updated blog '%s' %s", blog.title, post.link)
            post = wp.update_post(blog.guid, wp_post)
        else:
            logging.info("content of '%s' is up-to-date.", blog.title)
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

    logging.info("post available at %s", post.link)

    return 0
