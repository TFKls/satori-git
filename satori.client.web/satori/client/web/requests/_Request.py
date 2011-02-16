# vim:ts=4:sts=4:sw=4:expandtab

from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.http import HttpResponseRedirect
from django.http import HttpResponse

class MetaRequest(type):
    allreqs = {}
    
    def __init__(cls, name, bases, attrs):
        super(MetaRequest, cls).__init__(name, bases, attrs)
        #We don't want abstract class here
        if name != "Request":
            if not hasattr(cls, 'pathName'):
                raise Exception('No pathName in request ' + name)
            if cls.pathName in MetaRequest.allreqs:
                raise Exception('Two requests with the same pathName!') 
            MetaRequest.allreqs[cls.pathName] = cls

class Request:
    __metaclass__ = MetaRequest
    def __init__(self,params,path):
        pass
    @classmethod
    def process(self, request):
        'To overload'
        raise Exception('Request.process not overloaded!')

def process(argstr,request):
    res = MetaRequest.allreqs[argstr].process(request)
    if isinstance(res, HttpResponse):
        return res
    return HttpResponseRedirect(res)
