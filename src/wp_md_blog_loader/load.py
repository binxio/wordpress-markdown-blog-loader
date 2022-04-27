import datetime
import logging
import os
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse
from pathlib import Path

import frontmatter
import pytz
from PIL import Image
from api import Wordpress
from binx_og_image_generator.generator import (
    generate as generate_og_image,
    Blog as ImageGeneratorBlog,
)
from markdown import markdown


def JSONSerializer(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()


categories = {}


class Blog(object):
    def __init__(self):
        self.dir: Path = None
        self.path: Path = None
        self.blog: Blog = None
        self.uploaded_images: dict[str, Image] = {}
        self.markdown_image_pattern = re.compile(
            r"\!\[(?P<alt_text>[^]]*)\]\((?P<url>[^)]*)\)"
        )

    @staticmethod
    def load(path: str) -> "Blog":
        result = Blog()
        result.path = Path(path)
        result.dir = Path(path).parent
        if not result.path.exists():
            raise ValueError(f"{path} does not exist")

        with open(path, "r") as f:
            result.blog = frontmatter.load(f)
        return result

    def save(self):
        with open(self.path, "wb") as f:
            frontmatter.dump(self.blog, f)

    @property
    def slug(self):
        return self.blog.metadata.get("slug")

    @property
    def author(self):
        return self.blog.metadata.get("author")

    @property
    def title(self):
        return self.blog.metadata.get("title")

    @property
    def subtitle(self):
        return self.blog.metadata.get("subtitle")

    @property
    def status(self):
        return self.blog.metadata.get("status", "draft")

    @property
    def content(self):
        return self.blog.content

    @property
    def og(self):
        return self.blog.metadata.get("og", {})

    @property
    def image(self):
        return self.blog.metadata.get("image", "./images/banner.jpg")

    @property
    def og_image(self):
        return self.og.get("image", "./images/og-banner.jpg")

    @property
    def categories(self):
        return self.blog.metadata.get("categories", [])

    @property
    def guid(self):
        return self.blog.metadata.get("guid")

    @guid.setter
    def guid(self, new_guid):
        self.blog.metadata["guid"] = new_guid

    @property
    def date(self) -> datetime:
        return self.blog.metadata.get("date")

    @property
    def banner_path(self) -> Optional[Path]:
        path = Path(self.dir).joinpath(Path(self.image))
        return path

    @property
    def og_banner_path(self) -> Optional[Path]:
        path = Path(self.dir).joinpath(self.og_image)
        if "image" in self.og_image:
            if not path.exists():
                raise ValueError(f"og.image {path} does not exist")
        return path

    @property
    def banner(self) -> Optional[Image.Image]:
        path = self.banner_path
        return Image.open(path) if path.exists() else None

    @property
    def og_banner(self) -> Optional[Image.Image]:
        path = self.og_banner_path
        return Image.open(path) if path.exists() else None

    def generate_og_banner(self):
        in_file = self.banner_path
        out_file = self.og.get("image", os.path.join("images", "og-banner.jpg"))
        logging.info("generating new image in %s", out_file)
        blog = ImageGeneratorBlog(self.title, self.subtitle, self.author)
        generate_og_image(
            blog, in_file, out_file, resize=True, overwrite=True, gradient_magnitude=0.9
        )

    @property
    def rendered(self):
        def replace_references(match: re.Match):
            image = self.uploaded_images.get(match.group("url"))
            if image:
                return f"![{match.group('alt_text')}]({image.url})"
            return match.group(0)

        content = self.markdown_image_pattern.sub(replace_references, self.content)
        return markdown(content, extensions=["fenced_code", "codehilite"])

    @property
    def local_image_references(self) -> set[str]:
        return set(
            map(
                lambda u: u.path,
                filter(
                    lambda u: u.scheme in ["", "file"],
                    map(
                        lambda u: urlparse(u),
                        map(
                            lambda m: m.group("url"),
                            re.finditer(self.markdown_image_pattern, self.content),
                        ),
                    ),
                ),
            )
        )

    def upload_local_images(self, wp: Wordpress):
        self.uploaded_images = {}
        for filename in self.local_image_references:
            path = Path(self.dir).joinpath(filename)
            if not path.exists():
                logging.warning("%s does not exist", path)
                continue

            image = Image.open(path)
            slug = (
                self.slug
                + "-"
                + re.sub(r"[/\.\\]+", "-", Path(filename).stem).strip("-")
            )
            self.uploaded_images[filename] = wp.upload_media(slug, image)

    def to_wordpress(self, wp: Wordpress) -> dict:
        author = wp.get_unique_user_by_name(self.author)
        self.upload_local_images(wp)
        result = {
            "title": self.title,
            "slug": self.slug,
            "author": author.id,
            "date": self.date.isoformat(),
            "date_gmt": self.date.astimezone(pytz.UTC).isoformat(),
            "content": self.rendered,
            "format": "standard",
            "status": self.status,
            "author": author.id,
            "categories": [wp.categories[c] for c in self.categories],
        }
        if self.og.get("description"):
            result["excerpt"] = self.og.get("description")
        return result


def upsert_post(wp: Wordpress, blog: Blog) -> int:

    if blog.guid:
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
                "a post with the same slug already exists, %a", existing_post.guid
            )
            return 1

        post = wp.create_post(blog.to_wordpress(wp))
        blog.guid = post.guid
        blog.save()
        logging.info("uploaded blog '%s' as post %s", blog.title, post.link)

    banner = wp.upload_media(f"{blog.slug}-image", blog.banner)
    if post.featured_media != banner.medium_id:
        logging.info("updated featured image of as %s", post.guid)
        wp.update_post(blog.guid, {"featured_media": banner.medium_id})

    if blog.og_banner:
        og_banner = wp.upload_media(f"{blog.slug}-og-image", blog.og_banner)
        wp.update_post(
            blog.guid,
            {
                "meta": {
                    "yoast_wpseo_opengraph-image": og_banner.medium_id,
                }
            },
        )

    return 0
