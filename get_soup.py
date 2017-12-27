#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This script downloads as much of a soup.io page as you want. Either by giving
a limit or because the soup is done.
This works for all soups that I look at, I have no idea if other soups have different HTML.

Usage: get_soup.py [OPTIONS]

Options:
  --limit INTEGER  How many pages to get.
  --baseurl TEXT   Start page of soup to get.
  --stoppage TEXT  Stop at this page url
  --filetype TEXT  Limit download to this file type.
  --help           Show this message and exit.
"""

import HTMLParser
import click
import os.path
import requests
import shutil
import sys


def _clean_url(url, extension):
    if not extension:
        extension = '.' + url.split('.')[-1]
    url = url.split('?')[0]
    if url.count('_') == 2:
        url = '_'.join(url.split('_')[:2]) + extension
    return url


def _download_picture(url, extension):
    if url.count('-square') > 0:
        return
    url = _clean_url(url, extension)
    file_name = url.split('/')[-1]
    if os.path.isfile(file_name):
        return
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        print r.status_code, "status code is wrong for", url
    with open(file_name, 'wb') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)


class MyHTMLParser(HTMLParser.HTMLParser):

    _imagecontainer_open = False
    next_url = None
    _stop_page = None
    _file_type = None

    def __init__(self, stop_page, file_type):
        self._stop_page = stop_page
        self._file_type = file_type
        HTMLParser.HTMLParser.__init__(self)

    def handle_data(self, data):
        if 'SOUP.Endless.next_url' in data:
            u = data.split('=')[1].replace("'", "").strip()
            if self.next_url == u:
                print "reached end of soup"
                sys.exit(0)
            if u.startswith(self._stop_page):
                print "Reached stop page ", self._stop_page
                sys.exit(0)
            self.next_url = u

    def handle_starttag(self, tag, attrs):
        if self._imagecontainer_open:
            for attribute in attrs:
                if attribute[0] == 'src' and (
                    (self._file_type and attribute[1].endswith(self._file_type)) or
                    not self._file_type):
                    _download_picture(attribute[1], self._file_type)
                    self._imagecontainer_open = False
        else:
            if ('class', 'imagecontainer') in attrs:
                self._imagecontainer_open = True


class Soup(object):
    _base_url = None
    max_page_count = None

    def __init__(self, url, max_page_count):
        self._base_url = url
        self._max_page_count = max_page_count


    def walk(self, stop_page, extension):
        url = self._base_url
        parser = MyHTMLParser(stop_page, extension)
        page_count = 0
        while page_count < self._max_page_count:
            page_count += 1
            print "getting", url
            response = requests.get(url)
            if response.status_code != 200:
                print "wrong status", response.status, " on ", url
                raise AssertionError()
            body = response.text
            parser.feed(body)
            url = self._base_url + parser.next_url
            parser.close()


@click.command()
@click.option('--limit', default=1, help='How many pages to get.')
@click.option('--baseurl', default=None, help='Start page of soup to get.')
@click.option('--stoppage', default=None, help='Stop at this page url')
@click.option('--filetype', default=None, help='Limit download to this file type.')
def run(limit, baseurl, stoppage, filetype):
    Soup(baseurl, limit).walk(stoppage, filetype)

if __name__ == '__main__':
    run()
