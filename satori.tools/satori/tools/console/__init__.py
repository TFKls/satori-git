# vim:ts=4:sts=4:sw=4:expandtab

def main():
    from satori.tools import options, setup

    options.add_argument('--ipython', help='Use IPython', action='store_true')
    flags = setup()

    from satori.client.common import want_import
    want_import(globals(), "*")

    if flags.ipython:
        print 'IPython needs to be manually installed in your virtual environment'
        from IPython import embed
        embed()
    else:
        import code
        console = code.InteractiveConsole()
        console.interact()

