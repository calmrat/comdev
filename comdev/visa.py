#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: Chris Ward <cward@redhat.com>
# Based off a work done by fzatlouk@redhat.com

"""
Automatically generate visa invitation letters as pdf and mail to recipient
"""

import datetime
import os  # NOQA

import ipdb  # NOQA
from pandoc.core import Document

from comdev.lib import load_config, expand_path, render_template
from comdev.lib import get_jinja2_env, saveas


class Viser(object):
    def __init__(self, app_name, event_name, invitee_name, passport_number,
                 passport_expiration, passport_issued_by, invitee_citizenship,
                 dt_arrival, dt_departure):

        today = datetime.date.today().isoformat()

        self.params = {
            'today': today,
            'invitee_name': invitee_name,
            'passport_number': passport_number,
            'passport_expiration': passport_expiration,
            'passport_issued_by': passport_issued_by,
            'invitee_citizenship': invitee_citizenship,
            'dt_arrival': dt_arrival,
            'dt_departure': dt_departure,
        }

        self.config = config = load_config(app_name).get()
        event = config['events'][event_name]

        self.params.update(event)
        self.params.update(
            {k: expand_path(v) for k, v in self.params.items() if '~' in v})

        with open( self.params['event_description']) as f:
            content = ''.join(f.readlines())
            self.params['event_description'] = content

    def export(self):
        # # PATTERN? # #
        # move this all into render_template or this function into comdev.lib?
        #
        config = self.config
        today = self.params['today']
        path_templates_comdev = expand_path(
            config['paths']['templates'].get('comdev'))
        path_template = 'visa/invitation-letter.html'
        path_build = expand_path(config['paths']['build'])
        path_export = expand_path(config['paths']['export'])
        path_locale = expand_path(config['paths']['locale'])
        jinja2_env = get_jinja2_env(path_templates_comdev,
                                    path_build=path_build,
                                    path_locale=path_locale)
        content = render_template(jinja2_env, path_template, self.params)
        name = self.params.get('invitee_name').replace(' ', '-')
        path_file = 'visa-invitation-letter-{}-{}'.format(name, today)
        saveas(path_file, content, 'html', path_export)
        #
        # # END PATTERN? # #

        path_pdf = os.path.join(path_export, '{}.pdf'.format(path_file))
        path_saveas = os.path.join(path_export, path_file + '.html')
        #doc = Document()
        #doc.html = content
        #doc.to_file(path_pdf)
        import pdfkit
        pdfkit.from_file(path_saveas, path_pdf)



if __name__ == '__main__':
    kwargs = dict(app_name='devconf', event_name='DevConf.cz 2018',
                  invitee_name='Chris Ward', passport_number='XXXXXXYYYYYY',
                  passport_expiration='2018-01-01', passport_issued_by='XXX',
                  invitee_citizenship='XXX', dt_arrival='2018-01-20',
                  dt_departure='2018-01-28')
    v = Viser(**kwargs)
    v.export()
