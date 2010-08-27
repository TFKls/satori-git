from copy import deepcopy
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
#from satori.core.models import *
from satori.client.common import *
from satori.client.web.postmarkup import render_bbcode

class MetaWidget(type):
    allwidgets = {}
    
    def __init__(cls, name, bases, attrs):
        super(MetaWidget, cls).__init__(name, bases, attrs)
        #We don't want abstract class here
        if name != "Widget":
            if not hasattr(cls, 'pathName'):
                raise Exception('No pathName in widget ' + name)
            if cls.pathName in MetaWidget.allwidgets:
                raise Exception('Two widgets with the same pathName!') 
            MetaWidget.allwidgets[cls.pathName] = cls

class Widget:
    __metaclass__ = MetaWidget
    def __init__(self,params,path):
        pass

# returns a newly created widget of a given kind
    @staticmethod
    def FromDictionary(dict,path):
        if not ('name' in dict.keys()):
            dict = DefaultLayout(dict)
            #return dict #CoverWidget(dict, path)
        d = follow(dict,path)
        name = d['name'][0]
        return MetaWidget.allwidgets[name](dict,path)

