import logging
import os
import click
from wordpress_markdown_blog_loader import (
    upload,
    download,
    new,
    update_canonical,
    change_guid,
    add_email,
    regenerate_og_images
)


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


posts.add_command(upload.command)
posts.add_command(download.command)
posts.add_command(new.command)
posts.add_command(new.update_banner_command)
posts.add_command(update_canonical.command)
posts.add_command(change_guid.command)
posts.add_command(add_email.command)
posts.add_command(regenerate_og_images.command)


if __name__ == "__main__":
    main()
