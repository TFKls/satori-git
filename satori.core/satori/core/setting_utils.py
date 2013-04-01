import string

def parse_hostport(s, default_host, default_port):
	if not s:
		return default_host, default_port
	parts = string.split(s, ':')
	if len(parts) == 1:
		return default_host, int(s)
	if len(parts) == 2:
		host = parts[0] or default_host
		port = int(parts[1]) if parts[1] else default_port
		return host, port

