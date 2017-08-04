#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Chris Ward <cward@redhat.com>

'''
'''

import datetime
import dateutil
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


## Configuration with confuse
def load_config(app_name, path=None):
    '''
    '''
    if path:
        config = os.path.expanduser(os.path.abspath(path))
        # CONFIG - overide default location of the config.yaml file
        os.environ['{}DIR'.format(app_name.upper())] = config
    config = confuse.Configuration(app_name)
    return config


## JINJA2
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
    path_templates = expand_path(path_templates)
    _loader = jinja2.FileSystemLoader(path_templates)
    extensions = ['jinja2.ext.i18n', 'jinja2.ext.with_']
    env = jinja2.Environment(
        loader=_loader,
        autoescape=jinja2.select_autoescape(
            disabled_extensions=('txt',), default_for_string=True,
            default=True),
        extensions=extensions)
    return env


## Object manipulation
def as_list(obj):
    '''
    '''
    if isinstance(obj, str):
        return [x.strip() for x in obj.split(',')]
    elif isinstance(obj, pd.Series):
        return obj.apply(lambda x: [y.strip() for y in (x or '').split(',')])
    else:
        return list(obj)


def list2str(values, separator=";"):
    if not isinstance(values, (list, tuple)):
        return values
    values = ['' if not x or x != x else x for x in values]
    separator = separator + ' '
    try:
        values_csv = separator.join(values)
    except TypeError:
        # ATTACHMENT field types have ordereddicts in them...
        values_csv = str(values)
    return values_csv


## Datetime
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


def today(iso=True):
    d = datetime.date.today()
    if iso:
        return d.isoformat()
    else:
        return d


def now(iso=True):
    dt = datetime.datetime.now()
    if iso:
        return dt.isoformat()
    else:
        return dt


def this_month(iso=True):
    dt = today(False)
    dt = datetime.date(dt.year, dt.month, 1)
    if iso:
        return dt.strftime('%B')
    else:
        return dt


def last_month(iso=True):
    dt = this_month(False) + dateutil.relativedelta.relativedelta(months=-1)
    if iso:
        return dt.strftime('%B')
    else:
        return dt


def last_month_year(iso=True):
    dt = last_month(False)
    if iso:
        return dt.strftime('%Y')
    else:
        return dt


## Path manipulation
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


def saveas(title, message, ext, subdir=None):
    path = sluggify(title, ext, subdir)
    dumps(message, path)


def sluggify(string, ext=None, subdir=None, keep_characters=(' ', '.', '-')):
    path = expand_path(subdir or './')
    slug = "".join(c for c in string
                   if c.isalnum() or c in keep_characters).rstrip()
    slug = "-".join(slug.split())
    # append an extension to the slug (eg, file extension)
    ext = '.' + ext.lstrip('.') if ext else ''
    slug = '{}{}'.format(slug, ext) if ext else slug
    # prepend a path if provided
    if not os.path.exists(path):
        log.debug('Creating path: {}'.format(path))
        os.makedirs(path)
    slug = os.path.join(path, slug) if path else slug
    slug = re.sub('\-+', '-', slug)
    return slug


## I/O
def dumps(content, path):
    '''
    '''
    path = expand_path(path)
    log.info('Dumping content to {}'.format(path))
    mkdirs(path)
    with open(path, 'w') as out:
        out.writelines(content)


def mkdirs(path):
    path = os.path.dirname(path)
    if not os.path.exists(path):
        log.debug('Creating path: {}'.format(path))
        os.makedirs(path)


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


def load_pickle(path, name=None):
    log.debug('Loading pickle at {}'.format(path))
    df = pd.read_pickle(path)
    df.name = name if name else df.name
    return df


def save_pickle(df, path):
    log.debug(' . Saving pickle file {}'.format(path))
    return df.to_pickle(path)


logging.basicConfig(format='%(message)s')
log = logging.getLogger(__name__)

USER = getpass.getuser()
UTC_TZ = pytz.timezone('utc')
# FIXME: Why LOCAL_TZ == UTC? confusing...
LOCAL_TZ = pytz.timezone('utc')
#if config['local_timezone'].exists():
#    LOCAL_TZ = pytz.timezone(config['local_timezone'].get())
#else:
#    LOCAL_TZ = pytz.timezone('utc')


if __name__ == '__main__':
    import ipdb  # NOQA
    ipdb.set_trace()
