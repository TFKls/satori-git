from satori.client.common import want_import
want_import(globals(), '*')
from datetime import datetime
from xml.dom import minidom
from django import forms
from satori.web.utils import forms as satoriforms
from satori.tools.params import *


class ParamsForm(forms.Form):
    fieldtypes = {
                    OaTypeText  : forms.CharField,
                    OaTypeSize  : satoriforms.SatoriSizeField,
                    OaTypeTime  : satoriforms.SatoriTimedeltaField,
                    OaTypeInteger   : forms.IntegerField,
                    OaTypeFloat : forms.FloatField,
                    OaTypeDatetime  : satoriforms.SatoriDateTimeField,
                    OaTypeBoolean  : forms.BooleanField,
#                    OaTypeBlob  : forms.FileField 
                 }
    def __init__(self,parser,*args,**kwargs):
        super(ParamsForm,self).__init__(*args,**kwargs)
        for f in parser.params:
            ftype = ParamsForm.fieldtypes[f.type_]
            if f.type_=='bool':
                req = False
            else:
                req = f.required
            self.fields[f.name] = ftype(label=f.description,required=req)
    