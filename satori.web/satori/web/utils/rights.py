from satori.client.common import want_import
from django import forms
want_import(globals(),'*')

class RightsTower(object):
    def length(self):
        return len(self.choices)
    def __init__(self,label):
        self.roles = []
        self.objects = []
        self.rights = []
        self.choices = []
        self.label = label
        self.current = None
    def add(self,role,object,right,title):
        self.roles.append(role)
        self.objects.append(object)
        self.rights.append(right)
        self.choices.append(title)
    def check(self):
        for i in range(0,self.length()):
            if not self.roles[i] or Privilege.get(self.roles[i],self.objects[i],self.rights[i]):
                self.current = i
                return i
        return None
    def set(self,key):
        k = int(key)
        for i in range(0,self.length()):
            if self.roles[i]:
                Privilege.revoke(self.roles[i],self.objects[i],self.rights[i])
        if self.roles[k]:
            Privilege.grant(self.roles[k],self.objects[k],self.rights[k])
    def field(self):
        return forms.ChoiceField(label=self.label,choices=reversed([[unicode(i),self.choices[i]] for i in range(0,self.length())]))
