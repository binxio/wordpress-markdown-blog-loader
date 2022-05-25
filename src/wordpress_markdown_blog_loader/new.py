import click
from urllib.request import urlopen
from urllib.parse import urlparse
from pathlib import Path
from slugify import slugify
from PIL import Image
from wordpress_markdown_blog_loader.blog import Blog
from datetime import datetime, timedelta
import logging
from io import BytesIO


class ImageType(click.ParamType):
    name = "image-url"

    def convert(self, value, param, ctx):
        try:
            url = urlparse(value)
            if url.netloc == "":
                url = urlparse(f"file://{value}")
            response = urlopen(url.geturl())
            content_type = response.headers.get("Content-Type")
            if not content_type.startswith("image/"):
                self.fail(f"{value} is not an image type, but a {content_type}")
                return

            bytes = response.read()
            return Image.open(BytesIO(bytes))
        except ValueError as error:
            self.fail("%s, cannot read image url" % value, param, ctx)


@click.command(name="new")
@click.option("--title", required=True, help="of the blog")
@click.option("--subtitle", required=True, help="of the blog")
@click.option("--author", required=True, help="of the blog")
@click.option("--image", required=False, type=ImageType(), help="for the banner")
def command(title, subtitle, author, image):
    """
    creates a select blog file
    """
    slug = slugify(title)

    directory = Path(slug)
    if directory.exists():
        raise click.UsageError(f'a directory with the name "{slug}" already exists')

    Path(slug).mkdir()
    blog = Blog()
    blog.dir = directory
    blog.path = directory.joinpath("index.md")
    blog.title = title
    blog.subtitle = subtitle
    blog.status = "draft"
    blog.slug = slug
    blog.og_description = "TODO: add short SEO description here"
    blog.date = (datetime.now().astimezone() + timedelta(days=7)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    if image:
        image_path = save_og_image(image, directory.joinpath("images/banner"))
        blog.image = image_path.relative_to(directory).as_posix()
    blog.save()


def save_og_image(image: Image, path: Path) -> Path:
    """
    save the image to be the perfect og image size: 1200x630px
    """
    width, height = image.size
    if width != 1200:
        new_height = int(height * 1200 / width)
        logging.info("resizing %dx%d to %dx%d", width, height, 1200, new_height)
        image = image.resize((1200, new_height))
        width = 1200
        width, height = image.size

    if height > 630:
        logging.info("cropping to maximum height of 630px")
        top = int((height - 630) / 2)
        bottom = 630 + top
        image = image.crop((0, top, 1200, bottom))
        width, height = image.size

    if height < 630:
        new_image = Image.new("RGBA", (1200, 630), (255, 0, 0, 0))
        new_image.paste(image, (0, int((630 - height) / 2)))
        image = new_image

    path.parent.mkdir(exist_ok=True, parents=True)

    path = path.with_suffix(".png" if image.mode == "RGBA" else ".jpg")
    with open(path, "wb") as file:
        image.save(file, **image.info)
    return path
