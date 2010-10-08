# vim:ts=4:sts=4:sw=4:expandtab
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError, HttpResponseNotAllowed
import urllib
from satori.core import get_ars_interface
from satori.core import models
from satori.core.models import OpenAttribute
import traceback

interface = get_ars_interface()

def server(request, model, id, name, group):
    if request.method not in ['GET', 'PUT']:
        return HttpResponseNotAllowed(['GET', 'PUT'])

    if isinstance(model, unicode):
        model = model.encode('utf-8')
    if isinstance(id, unicode):
        id = id.encode('utf-8')
    if isinstance(name, unicode):
        name = name.encode('utf-8')
    if isinstance(group, unicode):
        group = group.encode('utf-8')

    token = request.COOKIES.get('satori_token', '')

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
        can_proc = interface.services[model].procedures[model + '_' + group + '_get_blob_can'].implementation
    except:
        traceback.print_exc()
        return HttpResponseNotFound()

    if not can_proc(token, id, name):
        return HttpResponseForbidden()

    obj = getattr(models, model).objects.get(id=id)
    
    if group != 'oa':
        obj = getattr(obj, group)

    oa = obj.attributes.oa_get(name)
    
    if (oa is None) or (not oa.is_blob):
        return HttpResponseNotFound()

    blob = OpenAttribute.open_blob(oa.value)

    def reader():
        while True:
            data = blob.read(1024)
            if len(data) == 0:
                break
            yield data
        blob.close()

    res = HttpResponse(reader())
    res['content-length'] = str(blob.length)
    res['Filename'] = urllib.quote(str(oa.filename))
    return res

def server_put(request, token, model, id, name, group):
    try:
        can_proc = interface.services[model].procedures[model + '_' + group + '_set_blob_can'].implementation
    except:
        return HttpResponseNotFound()

    if not can_proc(token, id, name):
        return HttpResponseForbidden()

    length = int(request.environ.get('CONTENT_LENGTH', 0))
    filename = urllib.unquote(request.environ.get('HTTP_FILENAME', ''))

    blob = OpenAttribute.create_blob()

    while(length > 0):
        r = min(length, 1024)
        data = request.environ['wsgi.input'].read(r)
        blob.write(data)
        length = length - r

    hash = blob.close()

    obj = getattr(models, model).objects.get(id=id)
    
    if group != 'oa':
        obj = getattr(obj, group)

    obj.attributes.oa_set(name, OpenAttribute(is_blob=True, value=hash, filename=filename))

    res = HttpResponse(hash)
    res['content-length'] = str(len(hash))
    return res

def download(request, hash):
    if request.method not in ['GET']:
        return HttpResponseNotAllowed(['GET'])

    if isinstance(hash, unicode):
        hash = hash.encode('utf-8')

    try:
        token = request.COOKIES.get('satori_token', '')

        try:
            can_proc = interface.services['Blob'].procedures['Blob_open_can'].implementation
        except:
            return HttpResponseNotFound()

        if not can_proc(token, hash):
            return HttpResponseForbidden()

        blob = OpenAttribute.open_blob(hash)

        def reader():
            while True:
                data = blob.read(1024)
                if len(data) == 0:
                    break
                yield data
            blob.close()

        res = HttpResponse(reader())
        res['content-length'] = str(blob.length)
        return res
    except:
        traceback.print_exc()
        return HttpResponseServerError()

def upload(request):
    if request.method not in ['PUT']:
        return HttpResponseNotAllowed(['PUT'])

    try:
        token = request.COOKIES.get('satori_token', '')

        try:
            can_proc = interface.services['Blob'].procedures['Blob_create_can'].implementation
        except:
            return HttpResponseNotFound()

        if not can_proc(token):
            return HttpResponseForbidden()

        length = int(request.environ.get('CONTENT_LENGTH', 0))

        blob = OpenAttribute.create_blob()

        while(length > 0):
            r = min(length, 1024)
            data = request.environ['wsgi.input'].read(r)
            blob.write(data)
            length = length - r

        hash = blob.close()

        res = HttpResponse(hash)
        res['content-length'] = str(len(hash))
        return res
    except:
        traceback.print_exc()
        return HttpResponseServerError()

