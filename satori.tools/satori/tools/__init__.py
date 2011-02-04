# vim:ts=4:sts=4:sw=4:expandtab

from satori.client.common import want_import, remote
import ConfigParser
import getpass
import optparse
import os

want_import(globals(), 'User', 'token_container')

config = ConfigParser.RawConfigParser()
options = optparse.OptionParser()
options.add_option('-c', '--config', dest='config', help='alternative configuration file')
options.add_option('-s', '--section', dest='section', help='section from configuration file to use')
options.add_option('-H', '--host', dest='host', help='Satori host in format host_name:thrift_port:blob_port')
options.add_option('-u', '--username', dest='username', help='user name (or "-" to skip authentication)')

def setup():
    (options.options, options.args) = options.parse_args()

    if options.options.config:
        if not os.path.exists(options.options.config):
            raise RuntimeError('The specified configuration file "{0}" does not exist'.format(options.options.config))
        config.read(options.options.config)
    else:
        config.read(os.path.expanduser('~/.satori.cfg'))

    section = None

    hostname = None
    thrift_port = None
    blob_port = None
    username = None

    if options.options.section:
        section = options.options.section
        if not config.has_section(section):
            raise RuntimeError('The specified section "{0}" not found in config file'.format(section))
    elif config.has_option('defaults', 'section'):
        section = config.get('defaults', 'section')
        if not config.has_section(section):
            raise RuntimeError('The default section "{0}" not found in config file'.format(section))

    if section:
        if config.has_option(section, 'host'):
            hostname = config.get(section, 'host')

        if config.has_option(section, 'thrift_port'):
            thrift_port = config.getint(section, 'thrift_port')

        if config.has_option(section, 'blob_port'):
            blob_port = config.getint(section, 'blob_port')

        if config.has_option(section, 'login'):
            username = config.get(section, 'login')

    if options.options.host:
        (hostname, thrift_port, blob_port) = options.options.host.split(':')
        thrift_port = int(thrift_port)
        blob_port = int(blob_port)

    if options.options.username:
        username = options.options.username

    if not hostname:
        raise RuntimeError('Satori host name not specified in config file or arguments')

    if not thrift_port:
        raise RuntimeError('Satori Thrift port number not specified in config file or arguments')

    if not blob_port:
        raise RuntimeError('Satori blob port number not specified in config file or arguments')

    print 'Connecting to: {0}:{1}:{2}'.format(hostname, thrift_port, blob_port)

    remote.setup(hostname, thrift_port, blob_port)

    if username != '-':
        if not username:
            username = raw_input('User name: ')
        else:
            print 'User name: {0}'.format(username)

        password = getpass.getpass('Password: ')

        token_container.set_token(User.authenticate(username, password))
   
    return (options.options, options.args)
