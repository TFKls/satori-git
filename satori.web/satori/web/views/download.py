# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from django.http import HttpResponse
from mimetypes import guess_type

def getfile(request, model, id, attr_name, file_name):
    try:
        token_container.set_token(request.COOKIES.get('satori_token', ''))
    except:
        token_container.set_token('')
    obj = globals()[model](int(id))
    blob = obj.oa_get_blob(attr_name)
    
    def generator():
        length = blob.length()
        counter = 0
        chunk = 1024
        while counter<length:
            r = min(chunk, length-counter)
            counter = counter+r
            yield blob.read(r)
        blob.close()
    response = HttpResponse(content=generator,mimetype=guesstype(file_name)[0])
    response['Content-Disposition'] = 'attachment; filename='+filename
    return response
