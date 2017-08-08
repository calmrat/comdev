#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Automatically generate visa invitation letters as pdf and mail to recipient
"""

import datetime

import ipdb  # NOQA
import pdfkit

from comdev.lib import load_config


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

        config = load_config(app_name)
        event = config['events'][event_name].get()
        self.params.update(event)

        print(self.params)

    def export():
        pdfkit.from_file(["temp.html"], "visas/visa_" + str(user_id) + ".pdf")


if __name__ == '__main__':
    ipdb.set_trace()
    cli(obj={})
