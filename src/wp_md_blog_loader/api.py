import configparser
import hashlib
import logging
import os.path
import re
from io import BytesIO
from os.path import expanduser
from pathlib import Path
from typing import List, Dict
from typing import Optional
from urllib.parse import urlparse

import requests
from PIL import Image


class WordpressEndpoint:
    def __init__(self, **kwargs):
        self.host = None
        self.api_host = None
        self.url = None
        self.username = None
        self.password = None
        for key in self.__dict__.keys():
            self.__setattr__(key, kwargs[key] if key in kwargs else None)

    def read_from_config(self, host: str):
        config = configparser.ConfigParser()
        config.read(expanduser("~/.wordpress.ini"))

        self.host = host if host else config.defaults().get("host")
        assert host, "no host specified and no default host found"

        self.api_host = config.get(host, "api_host", fallback=self.host)
        self.url = f"https://{self.api_host}/wp-json/wp/v2"
        self.username = config.get(host, "username")
        self.password = config.get(host, "password")

    def normalize_url(self, url: str) -> str:
        """
        >>> WordpressEndpoint(host="binx.io", api_host="binx.wpengine.com").normalize_url("https://binx.io/bla")
        'https://binx.wpengine.com/bla'
        >>> WordpressEndpoint(host="binx.io", api_host="binx.wpengine.com").normalize_url("https://xebia.com/bla")
        'https://xebia.com/bla'
        >>> WordpressEndpoint(host="binx.io", api_host="binx.wpengine.com").normalize_url("https://binx.io:443/bla")
        'https://binx.wpengine.com:443/bla'
        """
        if self.host == self.api_host:
            return url

        parsed_url = urlparse(url)
        if parsed_url.hostname == self.host:
            return parsed_url._replace(
                netloc=parsed_url.netloc.replace(self.host, self.api_host)
            ).geturl()

        return url

    @staticmethod
    def load(host: str = None) -> "WordpressEndpoint":
        result = WordpressEndpoint()
        result.read_from_config(host)
        return result


