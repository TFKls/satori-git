# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from django.http import HttpResponse
from mimetypes import guess_type

def blob_generator(blob):
    length = blob.length
    counter = 0
    chunk = 1024
    while counter<length:
        r = min(chunk, length-counter)
        counter = counter+r
        yield blob.read(r)
    blob.close()

def getfile(request, mode, model, id, attr_name, file_name):
    try:
        token_container.set_token(request.COOKIES.get('satori_token', ''))
    except:
        token_container.set_token('')

    obj = globals()[model](int(id))
    blob = obj.oa_get_blob(attr_name)
    
    response = HttpResponse(content=blob_generator(blob), mimetype=guess_type(file_name)[0])
    if mode == 'download':
        response['Content-Disposition'] = 'attachment; filename='+file_name
    return response

def getfile_group(request, mode, model, id, group_name, attr_name, file_name):
    try:
        token_container.set_token(request.COOKIES.get('satori_token', ''))
    except:
        token_container.set_token('')

    obj = globals()[model](int(id))
    blob = getattr(obj, group_name + '_get_blob')(attr_name)
    
    response = HttpResponse(content=blob_generator(blob), mimetype=guess_type(file_name)[0])
    if mode == 'download':
        response['Content-Disposition'] = 'attachment; filename='+file_name
    return response
