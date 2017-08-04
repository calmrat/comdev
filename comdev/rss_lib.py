#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

import click
import feedparser
import ipdb  # NOQA

from airlib import dt_normalize, sluggify

# Setup console logging
log = logging.getLogger(__name__)


def load_feed(url):
    data = feedparser.parse(url)
    return data


@click.group()
@click.option('--quiet', '-q', is_flag=True, default=False)
@click.option('--debug', '-d', is_flag=True, default=False)
@click.pass_context
def cli(ctx, quiet, debug):
    if quiet:
        log.setLevel(logging.WARN)
    elif debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)


@cli.command('scrape')
@click.argument('url', type=str)
@click.pass_context
def scrape(ctx, url):
    """
    Rip the events from a given rss feed, normalize the data and store.
    """
    data = load_feed(url)

    feed = data['feed']
    entries = data['entries']

    # THIS IS SPECIFIC TO # http://konfery.cz/rss/

    _type = 'community'
    country = 'Czech Republic'
    # title, title_detail, links, link, published, summary, tags
    # unused: summary_detail, guidislink, published_parsed
    for entry in entries:
        _id = sluggify(entry['id'])
        city = entry['tags'][0]['term']
        landing = entry['link']
        start_time = dt_normalize(entry['published_parsed'], local_tz=True)
        title = entry['title']
        summary = entry['summary']
        link = entry['link']

        ipdb.set_trace()


if __name__ == '__main__':
    ipdb.set_trace()
