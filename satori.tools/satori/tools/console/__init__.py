# vim:ts=4:sts=4:sw=4:expandtab

def main():
    from satori.tools import setup

    setup()

    import code
    import readline
    console = code.InteractiveConsole()
    console.runcode('from satori.client.common import want_import')
    console.runcode('want_import(globals(), "*")')
    console.interact()


