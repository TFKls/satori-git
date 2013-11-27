# vim:ts=4:sts=4:sw=4:expandtab

import logging

def main():
    from satori.tools import options, setup

    options.add_argument('--ipython', help='Use IPython', action='store_true')
    flags = setup(logging.INFO)

    if flags.ipython:
        from satori.client.common import want_import
        want_import(globals(), "*")
        from IPython import embed
        embed()
    else:
        import code
        console = code.InteractiveConsole()
        console.runcode('from satori.client.common import want_import')
        console.runcode('want_import(globals(), "*")')
        console.interact()
