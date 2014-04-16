class GenericTable(object):
    def __init__(self,prefix='',request_get={}):
        self.my_params = {}             # GET parameters that apply to me
        self.other_params = {}          # other GET parameters
        self.prefix = prefix            # prefix that distinguishes me from other tables
        self.rows = []                  # rows being served to template
        self.data = []
        self.filters = {}
        self.default_shown = 10
        self.page = 1
        self.default_sortfield = None
        
        for key, value in request_get.iteritems():
            if (key.startswith(prefix+'_')):
                self.my_params[key[len(prefix)+1:]] = value
            else:
                self.other_params[key] = value

    # Generates a link with (mostly) the same GET parameters, subst_my and subst_other tell which parameters should be changed        
    def params_subst_link(self, subst_my = {}, subst_other = {}):
        my_params_new = self.my_params.copy()
        my_params_new.update(subst_my)
        my_params_link = [self.prefix+'_'+str(key)+'='+str(value) for key,value in my_params_new.iteritems()]
        other_params_new = self.other_params.copy()
        other_params_new.update(subst_other)
        other_params_link = [str(key)+'='+str(value) for key,value in other_params_new.iteritems()]
        return '?'+('&'.join(my_params_link+other_params_link))

    def params_subst_dict(self, subst_my = {}, subst_other = {}):
        my_params_new = self.my_params.copy()
        my_params_new.update(subst_my)
        other_params_new = self.other_params.copy()
        other_params_new.update(subst_other)
        joined = {self.prefix+'_'+str(key) : str(value) for key,value in my_params_new.iteritems()}
        joined.update(other_params_new)
        return joined
    
            
    # Provides automatic sorting by a column given as 'sortfield' parameters
    def autosort(self):
        sorted_field = self.my_params.get('sortfield',self.default_sortfield)

        self.data.sort(key=lambda row : row.get(sorted_field,None))
        
    # Clips data to the range given by 'page' and 'show' parameters
    def autopaginate(self):
        try:
            self.show = int(self.my_params['show'])
        except:
            self.show = self.default_shown
        if self.show <= 0:              # setting show=0 would be a nice practical joke 'cause of dividing by it later
            self.show = self.default_shown
        self.total_pages = (len(self.data) + self.show - 1)/self.show
        try:
            self.page = int(self.my_params['page'])
        except:
            self.page = 1
        if self.page<1:
            self.page = 1
        if self.page>self.total_pages:
            self.page = self.total_pages
        self.start = (self.page-1)*self.show
        self.data = self.data[self.start : self.start + self.show]

    # Generates links to other parts of data. Needs self.total_pages set.
    def autopagelinks(self, width = 10):
        start = max(1,self.page-width/2)
        end = min(self.total_pages+1,start+width+1)
        return [[i,self.params_subst_link({'page' : i})] for i in range(start,end)]

    def autopagelink_first(self):
        return self.params_subst_link({'page' : 1})
    
    def autopagelink_last(self):
        return self.params_subst_link({'page' : self.total_pages})
    
    