from django import forms
from datetime import datetime


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
