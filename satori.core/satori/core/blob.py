# vim:ts=4:sts=4:sw=4:expandtab
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError, HttpResponseNotAllowed
from satori.core import get_ars_interface
from satori.core.models import OpenAttribute
import traceback

interface = get_ars_interface()

def server(request, model, id, name, group):
    if request.method not in ['GET', 'PUT']:
        return HttpResponseNotAllowed(['GET', 'PUT'])

    model = str(model)
    id = str(id)
    name = str(name)
    group = str(group)

    token = request.COOKIES.get('satori_token', '')
    print 'T', token.__class__

    try:
        if request.method == 'GET':
        	return server_get(request, token, model, id, name, group)
        elif request.method == 'PUT':
        	return server_put(request, token, model, id, name, group)
    except:
        traceback.print_exc()
        return HttpResponseServerError()

def server_get(request, token, model, id, name, group):
    try:
        print model + '_' + group + '_get_blob_hash_can'
        print model + '_' + group + '_get_blob_hash'
        can_proc = interface.services[model].procedures[model + '_' + group + '_get_blob_hash_can'].implementation
        proc = interface.services[model].procedures[model + '_' + group + '_get_blob_hash'].implementation
    except:
        traceback.print_exc()
        return HttpResponseNotFound()
    
    print 'a'

    if not can_proc(token, id, name):
    	return HttpResponseForbidden()

    print 'b'

    hash = proc(token, id, name)

    if hash is None:
        return HttpResponseNotFound()
    
    blob = OpenAttribute.open_blob(hash)

    def reader():
        while True:
            data = blob.read(1024)
            if len(data) == 0:
                break
            yield data
        blob.close()

    res = HttpResponse(reader())
    res['content-length'] = str(blob.length())
    return res

def server_put(request, token, model, id, name, group):
    try:
        can_proc = interface.services[model].procedures[model + '_' + group + '_set_blob_hash_can'].implementation
        proc = interface.services[model].procedures[model + '_' + group + '_set_blob_hash'].implementation
    except:
        return HttpResponseNotFound()

    if not can_proc(token, id, name, ''):
    	return HttpResponseForbidden()

    length = int(request.environ.get('CONTENT_LENGTH', 0))
    filename = request.environ.get('HTTP_FILENAME', '')

    blob = OpenAttribute.create_blob()

    while(length > 0):
        r = min(length, 1024)
        data = request.environ['wsgi.input'].read(r)
        blob.write(data)
        length = length - r

    hash = blob.close()

    proc(token, id, name, hash, filename)

    res = HttpResponse(hash)
    res['content-length'] = str(len(hash))
    return res

def upload(request):
    if request.method not in ['PUT']:
        return HttpResponseNotAllowed(['PUT'])

    # TODO: check permissions

    try:
        blob = OpenAttribute.create_blob()

        while(length > 0):
            r = min(length, 1024)
            data = request.environ['wsgi.input'].read(r)
            blob.write(data)
            length = length - r

        hash = blob.close()

        proc(token, id, name, hash, filename)

        res = HttpResponse(hash)
        res['content-length'] = str(len(hash))
    except:
        traceback.print_exc()
        return HttpResponseServerError()

