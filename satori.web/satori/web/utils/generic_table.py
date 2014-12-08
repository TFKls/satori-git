class GenericTable(object):
    def __init__(self,prefix='',request_get={}):
        self.my_params = {}             # GET parameters that apply to me
        self.other_params = {}          # other GET parameters
        self.prefix = prefix            # prefix that distinguishes me from other tables
        self.rows = []                  # rows being served to template
        self.data = []                  # data in raw format
        self.fields = []                # fields to show as columns
        self.filters = {}
        self.default_shown = 30         # default number of results to show
        self.page = 1
        self.sortfield = None
        self.default_sortfield = None
        
        for key, value in request_get.iteritems():
            if (key.startswith(prefix+'_')):
                self.my_params[key[len(prefix)+1:]] = value
            else:
                self.other_params[key] = value

        
    # Generates a dictionary with (mostly) the same GET parameters, subst_my and subst_other tell which parameters should be changed        
    def params_subst_dict(self, subst_my = {}, subst_other = {}, deleted_my = [], deleted_other = []):
        my_params_new = self.my_params.copy()
        my_params_new.update(subst_my)
        for key in deleted_my:
            my_params_new.pop(key,None)
        other_params_new = self.other_params.copy()
        other_params_new.update(subst_other)
        for key in deleted_other:
            other_params_new.pop(key,None)
        joined = {self.prefix+'_'+unicode(key) : unicode(value) for key,value in my_params_new.iteritems()}
        joined.update(other_params_new)
        return joined

    # Like above, but returns a GET link
    def params_subst_link(self, subst_my = {}, subst_other = {}, deleted_my = [], deleted_other = []):
        return '?'+('&'.join([key + '='+ value for key, value in self.params_subst_dict(subst_my,subst_other, deleted_my, deleted_other).iteritems()]))
    
    # Provides filters with "field contains substring" condition
    def filter_by_fields(self, filtered_fields_list):
        self.filtered_fields_list = filtered_fields_list
        self.filter_field = self.my_params.get('filter_field',None)
        self.filter_method = self.my_params.get('filter_method','starts')
        self.filter_string = self.my_params.get('filter_string','')
        if self.filter_field in self.filtered_fields_list:
            if self.filter_method=='contains':
                self.data = [ row for row in self.data if row[self.filter_field].find(self.filter_string)!=-1 ]
            if self.filter_method=='starts':
                self.data = [ row for row in self.data if row[self.filter_field].startswith(self.filter_string) ]
        self.params_nofilter = self.params_subst_dict(deleted_my = ['filter_field','filter_method','filter_string'])
            
    # Provides automatic sorting by a column given as 'sort' parameter
    def autosort(self):
        self.sortfield = self.my_params.get('sort',self.default_sortfield)
        self.direction = (self.my_params.get('direction','asc'))
        if self.direction!= 'asc' and self.direction!= 'desc':
            self.direction = 'asc'
        self.data.sort(key=lambda row : row.get(self.sortfield,None), reverse = (self.direction=='desc'))
            
    # Clips data to the range given by 'page' and 'show' parameters
    def autopaginate(self):
        try:
            self.show = int(self.my_params['show'])
        except:
            self.show = self.default_shown
        if self.show <= 0:              # setting show=0 would be a nice practical joke, as we are soon going to divide by it
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
        self.rows = self.data[self.start : self.start + self.show]

    # Generates links to other parts of data. Needs self.total_pages set.
    def autopagelinks(self, width = 10):
        start = max(1,self.page-width/2)
        end = min(self.total_pages+1,start+width+1)
        return [[i,self.params_subst_link({'page' : i})] for i in range(start,end)]

    def autopagelink_first(self):
        return self.params_subst_link({'page' : 1})
    
    def autopagelink_last(self):
        return self.params_subst_link({'page' : self.total_pages})
    
    