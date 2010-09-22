# vim:ts=4:sts=4:sw=4:expandtab

import threading

server_info = threading.local()
server_info.client_ip = None
server_info.client_port = None
