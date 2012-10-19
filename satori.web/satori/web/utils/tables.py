from copy import deepcopy

# Copied from django/utils/html.py
# TODO(robryk): Remove once we start using a version of Django that includes these
from django.utils.html import conditional_escape, mark_safe
def format_html(format_string, *args, **kwargs):
    """
    Similar to str.format, but passes all arguments through conditional_escape,
    and calls 'mark_safe' on the result. This function should be used instead
    of str.format or % interpolation to build up small HTML fragments.
    """
    args_safe = map(conditional_escape, args)
    kwargs_safe = dict([(k, conditional_escape(v)) for (k, v) in
                        kwargs.iteritems()])
    return mark_safe(format_string.format(*args_safe, **kwargs_safe))

def format_html_join(sep, format_string, args_generator):
    """
    A wrapper format_html, for the common case of a group of arguments that need
    to be formatted using the same format string, and then joined using
    'sep'. 'sep' is also passed through conditional_escape.

    'args_generator' should be an iterator that returns the sequence of 'args'
    that will be passed to format_html.

    Example:

      format_html_join('\n', "<li>{0} {1}</li>", ((u.first_name, u.last_name)
                                                  for u in users))

    """
    return mark_safe(conditional_escape(sep).join(
            format_html(format_string, *tuple(args))
            for args in args_generator))

class FilterFunction(object):
    def __init__(self, prefix, name='', choices=[], check=(lambda table, i, value : True),default=None,showall=True):
        self.check = check
        self.choices = choices
        if showall:
            self.choices = [['disable_filter','-------']]+self.choices
        self.name = name
        self.prefix = prefix
        self.default = default

class TableField(object):
    def __init__(self,id,name,sortable=True,value=(lambda table,i: unicode(i)+'th value'),render=None,filter=None,choices=[],css=None):
            
        if render == None:
            render = value
            
        self.id = unicode(id)
        self.name = name
        self.sortable = sortable
        self.render = render
        self.value = value
        self.filter = filter
        self.choices = choices
        self.css = css
        
    def class_string(self):
        if isinstance(self.css,str) or isinstance(self.css,unicode):
            self.css=[self.css]
        if self.css:
            return format_html(u' class="{0}"', ' '.join(self.css))
        else:
            return ''
        
