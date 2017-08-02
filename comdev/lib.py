#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Chris Ward <cward@redhat.com>

'''
'''

import getpass
import logging
import os
import pytz
import re

import confuse
import jinja2
import pandas as pd
from premailer import Premailer
import yaml


def as_list(obj):
    '''
    '''
    if isinstance(obj, str):
        return [x.strip() for x in obj.split(',')]
    elif isinstance(obj, pd.Series):
        return obj.apply(lambda x: [y.strip() for y in (x or '').split(',')])
    else:
        return list(obj)


def expand_path(path):
    return os.path.abspath(os.path.expanduser(path))


def set_path(dirname, parent_path=None, makedirs=True, env_var=None):
    '''
    '''
    if parent_path:
        path = os.path.join(parent_path, dirname)
    else:
        path = dirname
    path = os.path.expanduser(path)
    if makedirs and not os.path.exists(path):
        os.makedirs(path)
    if env_var:
        os.environ[env_var] = path
    return path


def load_yaml(path, transpose=True):
    '''
    '''
    path = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(path):
        raise IOError('{} does not exist'.format(path))
    with open(path) as stream:
        data = yaml.load(stream, yaml.Loader)
    if transpose:
        df = pd.DataFrame(data).T.copy()
    else:
        df = pd.DataFrame(data).copy()
    return df


def dump_yaml(data, path=None):
    '''
    '''
    path = os.path.abspath(os.path.expanduser(path)) if path else None
    if path:
        if not os.path.exists(path):
            raise IOError('{} does not exist'.format(path))
        with open(path, 'w') as outfile:
            yaml.dump(data, outfile, default_flow_style=False)
    else:
        content = yaml.dump(data, default_flow_style=False)
    return content


def load_config(app_name, path=None):
    '''
    '''
    if path:
        config = os.path.expanduser(os.path.abspath(path))
        # CONFIG - overide default location of the config.yaml file
        os.environ['{}DIR'.format(app_name.upper())] = config
    config = confuse.Configuration(app_name)
    return config


def parse_email(string):
    '''
    '''
    string = string.strip()
    result = re.match('^(["\']?([^<]*?)["\']? ?<)?([^>]+?)>?$', string)
    _, name, email = result.groups()
    user = (email, name)
    return user


def render_template(jinja2_env, path, params, inline_css=False):
    '''
    '''
    template = jinja2_env.get_template(path)
    content = template.render(**params)
    if os.path.basename(path).split('.')[-1].lower() == 'html':
        if inline_css:
            log.debug('... Inlining CSS')
            content = Premailer(
                content, remove_classes=True,
                cssutils_logging_level=logging.ERROR,
                preserve_inline_attachments=False).transform()
    return content


def get_jinja2_env(path_templates):
    _loader = jinja2.FileSystemLoader(path_templates)
    extensions = ['jinja2.ext.i18n', 'jinja2.ext.with_']
    env = jinja2.Environment(
        loader=_loader,
        autoescape=jinja2.select_autoescape(
            disabled_extensions=('txt',), default_for_string=True,
            default=True),
        extensions=extensions)
    return env


def dumps(content, path):
    '''
    '''
    log.debug('Exporting to {}'.format(path))
    mkdirs(path)
    with open(path, 'w') as out:
        out.writelines(content)


def dt_normalize(dt, iso=False, local_tz=False, utc_overide=False):
    '''
    '''
    dt = pd.to_datetime(dt, utc=True).to_pydatetime()
    if local_tz:
        try:
            dt = dt.astimezone(LOCAL_TZ)
        except ValueError:
            # ValueError: NaTType does not support astimezone
            log.debug('Failed to convert {} to local timezone'.format(dt))
            return dt

    # the source date is adjusted for local time but loaded as utc...
    # need to adjust local tz (to make utc) and then reset tz to utc
    dt = dt.replace(tzinfo=LOCAL_TZ) if utc_overide else dt

    # return a standard full iso string form
    dt = dt.strftime('%Y-%m-%dT%H:%M:%S.%f%z') if iso else dt
    return dt


def mkdirs(path):
    path = os.path.dirname(path)
    if not os.path.exists(path):
        log.debug('Creating path: {}'.format(path))
        os.makedirs(path)


logging.basicConfig(format='%(message)s')
log = logging.getLogger(__name__)

USER = getpass.getuser()
UTC_TZ = pytz.timezone('utc')
# FIXME: Why LOCAL_TZ == UTC? confusing...
LOCAL_TZ = pytz.timezone('utc')


if __name__ == '__main__':
    import ipdb  # NOQA
    ipdb.set_trace()
