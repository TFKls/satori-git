# vim:ts=4:sts=4:sw=4:expandtab
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError, HttpResponseNotAllowed
from django.db import models
from satori.core.sec import Token, RoleSet
from satori.core.models import Privilege, Global, Object, AttributeGroup, OpenAttribute, Blob
import traceback

def server(request, model, id, name, group =None):
    if request.method not in ['GET', 'PUT']:
        return HttpResponseNotAllowed(['GET', 'PUT'])

    try:
        obj = models.get_model('core', model).objects.get(id=id)
        if group != None:
            obj = getattr(obj, group, None)
            assert(isinstance(obj, AttributeGroup))
    except:
        return HttpResponseNotFound()
    token = Token(request.COOKIES.get('satori_token', ''))
    try:
        oa = OpenAttribute.objects.get(object=obj, name=name)
    except:
        oa = None

    try:
        if request.method == 'GET':
        	return server_get(request, token, obj, oa, name)
        elif request.method == 'PUT':
        	return server_put(request, token, obj, oa, name)
    except:
        traceback.print_exc()
        return HttpResponseServerError()

def server_get(request, token, obj, oa, name):
    if not obj.demand_right(token, 'ATTRIBUTE_READ'):
        return HttpResponseForbidden()
    if oa == None:
        return HttpResponseNotFound()
    if oa.oatype != OpenAttribute.OATYPES_BLOB:
        return HttpResponseForbidden()
    blob = oa.blob_hash
    res = HttpResponse()
    res.write(blob.data)
    return res

def server_put(request, token, obj, oa, name):
#    if not obj.demand_right(token, 'ATTRIBUTE_WRITE'):
#        return HttpResponseForbidden()
    if oa == None:
    	oa = OpenAttribute(object=obj, name=name)
    oa.oatype=OpenAttribute.OATYPES_BLOB
    blob = Blob()
    len = int(request.environ.get('CONTENT_LENGTH', 0))
    blob.data = request.environ['wsgi.input'].read(len)
    blob.save()
    oa.blob_hash = blob
    oa.save()
    res = HttpResponse()
    res.write('OK')
    return res
