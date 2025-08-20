import configparser
import json
import logging
import mimetypes
import os
import re
import sys
from datetime import datetime
from functools import cache
from os.path import expanduser
from pathlib import Path
from typing import List, Dict, Iterator
from typing import Optional, Union
from urllib.parse import urlparse, ParseResult

import pytz
import requests


def get_default_host() -> Optional[str]:
    """
    returns the default api host from .wordpress.ini and/or ~/.wordpress.ini
    """
    config = configparser.ConfigParser()
    config.read([".wordpress.ini", expanduser("~/.wordpress.ini")])
    return config.defaults().get("host")


def get_password(host: str) -> Optional[str]:
    """
    Returns a password from the environment variable for the specified host.

    The default environment variable is WP_APP_PASSWORD. A password for a specific host can be
    specified by setting an environment variable WP_APP_PASSWORD_<host> where
    the host name is all uppercase and non characters and digits replaced with _.

    If not set, None is returned.

    >>> os.environ["WP_APP_PASSWORD_XEBIA_COM"] = "host_password"
    >>> get_password('xebia.com')
    'host_password'
    >>> get_password('binx.io') is None
    True
    >>> os.environ["WP_APP_PASSWORD"] = "default_password"
    >>> get_password('binx.io')
    'default_password'
    """
    h = re.sub(r"[^a-zA-Z-0-9]", "_", host).upper()
    if result := os.getenv(f"WP_APP_PASSWORD_{h}"):
        return result

    return os.getenv("WP_APP_PASSWORD")


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
        config.read([".wordpress.ini", expanduser("~/.wordpress.ini")])

        if not host:
            host = config.defaults().get("host")
            assert host, "no host specified and no default host found"

        self.host = host
        self.api_host = config.get(host, "api_host", fallback=self.host)
        self.url = f"https://{self.api_host}/wp-json/wp/v2"

        self.username = config.get(host, "username")
        self.password = get_password(host)
        if not self.password:
            logging.warning(
                "taking plain text app password from configuration file, use WP_APP_PASSWORD environment variable instead!"
            )
            self.password = config.get(host, "password")

    def is_host_for(self, url: Union[str, ParseResult]) -> bool:
        result = url if isinstance(url, ParseResult) else urlparse(url)
        return result.hostname in [self.host, self.api_host]

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


class User(dict):
    def __init__(self, u):
        self.update(u)

    @property
    def name(self):
        return self.get("name")

    @property
    def id(self):
        return self.get("id")

    @property
    def email(self):
        return self.get("email")

    @property
    def slug(self):
        return self.get("slug")


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
    def link(self) -> str:
        return self["link"]

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
        return self["slug"] if self["slug"] else self.get("generated_slug")

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

    @property
    def content(self) -> Optional[str]:
        return self.get("content", {}).get("rendered")

    @property
    def raw_content(self) -> Optional[str]:
        return self.get("content", {}).get("raw")

    @property
    def categories(self) -> list[id]:
        return self.get("categories", [])

    @property
    def industries_taxonomy(self) -> list[id]:
        return self.get("industries_taxonomy", [])

    @property
    def partners_taxonomy(self) -> list[id]:
        return self.get("partners_taxonomy", [])

    @property
    def capabilities(self) -> list[id]:
        return self.get("capabilities", [])

    @property
    def tags(self) -> list[int]:
        return self.get("tags", [])

    @property
    def author(self) -> int:
        return self["author"]

    @property
    def excerpt(self) -> Optional[str]:
        return self.get("excerpt", {}).get("rendered")

    @excerpt.setter
    def excerpt(self, exerpt):
        self["excerpt"] = exerpt

    @property
    def date(self) -> datetime:
        return (
            pytz.timezone("utc")
            .localize(datetime.fromisoformat(self.get("date_gmt")))
            .astimezone()
        )

    @date.setter
    def date(self, new_date: datetime):
        self["date"] = new_date
        self["date_gmt"] = new_date.astimezone(pytz.timezone("utc"))

    @property
    def status(self):
        return self["status"]

    @status.setter
    def status(self, new_status):
        self["status"] = new_status

    @property
    def og_images(self) -> list[ParseResult]:
        """
        returns urls to the og:image links
        """
        result = []
        for name in ["rank_math_twitter_image", "rank_math_facebook_image"]:
            if image := self.get("meta", {}).get(name):
                result.append(urlparse(image))
        return result

    @property
    def og_description(self) -> Optional[str]:
        return self.get("meta", {}).get("rank_math_facebook_description")

    @property
    def permalink_template(self) -> Optional[str]:
        return self.get("permalink_template")

    @permalink_template.setter
    def permalink_template(self, template: str):
        self["permalink_template"] = template


