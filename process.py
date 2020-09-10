#!/usr/bin/env python3
#
# 1. Download HTML from list of URLs.
# 2. Parse HTML to find img tags containing rel="nix".
# 3. Download tagged images into output folder.
# TODO: compare output folder to tag list; remove local images not found in html.
# 4. Create user page from user template.
# 5. Create index page from index template.

import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

from jinja2 import Environment, FileSystemLoader

SRC = Path('templates')
OUT = Path('output')
URLS = Path('screenshot_galleries.list')
TAG = 'nix'


class PageParser(HTMLParser):
    def reset(self):
        HTMLParser.reset(self)
        self.urls = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            attrs = dict(attrs)
            if attrs.get('rel', '') == TAG and 'src' in attrs:
                self.urls.append(attrs['src'])


def get_sites():
    with open(URLS, 'r') as f:
        lines = f.read().split('\n')

    sites = {}
    for line in lines[:-1]:
        user, url = line.split(' ')
        sites[user] = url.strip()

    return sites


def main():
    sites = get_sites()
    templates = Environment(loader=FileSystemLoader(SRC))
    parser = PageParser()
    OUT.mkdir(exist_ok=True)
    everything = {}

    # render individual user pages
    user_template = templates.get_template('user.html')

    for user, site in sites.items():
        with urllib.request.urlopen(site) as f:
            html = f.read().decode('utf-8')
        parser.feed(html)

        address = urlparse(site)
        cache = OUT / address.netloc
        cache.mkdir(exist_ok=True)
        base_url = "{}://{}".format(address.scheme, address.netloc)
        user_images = []

        for i, url in enumerate(parser.urls):
            image = str(i).zfill(3) + urlparse(url).path.replace('/', '.')
            image_full = cache / image
            user_images.append(image)
            if not image_full.exists():
                full_url = urljoin(base_url, url)
                urllib.request.urlretrieve(full_url, image_full)

        if user_images:
            parser.reset()
            everything[user] = user_images
            with open(OUT / '{}.html'.format(user), 'w') as f:
                f.write(user_template.render(user=user, images=user_images))

    # render index page
    index_template = templates.get_template('index.html')
    with open(OUT / 'index.html', 'w') as f:
        f.write(index_template.render(everything=everything))


if __name__ == "__main__":
    main()
