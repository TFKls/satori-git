# vim:ts=4:sts=4:sw=4:expandtab

from six import print_

from satori.client.common import want_import, remote
from six.moves import configparser
import getpass
import logging
import argparse
import os
import sys

want_import(globals(), 'Machine', 'User', 'token_container', 'TokenInvalid', 'TokenExpired')

config = configparser.RawConfigParser()
options = argparse.ArgumentParser()
thrift_settings = options.add_argument_group('thrift settings')
thrift_settings.add_argument('-c', '--config', help='alternative configuration file')
thrift_settings.add_argument('-s', '--section', help='section from configuration file to use')
thrift_settings.add_argument('-H', '--host', help='Satori host in format host_name:thrift_port:blob_port')
thrift_settings.add_argument('-u', '--username', help='user name (or "-" to skip authentication)')
thrift_settings.add_argument('-p', '--password', help='password')
thrift_settings.add_argument('-m', '--machine', help='machine name (or "-" to skip authentication)')
thrift_settings.add_argument('-S', '--ssl', help='use SSL', action='store_true')
options.add_argument('-l', '--loglevel', type=int, help='Log level (as in logging module in python)')

class AuthSetup:
    def __init__(self):
        self.clear()

    def clear(self):
        self.section = None
        self.hostname = None
        self.thrift_port = None
        self.blob_port = None
        self.username = None
        self.machine = None
        self.password = None
        self.ssl = False

    def setup(self):
        if not self.hostname:
            raise RuntimeError('Satori host name not specified in config file or arguments')
        if not self.thrift_port:
            raise RuntimeError('Satori Thrift port number not specified in config file or arguments')
        if not self.blob_port:
            raise RuntimeError('Satori blob port number not specified in config file or arguments')
        logging.debug('Connecting to: {0}:{1}:{2}{3}'.format(self.hostname, self.thrift_port, self.blob_port, ' (SSL)' if self.ssl else ''))
        remote.setup(self.hostname, self.thrift_port, self.blob_port, self.ssl)

    def authenticate(self):
        if self.machine:
            print_('Machine name: {0}'.format(self.machine))
            if not self.password:
                self.password = getpass.getpass('Password: ')
            try:
                token_container.set_token(Machine.authenticate(self.machine, self.password))
            except (TokenInvalid, TokenExpired):
                token_container.set_token('')
                token_container.set_token(Machine.authenticate(self.machine, self.password))
        elif self.username != '-':
            if not self.username:
                self.username = raw_input('User name: ')
                self.password = None
            else:
                print_('User name: {0}'.format(self.username))
            if not self.password:
                self.password = getpass.getpass('Password: ')
            try:
                token_container.set_token(User.authenticate(self.username, self.password))
            except (TokenInvalid, TokenExpired):
                token_container.set_token('')
                token_container.set_token(User.authenticate(self.username, self.password))

auth_setup = AuthSetup()

def setup(log_level=logging.DEBUG):
    logger = logging.getLogger()
    logger.setLevel(log_level)

    for handler in logger.handlers:
        logger.removeHandler(handler)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    auth_setup.clear()

    option_values = options.parse_args()

    if option_values.config:
        if not os.path.exists(option_values.config):
            raise RuntimeError('The specified configuration file "{0}" does not exist'.format(option_values.config))
        config.read(option_values.config)
    else:
        config.read(os.path.expanduser('~/.satori.cfg'))

    if option_values.section:
        auth_setup.section = option_values.section
        if not config.has_section(auth_setup.section):
            raise RuntimeError('The specified section "{0}" not found in config file'.format(auth_setup.section))
    elif config.has_option('defaults', 'section'):
        auth_setup.section = config.get('defaults', 'section')
        if not config.has_section(auth_setup.section):
            raise RuntimeError('The default section "{0}" not found in config file'.format(auth_setup.section))

    if auth_setup.section:
        if config.has_option(auth_setup.section, 'host'):
            host = config.get(auth_setup.section, 'host')
            if len(host.split(':')) == 3:
                (auth_setup.hostname, auth_setup.thrift_port, auth_setup.blob_port) = host.split(':')
                auth_setup.thrift_port = int(auth_setup.thrift_port)
                auth_setup.blob_port = int(auth_setup.blob_port)
            else:
                auth_setup.hostname = host

        if config.has_option(auth_setup.section, 'thrift_port'):
            auth_setup.thrift_port = config.getint(auth_setup.section, 'thrift_port')

        if config.has_option(auth_setup.section, 'blob_port'):
            auth_setup.blob_port = config.getint(auth_setup.section, 'blob_port')

        if config.has_option(auth_setup.section, 'username'):
            auth_setup.username = config.get(auth_setup.section, 'username')

        if config.has_option(auth_setup.section, 'machine'):
            auth_setup.machine = config.get(auth_setup.section, 'machine')

        if config.has_option(auth_setup.section, 'password'):
            auth_setup.password = config.get(auth_setup.section, 'password')

        if config.has_option(auth_setup.section, 'ssl'):
            auth_setup.ssl = config.getboolean(auth_setup.section, 'ssl')

        if config.has_option(auth_setup.section, 'loglevel'):
            logger.setLevel(logging._levelNames[config.get(auth_setup.section, 'loglevel')])

    if option_values.host:
        (auth_setup.hostname, auth_setup.thrift_port, auth_setup.blob_port) = option_values.host.split(':')
        auth_setup.thrift_port = int(auth_setup.thrift_port)
        auth_setup.blob_port = int(auth_setup.blob_port)

    if option_values.username:
        auth_setup.username = option_values.username

    if option_values.password:
        auth_setup.password = option_values.password

    if option_values.machine:
        auth_setup.machine = option_values.machine

    if option_values.ssl:
        auth_setup.ssl = True

    if option_values.loglevel:
        logger.setLevel(logging._levelNames[option_values.loglevel])

    auth_setup.setup()

    auth_setup.authenticate()

    return option_values

def authenticate():
    auth_setup.authenticate()

def catch_exceptions(f):
    def ff(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except SystemExit:
            pass
        except:
            logging.exception("An error occured")
            exctype, value = sys.exc_info()[:2]
            print_("An error occured: ", str(value), file=sys.stderr)
    return ff

