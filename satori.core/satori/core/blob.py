# vim:ts=4:sts=4:sw=4:expandtab
import logging
from django.db import models
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError, HttpResponseNotAllowed
import urllib
from satori.core.sec import Token
import satori.core.models
from satori.core.models import AttributeGroup, Blob, OpenAttribute, Privilege
from satori.core.export import token_container

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

    try:
        token_container.check_set_token_str(request.COOKIES.get('satori_token', ''))

        model = getattr(satori.core.models, model, None)
        if model is None:
            return HttpResponseNotFound()

        if group != 'oa':
            oa_field = None
            for field in model._meta.fields:
                if field.name == group:
                    oa_field = field
            if oa_field is None:
                return HttpResponseNotFound()
            if not isinstance(oa_field, models.ForeignKey):
                return HttpResponseNotFound()
            if oa_field.rel.to != AttributeGroup:
                return HttpResponseNotFound()

        try:
            entity = model.objects.get(id=id)
        except model.DoesNotExist:
            return HttpResponseNotFound()

        if not Privilege.demand(entity, 'VIEW'):
            return HttpResponseNotFound()

        if request.method == 'GET':
            return server_get(request, entity, name, group)
        elif request.method == 'PUT':
            return server_put(request, entity, name, group)
    except:
        logging.exception('BLOB server: error in handler')
        return HttpResponseServerError()

def server_get(request, entity, name, group):
    func = getattr(entity, group + '_get_blob')

    if not func._export_method.pc(self=entity, name=name):
        return HttpResponseForbidden()

    try:
        blob = func(name)
    except BadAttributeType:
        return HttpResponseNotFound()

    if blob is None:
        return HttpResponseNotFound()

    def reader():
        while True:
            data = blob.read(1024)
            if len(data) == 0:
                break
            yield data
        blob.close()

    res = HttpResponse(reader())
    res['content-length'] = str(blob.length)
    res['Filename'] = urllib.quote(str(blob.filename))
    return res

def server_put(request, entity, name, group):
    func = getattr(entity, group + '_set_blob')

    if not func._export_method.pc(self=entity, name=name):
        return HttpResponseForbidden()

    length = int(request.environ.get('CONTENT_LENGTH', 0))
    filename = urllib.unquote(request.environ.get('HTTP_FILENAME', ''))

    blob = func(name, filename=filename)

    while(length > 0):
        r = min(length, 1024)
        data = request.environ['wsgi.input'].read(r)
        blob.write(data)
        length = length - r

    hash = blob.close()

    res = HttpResponse(hash)
    res['content-length'] = str(len(hash))
    return res

def download(request, hash):
    if request.method not in ['GET']:
        return HttpResponseNotAllowed(['GET'])

    if isinstance(hash, unicode):
        hash = hash.encode('utf-8')

    try:
        token_container.check_set_token_str(request.COOKIES.get('satori_token', ''))

        if not Privilege.global_demand('RAW_BLOB'):
            return HttpResponseForbidden()

        if not Blob.exists(hash):
            return HttpResponseNotFound()

        blob = Blob.open(hash)

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
        logging.exception('BLOB server: error in download')
        return HttpResponseServerError()

def upload(request):
    if request.method not in ['PUT']:
        return HttpResponseNotAllowed(['PUT'])

    try:
        token_container.check_set_token_str(request.COOKIES.get('satori_token', ''))

        if not Privilege.global_demand('RAW_BLOB'):
            return HttpResponseForbidden()

        length = int(request.environ.get('CONTENT_LENGTH', 0))

        blob = Blob.create()

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
        logging.exception('BLOB server: error in upload')
        return HttpResponseServerError()

