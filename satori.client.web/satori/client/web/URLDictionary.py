# Module for conversions URL <-> dictionary

import re

# creates a dictionary from first half of URL

class Session:
    user = ''
    pass

def ParseURL(argstr):
    res = {}
    pos = 0
    length = len(argstr)
    while pos<length:
        if argstr[pos]==',':
            pos = pos+1
        m = re.match("(?P<key>[a-zA-Z0-9_]*)\|",argstr[pos:])
        key = m.group("key")
        pos = pos+m.end()
        res[key]= []
        while pos<length and argstr[pos]!=',':
            if argstr[pos]=='+':
                pos = pos+1
            if argstr[pos]!='(':
                m = re.match("(?P<val>[a-zA-Z0-9_]*)",argstr[pos:])
                pos = pos+m.end()
                res[key].append(m.group("val"))
            else:
                k = pos+1
                counter = 1
                while k<length and counter!=0:
                    if argstr[k]=='(':
                        counter = counter+1
                    if argstr[k]==')':
                        counter = counter-1
                    k = k+1
                res[key].append(ParseURL(argstr[pos+1:k-1]))
                pos = k
    return res

# turns dictionary into URL
    
def ToString(dict):
    s = ""
    for key, value in dict.iteritems():
        s = s+key
        s = s+'|'
        for v in value:
            if type(v).__name__=='dict':
                s = s+'('+ToString(v)+')'+'+'
            else:
                s = s+v+'+'
        s = s[:-1]
        s = s+','
    s = s[:-1]
    return s;
    
# just for concatenating two URL halves 
    
def GetLink(dict, path):
    return ToString(dict)+"."+path;

# if path is nontrivial, returns a descendant dictionary        
        
def follow(dict, pathstr):
    d = dict
    if not pathstr or len(pathstr)==0:
        return d;
    path = re.split("\|",pathstr)
    for i in range(0,len(path)):
        m = re.match("(?P<name>[a-zA-Z0-9_]*)\((?P<index>[0-9]*)\)",path[i])
        d = d[m.group("name")][int(m.group("index"))]
    return d

