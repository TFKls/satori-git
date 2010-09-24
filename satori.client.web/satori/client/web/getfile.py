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