class PermissionDenied(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class Wordpress(object):
    def __init__(self, host: Optional[str] = None):
        self.endpoint = WordpressEndpoint.load(host)

        self._media: List[Medium] = {}
        self.headers = {
            "accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
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

    def is_host_for(self, url: Union[str, ParseResult]) -> bool:
        return self.endpoint.is_host_for(url)

    def get_all(self, resource: str, query: dict = None) -> Iterator[dict]:
        params = query.copy() if query else {}
        params["per_page"] = "100"
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
                for object in response.json():
                    yield object
                total_pages = int(response.headers["X-WP-TotalPages"])
                page = page + 1
            else:
                msg = f"failed to get all {resource}: {response.status_code}, {response.text}"
                if response.status_code in [401, 403]:
                    raise PermissionDenied(msg)
                else:
                    print(msg)
                    exit(1)

        return None

    def users(self, query: dict = None) -> List["User"]:
        return list(map(lambda u: User(u), self.get_all("users", query)))

    def get_user_by_id(self, resource_id: int) -> "User":
        return User(self.get("users", resource_id))

    def get_unique_user_by_name(
        self, name: str, email: Optional[str], author_id: Optional[str]
    ) -> "User":

        user = self.get_user_by_id("me")
        if user and user.name == name:
            return user

        users = []
        try:
            # The email field is only returned when the context edit is passed.
            # See: https://developer.wordpress.org/rest-api/reference/users/
            users = self.users({"search": name, "context": "edit"})
        except PermissionDenied as error:
            logging.warning("Permission denied to read user email addresses")
            users = self.users({"search": name})

        if len(users) == 0:
            raise ValueError(f"author '{name}' not found on {self.endpoint.host}")
        elif len(users) == 1:
            return users[0]

        if user := next(
            filter(
                lambda u: (author_id and u.slug == author_id)
                or (
                    not author_id
                    and email
                    and u.email
                    and u.email.lower() == email.lower()
                ),
                users,
            ),
            None,
        ):
            return user

        candidates = ", ".join(["{} / {}".format(u.slug, u.email) for u in users])
        if author_id:
            raise ValueError(
                f"Multiple authors named '{name}' found, none with author id {author_id} (possible: {candidates})."
            )
        elif email:
            raise ValueError(
                f"Multiple authors named '{name}' found, but none with email {email}. (possible: {candidates})."
            )
        else:
            raise ValueError(
                f"Multiple authors named '{name}' found. (possible: {candidates})."
            )

    def posts(self, query: dict = None) -> Iterator["Post"]:
        for p in self.get_all("posts", query):
            yield Post(p)

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

    def media(self) -> List[Medium]:
        if not self._media:
            self._media = [Medium(m) for m in self.get_all("media")]
        return self._media

    @property
    @cache
    def categories(self) -> Dict[str, int]:
        return {c["slug"]: c["id"] for c in self.get_all("categories")}

    @property
    @cache
    def categories_by_id(self) -> Dict[int, str]:
        return {id: slug for slug, id in self.categories.items()}

    @property
    @cache
    def industries_taxonomy(self) -> Dict[str, int]:
        return {c["slug"]: c["id"] for c in self.get_all("industries_taxonomy")}

    @property
    @cache
    def industries_taxonomy_by_id(self) -> Dict[str, int]:
        return  {id: slug for slug, id in self.industries_taxonomy.items()}

    @property
    @cache
    def partners_taxonomy(self) -> Dict[str, int]:
        return {c["slug"]: c["id"] for c in self.get_all("partners_taxonomy")}

    @property
    @cache
    def partners_taxonomy_by_id(self) -> Dict[str, int]:
        return  {id: slug for slug, id in self.partners_taxonomy.items()}

    @property
    @cache
    def capabilities(self) -> Dict[str, int]:
        return {c["slug"]: c["id"] for c in self.get_all("capabilities")}

    @property
    @cache
    def capabilities_by_id(self) -> Dict[str, int]:
        return  {id: slug for slug, id in self.capabilities.items()}


    @property
    @cache
    def tags(self) -> Dict[str, int]:
        return {c["slug"]: c["id"] for c in self.get_all("tags")}

    @property
    @cache
    def tags_by_id(self) -> Dict[int, str]:
        return {id: slug for slug, id in self.tags.items()}

    def search_for_image_by_slug(self, slug) -> Optional[Medium]:
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

    def get_media(self, url: str) -> bytes:
        response = self.session.get(
            url, headers=self.headers, stream=True, auth=self.auth
        )
        assert response.status_code == 200, f"status code {response.status_code}"
        return response.content

    def upload_media(self, slug: str, path: Path) -> Medium:
        old_content = []

        with open(path, "rb") as file:
            content = file.read()

        stored_image = self.search_for_image_by_slug(slug)
        if stored_image:
            response = self.session.get(
                stored_image.url,
                headers={"User-Agent": self.headers["User-Agent"]},
                stream=True,
                auth=self.auth,
            )
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
                    raise Exception(delete_response.text)

            filename = f"{slug}{path.suffix}"
            print(f"INFO: uploading image as {filename}")

            headers = self.headers | {
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": mimetypes.guess_type(path)[0],
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

    def find_image_by_link(self, link: Union[str, ParseResult]) -> Optional[Medium]:
        url = link if isinstance(link, ParseResult) else urlparse(link)
        stem = Path(url.path).stem

        if not (self.is_host_for(link) and url.path.startswith("/wp-content/uploads/")):
            return None

        return next(
            filter(
                lambda m: url.geturl() == m.url,
                map(lambda m: Medium(m), self.get_all("media", {"search": stem})),
            ),
            None,
        )

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

    def get_resource_by_url(self, url: str, params: dict = {}) -> Optional[dict]:
        response = self.session.get(
            self.normalize_url(url), auth=self.auth, headers=self.headers, params=params
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            raise Exception(response.text)

    def get(self, resource, resource_id, params: dict = {}) -> Optional[dict]:
        return self.get_resource_by_url(f"{self.url}/{resource}/{resource_id}", params)

    def connect(self):
        global categories

        categories = {c["slug"]: c["id"] for c in self.get_all("categories")}

    def get_category_id_by_name(self, category: str) -> str:
        if category in self.categories:
            return self.categories[category]

        raise ValueError(
            "invalid category '{}' try one of\n {}".format(
                category, ",\n ".join(self.categories.keys())
            )
        )

    def get_industry_by_name(self, slug: str) -> str:
        if slug in self.industries_taxonomy:
            return self.industries_taxonomy[slug]

        raise ValueError(
            "invalid industry '{}' try one of\n {}".format(
                slug, ",\n ".join(self.industries_taxonomy.keys())
            )
        )

    def get_partner_by_name(self, slug: str) -> str:
        if slug in self.partners_taxonomy:
            return self.partners_taxonomy[slug]

        raise ValueError(
            "invalid partner '{}' try one of\n {}".format(
                slug, ",\n ".join(self.partners_taxonomy.keys())
            )
        )

    def get_capabilities_by_name(self, slug: str) -> str:
        if slug in self.capabilities:
            return self.capabilities[slug]

        raise ValueError(
            "invalid capability '{}' try one of\n {}".format(
                slug, ",\n ".join(self.capabilities.keys())
            )
        )


    def get_tag_id_by_name(self, tag: str) -> str:
        if tag in self.tags:
            return self.tags[tag]

        raise ValueError(
            "invalid tag '{}' try one of\n {}".format(
                tag, ",\n ".join(self.tags.keys())
            )
        )
