from satori.client.common.remote import *
from django.http import HttpResponse
import re

def getfile(argstr, request):
    params = re.split('\.',argstr)
    if params[0]=='pdfstatement':
        pid = int(params[1])
        pm = ProblemMapping.filter({'id' : int(params[1])})[0]
        response = HttpResponse(mimetype='application/pdf')
        response['Content-Disposition'] = 'attachment; filename='+pm.code+'.pdf'
        reader = pm.statement_get_blob('pdf')
        response.write(reader.read(reader.length))
        reader.close()
        return response
    if params[0]=='defaulttestdata':
        pid = int(params[1])
        pm = Problem.filter({'id' : int(params[1])})[0]
        response = HttpResponse(mimetype='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename='+pm.name+'.'+params[2]+'.default'
        reader = pm.default_test_data_get_blob(params[2])
        response.write(reader.read(reader.length))
        reader.close()
        return response
    if params[0]=='testdata':
        pid = int(params[1])
        t = Test.filter({'id' : int(params[1])})[0]
        response = HttpResponse(mimetype='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename='+t.name+'.'+params[2]
        reader = t.oa_get_blob(params[2])
        response.write(reader.read(reader.length))
        reader.close()
        return response
    if params[0]=='submit':
        pid = int(params[1])
        s = Submit.filter({'id' : pid})[0]
        response = HttpResponse(mimetype='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename=submit'+params[1]
        reader = s.data_get_blob('content')
        response.write(reader.read(reader.length))
        reader.close()
        return response
        
