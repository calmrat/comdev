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

Instructions:
    https://developers.google.com/sheets/api/quickstart/python
    https://developers.google.com/drive/v3/web/quickstart/python
'''

# FIXME: RENAME THIS TO GOOGLE since we're using contacts, calendar,
# spreadsheet....

import logging
import ipdb  # NOQA
import mimetypes
import os
import time
import sys

from comdev.lib import load_config, expand_path

# FIXME: reconcile this! use one library?
from apiclient import discovery
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import httplib2
import oauth2client
from oauth2client import client, tools


def get_credentials(app_name, path_credentials, client_secret, scopes):
    ''' '''
    store = oauth2client.file.Storage(path_credentials)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(client_secret, scopes)
        flow.user_agent = app_name
        # there is some strange error where something within tools.run_flow
        # looks for arguments in argv... and crashes since we have arbitrary
        # argv for whatever CLI ui used by caller
        _argv = sys.argv.copy()
        sys.argv = sys.argv[0:1]
        credentials = tools.run_flow(flow, store)
        sys.argv = _argv
        log.info('Storing credentials to ' + str(credentials))
    return credentials


class Gmailer(object):
    def __init__(self, app_name, sender=None):
        config = load_config(app_name)
        paths = {k: expand_path(x) for k, x in config['paths'].get().items()}

        self.path_logs = paths['logs']

        #self._init_logging()

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
        # FIXME: This isn't working as expected; logging calls are still
        # propagating
        logfile = os.path.join(self.path_logs, 'gmail.log')
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


log = logging.getLogger(__name__)


if __name__ == '__main__':
    ipdb.set_trace()
