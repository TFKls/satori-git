from six import print_
# vim:ts=4:sts=4:sw=4:expandtab

def start_console():
    import code
    import readline
    console = code.InteractiveConsole()
    console.runcode('from satori.client.common.remote import *')
    print
    print_('satori.client.common.remote classes are imported')
    print
    console.interact()

def start_local_console():
    import code
    import readline
    console = code.InteractiveConsole()
    console.runcode('from satori.client.common.local import *')
    print
    print_('satori.client.common.local classes are imported')
    print
    console.interact()

_wanted_imports = {}
_api = None

def _import_into(namespace, classes):
    if '*' in classes:
        namespace.update(_api)
    else:
        for c in classes:
            if not c in _api:
                raise RuntimeError('Class {0} cannot be imported.'.format(c))
            else:
                namespace[c] = _api[c]


def want_import(namespace, *classes):
    if _api is not None:
        _import_into(namespace, classes)
    _wanted_imports.setdefault(id(namespace), (namespace, set()))[1].update(classes)

def setup_api(api):
    global _api
    _api = api
    for (identity, (namespace, classes)) in _wanted_imports.items():
        _import_into(namespace, classes)


