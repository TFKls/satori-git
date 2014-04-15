class GenericTable(object):
    def __init__(self,prefix='',request_get={}):
        self.my_params = {}             # GET parameters that apply to me
        self.other_params = {}          # other GET parameters
        self.prefix = prefix            # prefix that distinguishes me from other tables
        self.rows = []                  # rows being served to template
        self.data = []
        self.filters = {}
        self.default_shown = 30
        self.default_sortfield = None
        
        for key, value in request_get.iteritems():
            if (key.startswith(prefix+'_')):
                self.my_params[key[len(prefix)+1:]] = value
            else:
                self.other_params[key] = value
        
    def params_subst_link(self, subst_my, subst_other):
        my_params_link = [prefix+'_'+str(key)+'='+str(value) for key,value in self.my_params.copy().update(subst_my).iteritems()]
        other_params_link = [str(key)+'='+str(value) for key,value in self.other_params.copy().update(subst_other).iteritems()]
        return '?'+('&'.join(my_params_link+other_params_link))
            
    def autosort(self):
        sorted_field = self.my_params.get('sortfield',self.default_sortfield)
        self.data.sort(key=lambda row : row.get(sorted_field,None))

    def autopaginate(self):
        start = int(self.my_params.get('start',0))
        show = int(self.my_params.get('show',self.default_shown))
        self.data = self.data[start:start+show]
    