class ResultTable(object):

    def length(self):
        return len(self.results)
    
    @staticmethod
    def default_limit():
        return 0
                    
    def __init__(self, req = {}, prefix='', autosort=True, default_sort=None, default_desc=False):
        self.results = []
        self.params = {}
        self.filters = {}
        self.filter_functions = []
        self.other = {}
        self.total = 0
        self.prefix = prefix
        self.autosort = autosort
        self.fields = []
        
        for k in req.keys():
            if k.find(prefix)==0:
                self.params[k[len(prefix)+1:]] = req[k]
            else:
                self.other[k] = req[k]
        for k in self.params.keys():
            if k.find('filter')==0:
                if self.params[k]!='disable_filter':
                    self.filters[k[7:]] = self.params[k]
                del self.params[k]
                
        if 'page' not in self.params.keys():
            self.params['page'] = 1
        else:
            self.params['page'] = int(self.params['page'])
        if self.params['page'] <= 0:
            self.params['page'] = 1
            
        if 'limit' not in self.params.keys():
            self.params['limit'] = self.default_limit()
        else:
            self.params['limit'] = int(self.params['limit'])
        if self.params['limit'] < 0:
            self.params['limit'] = self.default_limit()
        if 'sort' not in self.params.keys() and default_sort:
            self.params['sort'] = unicode(default_sort)
            if default_desc:
                self.params['order'] = 'desc'

    def add_autofilter(self,field):
        def autocheck(table,i,v):
            return v!='disable_filter' and field.value(table,i)==v
        choices = []
        for i in range(0,self.length()):
            choices.append(field.value(self,i))
        choices.sort()
        choices = [ [choices[i],choices[i]] for i in range(0,len(choices)) if i==0 or choices[i]!=choices[i-1]]
        self.filter_functions.append(FilterFunction(name=field.name,prefix=unicode(field.id),choices=choices,check=autocheck))
        
    def getparams(self,filters={},**kwargs):
        p = deepcopy(self.params)
        for key in kwargs:
            p[key] = kwargs[key]
        for key in filters:
            p['filter_'+key] = filters[key]            
        for key in self.filters:
            if not key in filters.keys():
                p['filter_'+key] = self.filters[key]
        return '?'+'&'.join([self.prefix+'_'+unicode(k)+'='+unicode(v) for (k,v) in p.iteritems()])
        
    def render_header(self):
        def sort_link(f):
            if self.params.get('sort',None)!=unicode(f.id) or self.params.get('order',None)=='desc':
                return self.getparams(sort=f.id,order='asc')
            return self.getparams(sort=f.id,order='desc')
        def header(f):
            if self.autosort and f.sortable:
                return format_html(u'<a class="stdlink" href="{0}">{1}</a>', sort_link(f), f.name)
            else:
                return f.name
        s = format_html_join(u'', u'<th>{0}</th>', [(header(f),) for f in self.fields])
        return format_html(u'<tr>{0}</tr>', s)
        
    def render_row(self,i):
        s = format_html_join(u'', u'<td{0}>{1}</td>', [(f.class_string(), f.render(self,i)) for f in self.fields])
        return format_html(u'<tr>{0}</tr>', s)
        
    def render_table(self):
        f_key = None
        order = []
        for i in range(0,self.length()):
            ok = True
            for ff in self.filter_functions:
                v = self.filters.get(ff.prefix,ff.default)
                if v and not ff.check(self,i,v):
                    ok = False
            for f in self.fields:
                if f.filter=='auto' and unicode(f.id) in self.filters.keys() and self.filters[f.id]!='disable_filter' and f.value(self,i)!=self.filters[f.id]:
                    ok = False
            if ok:
                order.append(i)
        if 'sort' in self.params.keys():
            for f in self.fields:
                if unicode(f.id) == self.params['sort']:
                    f_key = f
        if self.autosort and f_key:
            order.sort(key=lambda i: f_key.value(self,i),reverse=(self.params.get('order',None)=='desc'))
        limit = self.params['limit']
        page = self.params['page']
        if self.autosort and limit>0:
            order = order[(page-1)*limit:page*limit]
        s = format_html_join(u'', u'{0}', [(self.render_row(i),) for i in order])
        return format_html(u'{0}{1}', self.render_header(), s)
        
    def render_scrollbar(self):
        limit = self.params['limit']
        if limit==0:
            return ''
        page = self.params['page']
        tpages = (self.total+limit-1)/limit + 1
        def render_wheelitem(i):
            if i == page:
                return format_html(u'<span class="wheelsel">{0}</span>', i)
            else:
                return format_html(u'<a class="wheelitem" href="{0}">{1}</a>',self.getparams(page=i), i)
        s = format_html_join(u'', u'{0}', [(render_wheelitem(i),) for i in range(1, tpages)])
        return format_html(u'<div class="wheel">{0}</div>', s)

    def render_filters(self):
        s = '<form action="" method="GET">'
        s += ''.join(['<input type="hidden" name="'+self.prefix+'_'+unicode(k)+'" value="'+unicode(v)+'"/>' for (k,v) in self.params.iteritems() if k!='page'])
        s += ''.join(['<input type="hidden" name="'+unicode(k)+'" value="'+unicode(v)+'"/>' for (k,v) in self.other.iteritems()])
        for ff in self.filter_functions:
            current = self.filters.get(ff.prefix,None)
            s += ff.name+': <select name="'+self.prefix+'_filter_'+ff.prefix+'">'
            for v in ff.choices:
                s += '<option value="'+unicode(v[0])+'"'
                if current and unicode(v[0])==unicode(current):
                    s+='selected'
                s += ' >'+ unicode(v[1])+'</option>'
            s += '</select>'
            
        for f in self.fields:
            if f.filter=='custom':
                current=self.filters.get(unicode(f.id),None)
                s += f.name+': <select name="'+self.prefix+'_filter_'+unicode(f.id)+'">'
                s += '<option value="disable_filter">Show all</option>'
                for v in f.choices:
                    s += '<option value="'+unicode(v[1])+'"'
                    if unicode(v[1])==current:
                        s+='selected'
                    s += ' >'+ unicode(v[0])+'</option>'
                s += '</select>'
            
        s += '<input type="submit" class="button" value="Filter"/></form>'
        # FIXME(robryk): Make this saner, although this doesn't seem to be a vulnerability now.
        return mark_safe(s)
        
