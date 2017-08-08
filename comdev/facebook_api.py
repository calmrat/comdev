#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Notes:
    Timeformat: 2013-01-25T00:11:02+0000
"""

import ipdb  # ipdb.set_trace()  # NOQA
import logging
import requests

from facepy import GraphAPI

# Setup console logging
log = logging.getLogger(__name__)


def get_token(client_id, client_secret, client_access_token, page=None):
    """
    See: http://nodotcom.org/python-facebook-tutorial.html
    """
    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    }

    if client_access_token:
        payload['grant_type'] = 'fb_exchange_token'
        payload['fb_exchange_token'] = client_access_token

    # response {"access_token":" ... ", "token_type":"bearer", "expires_in":..}
    response = requests.post(
        'https://graph.facebook.com/oauth/access_token?',
        params=payload)
    access_token = response.json()['access_token']
    return access_token


def get_page_api(client_access_token, page_id):
    """
    You can also skip the above if you get a page token:
    http://stackoverflow.com/questions/8231877
    and make that long-lived token as in Step 3
    """
    graph = GraphAPI(client_access_token)
    # Get page token to post as the page. You can skip
    # the following if you want to post as yourself.
    resp = graph.get('me/accounts')
    page_access_token = None

    for page in resp['data']:
        if page['id'] == page_id:
            page_access_token = page['access_token']
            break

    return GraphAPI(page_access_token)


def wall_post():
    """
    https://developers.facebook.com/docs/graph-api/reference/v2.9/page/feed
    """
    pass


if __name__ == '__main__':
    ipdb.set_trace()
