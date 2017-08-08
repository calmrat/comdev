#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ipdb  # ipdb.set_trace()  # NOQA
import logging

import twitter

log = logging.getLogger(__name__)


def get_api(consumer_key, consumer_secret,
            access_token_key, access_token_secret):

    log.info('Authenticating Twitter API credentials')
    api = twitter.Api(consumer_key=consumer_key,
                      consumer_secret=consumer_secret,
                      access_token_key=access_token_key,
                      access_token_secret=access_token_secret)
    return api


if __name__ == '__main__':
    ipdb.set_trace()
