# vim:ts=4:sts=4:sw=4:expandtab

from satori.client.common import want_import, remote
import ConfigParser
import getpass
import optparse
import os

want_import(globals(), 'Machine', 'User', 'token_container', 'TokenInvalid', 'TokenExpired')

config = ConfigParser.RawConfigParser()
options = optparse.OptionParser()
options.add_option('-c', '--config', dest='config', help='alternative configuration file')
options.add_option('-s', '--section', dest='section', help='section from configuration file to use')
options.add_option('-H', '--host', dest='host', help='Satori host in format host_name:thrift_port:blob_port')
options.add_option('-u', '--username', dest='username', help='user name (or "-" to skip authentication)')
options.add_option('-p', '--password', dest='password', help='password')
options.add_option('-m', '--machine', dest='machine', help='machine name (or "-" to skip authentication)')
options.add_option('-S', '--ssl', dest='ssl', help='use SSL', action='store_true')

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
        print 'Connecting to: {0}:{1}:{2}{3}'.format(self.hostname, self.thrift_port, self.blob_port, ' (SSL)' if self.ssl else '')
        remote.setup(self.hostname, self.thrift_port, self.blob_port, self.ssl)

    def authenticate(self):
        if self.machine:
            print 'Machine name: {0}'.format(self.machine)
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
                print 'User name: {0}'.format(self.username)
            if not self.password:
                self.password = getpass.getpass('Password: ')
            try:
                token_container.set_token(User.authenticate(self.username, self.password))
            except (TokenInvalid, TokenExpired):
                token_container.set_token('')
                token_container.set_token(User.authenticate(self.username, self.password))

auth_setup = AuthSetup()

def setup():
    auth_setup.clear()

    (options.options, options.args) = options.parse_args()

    if options.options.config:
        if not os.path.exists(options.options.config):
            raise RuntimeError('The specified configuration file "{0}" does not exist'.format(options.options.config))
        config.read(options.options.config)
    else:
        config.read(os.path.expanduser('~/.satori.cfg'))


    if options.options.section:
        auth_setup.section = options.options.section
        if not config.has_section(auth_setup.section):
            raise RuntimeError('The specified section "{0}" not found in config file'.format(auth_setup.section))
    elif config.has_option('defaults', 'section'):
        auth_setup.section = config.get('defaults', 'section')
        if not config.has_section(auth_setup.section):
            raise RuntimeError('The default section "{0}" not found in config file'.format(auth_setup.section))

    if auth_setup.section:
        if config.has_option(auth_setup.section, 'host'):
            auth_setup.hostname = config.get(auth_setup.section, 'host')

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

    if options.options.host:
        (auth_setup.hostname, auth_setup.thrift_port, auth_setup.blob_port) = options.options.host.split(':')
        auth_setup.thrift_port = int(auth_setup.thrift_port)
        auth_setup.blob_port = int(auth_setup.blob_port)

    if options.options.username:
        auth_setup.username = options.options.username

    if options.options.password:
        auth_setup.password = options.options.password

    if options.options.machine:
        auth_setup.machine = options.options.machine

    if options.options.ssl:
        auth_setup.ssl = True

    auth_setup.setup()

    auth_setup.authenticate()

    return (options.options, options.args)

def authenticate():
    auth_setup.authenticate()
