# vim:ts=4:sts=4:sw=4:expandtab
"""The base API for ARS providers.
"""


class Reader(object):
    """Abstract. Reads ARS Contract(s) from a file-like objects.
    """

    def readFrom(self, source):
        """Abstract. Read Contract(s) from file.
        """
        raise NotImplementedError()


class Writer(object):
    """Abstract. Writes ARS Contract(s) to a file-like object.
    """

    def writeTo(self, contracts, target):
        """Abstract. Write Contract(s) to file.
        """
        raise NotImplementedError()


class Server(object):
    """Abstract. Server ARS Contract(s).
    """

    def run(self):
        """Abstract. Run the server.
        """
        raise NotImplementedError()


class Client(object):
    """Abstract. Client fo ARS Contract(s).
    """

    def start(self):
        """Abstract. Start the client. Implement the Procedure(s) in Contract(s).
        """
        raise NotImplementedError()

    def stop(self):
        """Abstract. Stop the client. Unimplement the Procedure(s) in Contract(s).
        """
        raise NotImplementedError()
