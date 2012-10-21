from django import forms
from django.db import models
from datetime import datetime
from satori.tools.params import OaTypeTime
from copy import deepcopy
from satori.web.utils.tables import format_html

class StatusBar():
    def __init__(self):
        self.messages = []
        self.errors = []
        self.msgclass = 'bar_message'
        self.errclass = 'bar_error'

class SatoriSplitDateTime(forms.SplitDateTimeWidget):
    class Media:
        css = { 'all' : ('/files/calendar/css/jquery.datepick.css',) }
        js = ("/files/jquery.min.js","/files/calendar/js/jquery.datepick.js","/files/calendar/js/datepick.init.js")
    def __init__(self, attrs=None):
        super(SatoriSplitDateTime,self).__init__(attrs=attrs)
        self.widgets[0].attrs = {'class': 'SatoriDateField', 'size': '10'}
        self.widgets[1].attrs = {'class': 'SatoriTimeField', 'size': '8'}

class SatoriDateTimeField(forms.DateTimeField):
    def __init__(self,*args,**kwargs):
        super(SatoriDateTimeField,self).__init__(widget=SatoriSplitDateTime,*args,**kwargs)

class SatoriTimedeltaWidget(forms.TextInput):
    def render(self,name,value,attrs=None):
        try:
            value = OaTypeTime._to_unicode(value)
        except:
            pass
        return super(SatoriTimedeltaWidget,self).render(name,value,attrs)

class SatoriTimedeltaField(forms.CharField):
    def __init__(self,*args,**kwargs):
        super(SatoriTimedeltaField,self).__init__(widget=SatoriTimedeltaWidget,*args,**kwargs)
    def to_python(self,value):
        try: 
            return OaTypeTime._from_unicode(value)
        except:
            raise forms.ValidationError('Invalid time format.')
    def clean(self,value):
        return self.to_python(value)



class SatoriSizeWidget(forms.TextInput):
    def render(self,name,value,attrs=None):
        try:
            value = OaTypeSize._to_unicode(value)
        except:
            pass
        return super(SatoriSizeWidget,self).render(name,value,attrs)

class SatoriSizeField(forms.CharField):
    def __init__(self,*args,**kwargs):
        super(SatoriSizeField,self).__init__(widget=SatoriSizeWidget,*args,**kwargs)
    def to_python(self,value):
        try: 
            return OaTypeSize._from_unicode(value)
        except:
            raise forms.ValidationError('Invalid size format.')
    def clean(self,value):
        return self.to_python(value)


def RenderObjectButton(id, name, buttonname, css='button'):
    return format_html(u'<form action="" method="POST"><input type="submit" class="{0}" name="{1}" value="{2}"><input type="hidden" name="id" value="{3}"/></form>', css, name, buttonname, id)