class Wordpress(object):
    def __init__(self, host: Optional[str] = None):
        self.endpoint = WordpressEndpoint.load(host)

        self._media: Dict[str, dict] = {}
        self._categories: Dict[str, int] = {}
        self.headers = {
            "accept": "application/json",
            "User-Agent": "Wordpress markdown blog loader - Python",
        }
        self.session = requests.Session()

    @property
    def auth(self) -> (str, str):
        return (self.endpoint.username, self.endpoint.password)

    @property
    def url(self) -> str:
        return self.endpoint.url

    def normalize_url(self, url: str) -> str:
        return self.endpoint.normalize_url(url)

    def get_all(self, resource: str, query: dict = None) -> List[dict]:
        result = []
        params = query.copy() if query else {}
        params["per_page"] = "50"
        page = 1
        total_pages = 1
        while page <= total_pages:
            params["page"] = str(page)
            response = self.session.get(
                f"{self.url}/{resource}",
                auth=self.auth,
                params=params,
                headers=self.headers,
            )
            if response.status_code == 200:
                result.extend(response.json())
                total_pages = int(response.headers["X-WP-TotalPages"])
                page = page + 1
            else:
                print(f"failed to get all {resource}: {response.text}")
                exit(1)

        return result

    def users(self, query: dict = None) -> List["User"]:
        return list(map(lambda u: User(u), self.get_all("users", query)))

    def get_unique_user_by_name(self, name: str) -> "User":
        users = self.users({"search": name})
        if len(users) == 0:
            raise ValueError("author %s not found as user of %s", name, self.host)
        elif len(users) > 1:
            raise ValueError(
                "author name '%s' results in multiple matches in %s", name, self.host
            )
        return users[0]

    def posts(self, query: dict = None) -> List["Post"]:
        return list(map(lambda u: Post(u), self.get_all("posts", query)))

    def get_post_by_slug(self, slug: str) -> Optional["Post"]:
        return next(
            filter(
                lambda p: p.slug == slug,
                (
                    map(
                        lambda u: Post(u),
                        self.get_all(
                            "posts", {"status": "draft,publish,pending", "slug": slug}
                        ),
                    )
                ),
            ),
            None,
        )

    @property
    def media(self) -> List["Medium"]:
        if not self._media:
            self._media = {m["slug"]: Medium(m) for m in self.get_all("media")}
        return self._media

    @property
    def categories(self) -> Dict[str, int]:
        if not self._categories:
            self._categories = {c["slug"]: c["id"] for c in self.get_all("categories")}
        return self._categories

    def search_for_image_by_slug(self, slug) -> Optional["Medium"]:
        response = self.session.get(
            f"{self.url}/media",
            auth=self.auth,
            headers=self.headers,
            params={"search": slug},
        )
        if response.status_code == 200:
            matches = map(lambda i: Medium(i), response.json())
            return next(filter(lambda i: slug in [i.slug, i.title], matches), None)
        else:
            return None

    def upload_media(self, slug: str, image: Image) -> "Medium":
        old_content = []

        stream = BytesIO()
        image.save(stream, format=image.format)
        content = stream.getvalue()

        stored_image = self.search_for_image_by_slug(slug)
        if stored_image:
            response = self.session.get(stored_image.url, stream=True, auth=self.auth)
            assert response.status_code == 200
            old_content = response.content

        if old_content != content:
            if stored_image:
                logging.info(
                    "force delete existing image under slug %s, id %s",
                    slug,
                    stored_image.medium_id,
                )
                delete_response = self.session.delete(
                    f"{self.url}/media/{stored_image.medium_id}",
                    auth=self.auth,
                    headers=self.headers,
                    params={"force": 1},
                )
                if delete_response.status_code not in [200, 201, 202]:
                    raise Exception(response.text)

            filename = f"{slug}.{image.format.lower()}"
            print(f"INFO: uploading image as {filename}")

            headers = self.headers | {
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": Image.MIME[image.format],
            }

            response = self.session.post(
                f"{self.url}/media/",
                data=content,
                auth=self.auth,
                headers=headers,
                params={
                    "slug": slug,
                    "title": slug,
                },
            )
            if response.status_code not in [200, 201]:
                raise Exception(response.text)

            stored_image = Medium(response.json())
            self.session.patch(
                f"{self.url}/media/{stored_image.medium_id}",
            )

        self._media[slug] = stored_image
        return self._media[slug]

    def update_post(self, guid: str, properties: dict):
        response = self.session.patch(
            self.normalize_url(guid),
            json=properties,
            auth=self.auth,
            headers=self.headers,
        )
        if response.status_code not in [200, 201]:
            raise Exception(response.text)
        return Post(response.json())

    def create_post(self, properties: dict) -> "Post":
        response = self.session.post(
            f"{self.url}/posts",
            json=properties,
            auth=self.auth,
            headers=self.headers,
        )
        if response.status_code not in [200, 201]:
            raise Exception(response.text)
        return Post(response.json())

    def get_resource_by_url(self, url: str) -> Optional[dict]:
        response = self.session.get(
            self.normalize_url(url), auth=self.auth, headers=self.headers
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            raise Exception(response.text)

    def get(self, resource, resource_id) -> Optional[dict]:
        return self.get_resource_by_url(
            f"{self.url}/{resource}/{resource_id}", headers=self.headers, auth=self.auth
        )

    def connect(self):
        global categories

        categories = {c["slug"]: c["id"] for c in self.get_all("categories")}


class User(dict):
    def __init__(self, u):
        self.update(u)

    @property
    def name(self):
        return self.get("name")

    @property
    def id(self):
        return self.get("id")


class Medium(dict):
    def __init__(self, properties: dict):
        self.update(properties)

    @property
    def medium_id(self):
        return int(self["id"])

    @property
    def url(self) -> str:
        return self.get("guid").get("rendered")

    @property
    def slug(self) -> str:
        return self.get("slug")

    @property
    def title(self) -> Optional[str]:
        return self.get("title", {}).get("rendered")


class Post(dict):
    def __init__(self, p):
        self.update(p)

    @property
    def slug(self):
        return self["slug"]

    @property
    def post_id(self) -> id:
        return int(self["id"])

    @property
    def link(self):
        return self["link"]

    @property
    def guid(self) -> str:
        return self["_links"]["self"][0]["href"]

    @property
    def title(self):
        r = self["title"]["rendered"]
        return r.replace("&#8211;", "-")

    @property
    def featured_media(self) -> Optional[int]:
        return self.get("featured_media")

    @featured_media.setter
    def featured_media(self, medium_id: int):
        self["featured_media"] = medium_id
