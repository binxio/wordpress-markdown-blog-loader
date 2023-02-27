import requests
from bs4 import BeautifulSoup


def check_links(content: str):
    """
    Checks a given URL for broken links in its HTML document.
    Returns a list of all broken links found.
    """
    soup = BeautifulSoup(content, "html.parser")

    broken_links = []
    for link in soup.find_all("a"):
        href = link.get("href")
        if href and href.startswith("http"):
            try:
                response = requests.get(href, headers={"User-Agent": "curl/7.86.0"})
                if response.status_code in [400, 404]:
                    broken_links.append((response.status_code, href))
            except requests.exceptions.RequestException:
                broken_links.append((-400, href))

    return broken_links


import logging

import click

from wordpress_markdown_blog_loader.api import Wordpress, Post


@click.command(name="check-links")
@click.option(
    "--host",
    type=str,
    required=True,
    nargs=1,
    help="wordpress host to check blog post links of",
)
@click.argument(
    "post-id",
    type=int,
    nargs=-1,
)
def command(host: str, post_id: tuple[str]):
    """
    check for broken links in WordPress posts
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
        broken_links = check_links(post.content)
        if broken_links:
            logging.error("post %s has %d broken links", post.link, len(broken_links))
            for link in broken_links:
                logging.error("  %s", link)
        else:
            logging.info("post %s has no broken links", post.link)
