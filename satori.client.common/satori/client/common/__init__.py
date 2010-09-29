# vim:ts=4:sts=4:sw=4:expandtab

def start_console():
    import code
    import readline
    console = code.InteractiveConsole()
    console.runcode('from satori.client.common.remote import *')
    print
    print 'satori.client.common.remote classes are imported'
    print
    console.interact()

def start_local_console():
    import code
    import readline
    console = code.InteractiveConsole()
    console.runcode('from satori.client.common.local import *')
    print
    print 'satori.client.common.local classes are imported'
    print
    console.interact()

