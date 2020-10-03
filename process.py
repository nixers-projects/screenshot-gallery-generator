#!/usr/bin/env python3
"""
What this does:
    1. Downloads HTML from list of URLs.
    2. Parses HTML to find img/a tags containing rel="nix".
    3. Create a page for each user from the user template.
    4. Create an index page from the index template.

Usage:
    python process.py -l /../screenshot_galleries.list -o /../output/ -t /../templates/

"""

import argparse
import shutil
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
    output = Path(output)
    output.mkdir(exist_ok=True)
    shutil.copy(Path(templates) / "style.css", output / 'style.css')
    everything = {}
    parser = PageParser()
    templates = Environment(loader=FileSystemLoader(templates))

    # render individual user pages
    user_template = templates.get_template('user.html')

    for user, site in sites.items():
        with urllib.request.urlopen(site) as f:
            html = f.read().decode('utf-8')
        parser.feed(html)

        address = urlparse(site)
        base_url = "{}://{}".format(address.scheme, address.netloc)
        user_images = []

        for url in parser.urls:
            path = urlparse(url).path
            if path.startswith('/'):
                image_url = urljoin(base_url, url)
            else:
                image_url = base_url + urljoin(address.path, path)
            user_images.append(image_url)

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
        if tag in ('img', 'a'):
            attrs = dict(attrs)
            if attrs.get('rel', '') == TAG and 'src' in attrs:
                self.urls.append(attrs['src'])
            if attrs.get('rel', '') == TAG and 'href' in attrs:
                self.urls.append(attrs['href'])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-l', '--list', nargs='?',
        help='File containing list of users and gallery URLs',
        default='screenshot_galleries.list',
        type=str,
    )

    parser.add_argument(
        '-o', '--output', nargs='?',
        help='Folder to output generate HTML files into.',
        default='output',
        type=str,
    )

    parser.add_argument(
        '-t', '--templates', nargs='?',
        help='Folder containing HTML templates.',
        default='templates',
        type=str,
    )
    args = parser.parse_args()

    scrape_sites(get_sites(args.list), args.templates, args.output)
