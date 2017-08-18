#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Chris Ward <cward@redhat.com>

import ipdb  # NOQA
import logging
import os

from ldap3 import Server, Connection, ALL
import pandas as pd

from comdev import __app__
from comdev.lib import load_config, expand_path, load_yaml


class LDAPer(object):
    attrs_user = None

    def __init__(self, app_name, merge_path=None):
        self.app_name = app_name
        self.merge_path = merge_path

        config = load_config(app_name)
        paths = {k: expand_path(x) for k, x in config['paths'].get().items()}

        config = self.config = config['ldap'].get()

        self.base_query = config['base_query']
        self.path_cache = paths['cache']
        self.path_pickle = os.path.join(self.path_cache, 'ldap.pickle')

    def _get_api(self):
        uri = self.config['uri']
        user = self.config['user']
        password = self.config['password']
        server = Server(uri, get_info=ALL, use_ssl=True)
        api = Connection(server, user=user, password=password)
        api.bind()
        return api

    def get_users(self, sync=False):
        if sync:
            self.sync_users()
        is_cached = os.path.isfile(self.path_pickle)
        if is_cached:
            # load local cache, otherwise fail and tell user to sync first
            df = pd.read_pickle(self.path_pickle)
        else:
            raise RuntimeError("Run 'sync' command first")
        return df

    def sync_users(self):
        log.info('Syncing LDAP user data')
        merge_path = self.merge_path
        entries = self.query_users()
        # extract out all the users data as list of dicts
        users = [user.entry_attributes_as_dict for user in entries]
        # dump it all into a dataframe
        df = pd.DataFrame(users)
        df.index = df['uid']
        # assumes index <-> index join
        if merge_path:
            defaults = load_yaml(merge_path)
            df = df.join(defaults, rsuffix='_local')
        # sync cache locally
        df.to_pickle(self.path_pickle)
        return df

    def query_users(self, query=None, attrs=None,
                    obj_class='(objectclass=person)', as_df=False):
        log.debug('LDAP search START')
        attrs = attrs or self.attrs_user
        api = self._get_api()
        base_query = self.base_query if self.base_query else ''
        query = ','.join((query, base_query)) if query else base_query
        attrs = attrs.keys() if isinstance(attrs, dict) else attrs
        api.search(query, obj_class, attributes=attrs)
        entries = api.entries
        log.debug(' ... found {} entries'.format(len(entries)))
        if as_df:
            df = pd.DataFrame()
            for entry in entries:
                series = pd.Series(entry.entry_attributes_as_dict)
                entries = pd.concat([df, series])
        log.debug('LDAP search END')
        return entries

    def find_uids(self, uids, live):
        if live:
            users = self.query_users(
                'uid={}'.format('|'.join(uids)), as_df=True)
        else:
            # FIXME: this should work through query_users... one search ui
            users = self.get_users()
            users = users[users.index.isin(uids)]
        return users


# Setup console logging
log = logging.getLogger(__app__)


if __name__ == '__main__':
    ipdb.set_trace()
