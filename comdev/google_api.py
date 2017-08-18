#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Chris Ward <cward@redhat.com>

'''
API docs: https://developers.google.com/api-client-library/python/apis/
Drive:
 https://developers.google.com/resources/api-libraries/documentation/drive/v3/python/latest/drive_v3.files.html#create  #NOQA
'''

import logging
import os
import sys

from comdev.lib import load_config

import ipdb  # NOQA

import atom
import gdata.contacts.client
import gdata.contacts.data
import gdata.service
from gdata.gauth import OAuth2TokenFromCredentials
from googleapiclient import discovery
import oauth2client as o2c

# FIXME convert gmail to this?
# https://developers.google.com/resources/api-libraries/documentation/gmail/v1/python/latest/gmail_v1.users.messages.html#send   # NOQA


def get_credentials(app_name, path_credentials, client_secret, scopes):
    ''' '''
    from oauth2client.file import Storage
    store = Storage(path_credentials)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = o2c.client.flow_from_clientsecrets(client_secret, scopes)
        flow.user_agent = app_name
        # there is some strange error where something within tools.run_flow
        # looks for arguments in argv... and crashes since we have arbitrary
        # argv for whatever CLI ui used by caller
        _argv = sys.argv.copy()
        sys.argv = sys.argv[0:1]
        credentials = o2c.tools.run_flow(flow, store)
        sys.argv = _argv
        log.info('Storing credentials to ' + path_credentials)
    return credentials


class Googler:
    _client = None
    _api = None
    __service = None
    __version = None

    def __init__(self, app_name, service=None, version=None):
        self.app_name = app_name
        self.__service = service
        self.__version = version
        config = self.config = load_config(app_name)['gmail'].get()
        self.scopes = config['scopes']
        self.path_client_secret = os.path.expanduser(
            config['client_secret'])
        self.path_credentials = os.path.expanduser(
            config['credentials'])
        self.credentials = get_credentials(
            self.app_name, self.path_credentials, self.path_client_secret,
            self.scopes)
        self.auth2token = OAuth2TokenFromCredentials(self.credentials)

    def _get_client(self):
        raise NotImplementedError('This must be defined by subclass of Googler')

    @property
    def client(self):
        if not self._client:
            self._client = self._get_client()
        return self._client

    @property
    def api(self):
        if not self._api:
            self._api = self._discover()
        return self._api

    def _discover(self, service=None, version=None):
        _service = service or self.__service
        _version = version or self.__version
        credentials = get_credentials(self.app_name, self.path_credentials,
                                      self.path_client_secret, self.scopes)
        service = discovery.build(_service, _version, credentials=credentials)
        return service


class Spreadsheets(Googler):
    ''' '''
    def __init__(self, app_name, service='sheets', version='v4'):
        super().__init__(app_name, service, version)

    def _get_client(self):
        import gdata.spreadsheets.client
        gd_client = gdata.spreadsheets.client.SpreadsheetsClient(
            source=self.app_name)
        gd_client = self.auth2token.authorize(gd_client)
        return gd_client

    def create(self, title='Untitled Spreadsheet'):
        body = {
            'properties': {
                'title': title,
            }
        }
        request = self.api.spreadsheets().create(body=body)
        response = request.execute()
        return response


class Docs(Googler):
    ''' '''
    def __init__(self, app_name):
        super().__init__(app_name)

    def _get_client(self):
        import gdata.docs.client
        gd_client = gdata.docs.client.DocsClient(source=self.app_name)
        gd_client = self.auth2token.authorize(gd_client)
        return gd_client

    def create(self, title, _type='document'):
        import gdata.docs.data
        doc = gdata.docs.data.Resource(type=_type, title=title)
        doc = self.api.CreateResource(doc)
        return doc


class Contacts(Googler):
    ''' '''
    def _get_client(self):
        gd_client = gdata.contacts.client.ContactsClient(source=self.app_name)
        gd_client = self.auth2token.authorize(gd_client)
        return gd_client

    def get_contact_groups(self, query=None):
        ''' '''
        # FIXME: this is local query... we want to query using the API!
        # FIXME: name implies we should be returning a list of groups...
        groups = self.api.get_groups()
        group = None
        while True:
            for entry in groups.entry:
                title = entry.title.text.strip()
                if title == query:
                    group = entry
                    log.debug('Found group: {}'.format(group))
                    return group
            if groups.get_next_link():
                groups = self.api.get_next(groups)
            else:
                break
        return group

    def add_contact_group(self, title, members=None, prefix=None):
        ''' '''
        log.debug('... Adding {} members to {}'.format(len(members), title))
        title = title if not prefix else '{}{}'.format(prefix, title)
        # check if the group doesn't already exist
        new_group = self.get_contact_groups(title)
        if not new_group:
            log.info('... Creating group: {}'.format(title))
            # if the groups doesn't already exist, let's add it as requested
            new_group = self.api.contacts.data.GroupEntry(
                title=atom.data.Title(text=title))
            group = self.api.create_group(new_group)
        else:
            log.debug('... Found group: {}'.format(title))
            group = new_group

        for email in members:
            contact = self.find_contact(email)
            self.update_membership(contact, group)

        return group

    def update_membership(self, contact, group):
        '''
        input: gdata ContactEntry and GroupEntry objects
        '''
        if not contact:
            log.debug('Not updating membership for EMPTY contact.')
            return None
        _uid = contact.email[0].address
        _gtitle = group.title.text

        for contact_group in contact.group_membership_info:
            if contact_group.href == group.get_id():
                log.warn(
                    ' ... {} already a member of {}.'.format(_uid, _gtitle))
                return contact

        log.debug('Adding {} to group {}'.format(_uid, _gtitle))
        membership = self.api.contacts.data.GroupMembershipInfo(
            href=group.id.text)
        contact.group_membership_info.append(membership)
        contact = self.api.update(contact)
        return contact

    def find_contact(self, email):
        ''' '''
        feed = self.api.get_contacts(q=email)
        contact = None
        if not feed.entry:
            log.warn('Contact not found: {}'.format(email))
            return None
        elif len(feed.entry) > 1:
            log.warn(
                'Duplicates found for {}, using first found.'.format(email))
            contact = feed.entry[0]
        else:
            contact = feed.entry[0]
        return contact

    def list_contacts(self):
        ''' '''
        feed = self.api.get_contacts()
        for i, entry in enumerate(feed.entry):
            try:
                full_name = entry.name.full_name.text
            except Exception:
                full_name = 'NO NAME'
            print('\n{} {}'.format(i+1, full_name))
            if entry.content:
                print('    {}'.format(entry.content.text))
            # Display the primary email address for the contact.
            for email in entry.email:
                if email.primary and email.primary == 'true':
                    print('    {}'.format(email.address))
            # Show the contact groups that this contact is a member of.
            for group in entry.group_membership_info:
                print('    Member of group: {}'.format(group.href))
            # Display extended properties.
            for extended_property in entry.extended_property:
                if extended_property.value:
                    value = extended_property.value
                else:
                    value = extended_property.GetXmlBlob()
                print('    Extended Property - {}: {}'.format(
                        extended_property.name, value))


log = logging.getLogger(__name__)


if __name__ == '__main__':
    ipdb.set_trace()
