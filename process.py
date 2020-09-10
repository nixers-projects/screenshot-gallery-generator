#!/usr/bin/env python3
#
# 1. Download HTML from list of URLs.
# 2. Parse HTML to find img tags containing rel="nix".
# 3. Download tagged images into output folder.
# TODO: compare output folder to tag list; remove local images not found in html.
# 4. Create user page from user template.
# TODO: compare output folder to user list; remove users not found in list or with no images.
# 5. Create index page from index template.
#
# Usage:
#
# python process.py -l /../screenshot_galleries.list -o /../output/ -t /../templates/
#

import argparse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

from jinja2 import Environment, FileSystemLoader

TAG = 'nix'


def get_sites(list_file):
    with open(list_file, 'r') as f:
        lines = f.read().split('\n')

    sites = {}
    for line in lines[:-1]:
        user, url = line.split(' ')
        sites[user] = url.strip()

    return sites


def scrape_sites(sites, templates, output):
    templates = Environment(loader=FileSystemLoader(templates))
    parser = PageParser()
    output = Path(output)
    output.mkdir(exist_ok=True)
    everything = {}

    # render individual user pages
    user_template = templates.get_template('user.html')

    for user, site in sites.items():
        with urllib.request.urlopen(site) as f:
            html = f.read().decode('utf-8')
        parser.feed(html)

        address = urlparse(site)
        cache = output / address.netloc
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
            with open(output / '{}.html'.format(user), 'w') as f:
                f.write(user_template.render(user=user, images=user_images))

    # render index page
    index_template = templates.get_template('index.html')
    with open(output / 'index.html', 'w') as f:
        f.write(index_template.render(everything=everything))


class PageParser(HTMLParser):
    def reset(self):
        HTMLParser.reset(self)
        self.urls = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            attrs = dict(attrs)
            if attrs.get('rel', '') == TAG and 'src' in attrs:
                self.urls.append(attrs['src'])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-l', '--list', nargs=1,
        help='File containing list of users and gallery URLs',
        default='screenshot_galleries.list',
        type=str,
    )

    parser.add_argument(
        '-o', '--output', nargs=1,
        help='Folder to output generate HTML files into.',
        default='output',
        type=str,
    )

    parser.add_argument(
        '-t', '--templates', nargs=1,
        help='Folder containing HTML templates.',
        default='templates',
        type=str,
    )
    args = parser.parse_args()

    sites = get_sites(args.list)
    scrape_sites(sites, args.templates, args.output)
