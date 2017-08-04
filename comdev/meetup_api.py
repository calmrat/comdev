#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
    Get your Meetup API key here:
    https://secure.meetup.com/meetup_api/key/
"""


import logging

import ipdb  # ipdb.set_trace()  # NOQA

import meetup.api

# Setup logging
log = logging.getLogger(__name__)


def get_api(api_key):
    return meetup.api.Client(api_key)


if __name__ == '__main__':
    ipdb.set_trace()
