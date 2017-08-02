#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Chris Ward <cward@redhat.com>

'''
Instructions for getting your OAuth2 client_secret and credentials
1) Go to https://console.developers.google.com
2) Open 'Credentials' page
3) Create Client ID - Type: "Other" - Name: Airtable
4) Then, on the summary overview page, download the key as JSON
5) Then the first time you send an email a browser window will
   pop open and you must agree to the request
'''

import logging
import mimetypes
import os
import time

from comdev.lib import load_config, expand_path

from apiclient import discovery
import atom
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import gdata.contacts.client
import gdata.contacts.data
import gdata.service
from gdata.gauth import OAuth2TokenFromCredentials
import httplib2
import oauth2client
from oauth2client import client, tools


def get_credentials(app_name, credentials, client_secret, scopes):
    ''' '''
    store = oauth2client.file.Storage(credentials)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(client_secret, scopes)
        flow.user_agent = app_name
        credentials = tools.run_flow(flow, store)
        log.info('Storing credentials to ' + credentials)
    return credentials


class Gmailer(object):
    def __init__(self, app_name, sender=None):
        config = load_config(app_name)
        paths = {k: expand_path(x) for k, x in config['paths'].get().items()}
        self.path_logs = paths['logs']

        config = self.config = config['gmail'].get()

        self.app_name = app_name
        self.sender = sender or self.config['sender']
        self.gmail_app = config['app_name']
        self.scopes = config['scopes']
        self.path_client_secret = os.path.expanduser(
            config['client_secret'])
        self.path_credentials = os.path.expanduser(
            config['credentials'])

        self.credentials = get_credentials(
            self.app_name, self.path_credentials, self.path_client_secret,
            self.scopes)

    def _init_logging(self):
        logfile = os.path.join(self.path_logs, 'gmail.log')
        # Setup logging
        fhandler = logging.FileHandler(logfile)
        fhandler.setLevel(logging.CRITICAL)
        fhandler.propagate = False
        log.addHandler(fhandler)

    def send(self, to, subject, body_txt, body_html=None, sleep=0,
             attachments=None):
        ''' '''
        # FIXME: accept list of sendto email addresses
        sender = self.sender
        log.critical(
            'FROM: {}\nTO: {}\nSUBJ: {}\nBODY TEXT: {}\n{}'.format(
                sender, to, subject, body_txt, '-'*70))
        if not body_html:
            body_html = body_txt.replace('\n', '<br/>')
        log.info('Sending the message to {}'.format(to))
        result = self._send_msg(to, subject, body_html, body_txt, attachments)
        time.sleep(sleep)
        return result

    def _send_msg(self, to, subject, msgHtml, msgPlain, attachments):
        ''' '''
        http = self.credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http,
                                  cache_discovery=False)
        message1 = self._create_msg(to, subject, msgHtml, msgPlain, attachments)
        self._send_msg_internal(service, "me", message1)

    def _send_msg_internal(self, service, user_id, message):
        ''' '''
        try:
            message = service.users().messages().send(
                userId=user_id, body=message).execute()
            log.info('Message Id: %s' % message['id'])
            return message
        except Exception as error:
            log.error('An error occurred: %s' % error)

    def _create_msg(self, to, subject, msgHtml, msgPlain, attachments=None):
        '''
        attachments should be a list of paths
        '''
        sender = self.sender
        if attachments and isinstance(attachments, str):
            attachments = [attachments]
        else:
            attachments = list(attachments or [])

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = to
        msg.attach(MIMEText(msgPlain, 'plain'))
        msg.attach(MIMEText(msgHtml, 'html'))

        # append attachments if any
        for path in attachments:
            _attachment = self._prep_attachment(path)
            msg.attach(_attachment)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        #raw = raw.decode()
        body = {'raw': raw}
        return body

    def _prep_attachment(self, path):
        ''' '''
        if not os.path.exists(path):
            raise RuntimeError('Can not find attachment at {}'.format(path))

        content_type, encoding = mimetypes.guess_type(path)

        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
        if main_type == 'text':
            fp = open(path, 'rb')
            message = MIMEText(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'image':
            fp = open(path, 'rb')
            message = MIMEImage(fp.read(), _subtype=sub_type)
            fp.close()
        else:
            fp = open(path, 'rb')
            message = MIMEBase(main_type, sub_type)
            message.set_payload(fp.read())
            fp.close()
        filename = os.path.basename(path)
        message.add_header(
            'Content-Disposition', 'attachment', filename=filename)
        return message


class ContactsClient(object):
    ''' '''
    def __init__(self, app_name):
        config = self.config = load_config(app_name)['gmail'].get()

        self.gmail_app = config['app_name']
        self.scopes = config['scopes']
        self.path_client_secret = os.path.expanduser(
            config['client_secret'])
        self.path_credentials = os.path.expanduser(
            config['credentials'])

        self.app_name = app_name
        self.api = self._get_client()

        self.credentials = get_credentials(
            self.app_name, self.path_credentials, self.path_client_secret,
            self.scopes)

    def _get_client(self):
        auth2token = OAuth2TokenFromCredentials(self.credentials)
        gd_client = gdata.contacts.client.ContactsClient(source=self.app_name)
        gd_client = auth2token.authorize(gd_client)
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
                log.warn(' ... {} already a member of {}.'.format(_uid, _gtitle))
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
            except:
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
    import ipdb  # NOQA
    ipdb.set_trace()
