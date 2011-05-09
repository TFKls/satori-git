from satori.client.common import want_import
want_import(globals(), '*')
from datetime import datetime
from xml.dom import minidom
from django import forms
from satori.web.utils import forms as satoriforms
from satori.tools.params import *

class ParamsDict(object):
    def __init__(self, xml_node):
        self.fields = []
        for n in xml_node.childNodes:
            if n.nodeName=="param":
                d = {}
                d["type"] = n.getAttribute("type")
                d["name"] = n.getAttribute("name")
                d["description"] = n.getAttribute("description")
                d["required"] = n.getAttribute("required")=="true"
                d["default"] = n.getAttribute("default")
                d["value"] = d["default"]
                self.fields.append(d)
                    
    def fill(self,par_map,groupname = None):
        for d in self.fields:
            attr = par_map.get(f["name"],None)
            if attr:
                if attr.is_blob:
                    d["filename"] = attr.filename
#                    d["getlink"] = ''
                d["value"] = attr.value
                        
    def dict_to_oa_map(self,dictionary):
        ret = OaMap()
        for d in self.fields:
            name = d["name"]
            value = dictionary.get(name,None)
            if d["type"]=='bool':
                dictionary[name] = bool(value)
                value = bool(value)
            if value==None:
                if d["required"]:
                    raise Exception("Attribute required.")        
                else:
                    continue
            if d["type"]=="blob":
                writer = ret.set_blob(name,value.size,value.name)
                writer.write(value.read())
                writer.close()
            elif d["type"]=="datetime":
                ret.set_str(name,value.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                ret.set_str(name,str(value))
        return ret
                

def ParseXML(string):
    ret = {}
    tree = minidom.parseString(string)
    for s in tree.firstChild.childNodes:
        if s.nodeType==minidom.Node.ELEMENT_NODE:
            ret[s.nodeName] = ParamsDict(s)
    return ret
    
class ParamsForm(forms.Form):
    fieldtypes = {
                    'text'  : forms.CharField,
                    'size'  : forms.CharField,
                    'time'  : forms.CharField,
                    'int'   : forms.IntegerField,
                    'float' : forms.FloatField,
                    'datetime'  : satoriforms.SatoriDateTimeField,
                    'bool'  : forms.BooleanField,
                    'blob'  : forms.FileField 
                 }
                
    def __init__(self,paramsdict,oamap=None,*args,**kwargs):
        data = {}
        if oamap:
            for f in paramsdict.fields:
                ftype =f['type']
                name = f['name']
                if not name in oamap.keys():
                    continue
                attr = oamap[name]
                val = attr.value
                if ftype=='datetime':
                    data[name] = datetime.strptime(attr.value,"%Y-%m-%d %H:%M:%S")
                elif ftype=='bool':
                    data[name] = (val=='True' or val=='true' or val=='Yes' or val=='yes' or val==1 or val=='1')
                else:
                    data[name] = attr.value
        super(ParamsForm,self).__init__(initial=data,*args,**kwargs)
        for f in paramsdict.fields:
            ftype = ParamsForm.fieldtypes[f['type']]
            if f['type']=='bool':
                req = False
            else:
                req = f['required']
            self.fields[f['name']] = ftype(label=f['description'],required=req,initial=f['default'])


class ParamsForm2(forms.Form):
    fieldtypes = {
                    OaTypeText  : forms.CharField,
                    OaTypeSize  : forms.CharField,
                    OaTypeTime  : satoriforms.SatoriTimedeltaField,
                    OaTypeInteger   : forms.IntegerField,
                    OaTypeFloat : forms.FloatField,
                    OaTypeDatetime  : satoriforms.SatoriDateTimeField,
                    OaTypeBoolean  : forms.BooleanField,
#                    OaTypeBlob  : forms.FileField 
                 }
    def __init__(self,parser,*args,**kwargs):
        super(ParamsForm2,self).__init__(*args,**kwargs)
        for f in parser.params:
            ftype = ParamsForm2.fieldtypes[f.type_]
            if f.type_=='bool':
                req = False
            else:
                req = f.required
            self.fields[f.name] = ftype(label=f.description,required=req)
    