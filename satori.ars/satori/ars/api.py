# vim:ts=4:sts=4:sw=4:expandtab
"""The base API for ARS providers.
"""


from satori.objects import Object


class Reader(Object):
    """Abstract. Reads ARS Contract(s) from a file-like objects.
    """

    def readFrom(self, source):
        """Abstract. Read Contract(s) from file.
        """
        raise NotImplementedError()

    @property
    def contracts(self):
        """Abstract. Set. The Contract(s) read by this Reader.
        """
        raise NotImplementedError()


class Writer(Object):
    """Abstract. Writes ARS Contract(s) to a file-like object.
    """

    @property
    def contracts(self):
        """Abstract. MutableSet. The Contract(s) to be written by this Writer.
        """
        raise NotImplementedError()

    def writeTo(self, target):
        """Abstract. Write Contract(s) to file.
        """
        raise NotImplementedError()


class Server(Object):
    """Abstract. Server ARS Contract(s).
    """

    @property
    def contracts(self):
        """Abstract. MutableSet. The Contract(s) to be served by this Server.
        """
        raise NotImplementedError()

    def run(self):
        """Abstract. Run the server.
        """
        raise NotImplementedError()


class Client(Object):
    """Abstract. Client fo ARS Contract(s).
    """

    @property
    def contracts(self):
        """Abstract. MutableSet. The Contract(s) to be handled by this Client.
        """
        raise NotImplementedError()

    def start(self):
        """Abstract. Start the client. Implement the Procedure(s) in Contract(s).
        """
        raise NotImplementedError()

    def stop(self):
        """Abstract. Stop the client. Unimplement the Procedure(s) in Contract(s).
        """
        raise NotImplementedError()
