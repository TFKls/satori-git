from django import forms


class SatoriSplitDateTime(forms.SplitDateTimeWidget):
    class Media:
        css = { 'all' : ('/files/calendar/css/jquery.datepick.css',) }
        js = ("http://ajax.googleapis.com/ajax/libs/jquery/1.4.4/jquery.min.js","/files/calendar/js/jquery.datepick.js","/files/calendar/js/datepick.init.js")
    def __init__(self, attrs=None):
        super(SatoriSplitDateTime,self).__init__(attrs=attrs)
        self.widgets[0].attrs = {'class': 'SatoriDateField', 'size': '10'}
        self.widgets[1].attrs = {'class': 'SatoriTimeField', 'size': '8'}


