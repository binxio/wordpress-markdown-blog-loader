import logging
import os
import click
from wordpress_markdown_blog_loader import upload, download, new


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


if __name__ == "__main__":
    main()
