# -*- coding: utf-8 -*-
# vim:ts=4:sts=4:sw=4:expandtab

from xml.dom import minidom
from datetime import datetime, timedelta

from satori.objects import Namespace

def total_seconds(value):
    return float(value.microseconds + (value.seconds + value.days * 24 * 3600) * 10**6) / 10**6

class OaType(object):
    @classmethod
    def name(cls, value):
        raise NotImplemented
    @classmethod
    def value_type(cls):
        raise NotImplemented
    @classmethod
    def cast(cls, value):
        if isinstance(value, cls.value_type()):
            return value
        return cls.value_type()(value)
    @classmethod
    def _from_unicode(cls, value):
        return cls.cast(value)
    @classmethod
    def from_unicode(cls, value):
        return cls.cast(cls._from_unicode(unicode(value)))
    @classmethod
    def _to_unicode(cls, value):
        return unicode(value)
    @classmethod
    def to_unicode(cls, value):
        return unicode(cls._to_unicode(cls.cast(value)))
    def __init__(self, value=None, str_value=None):
        if value is not None:
            self.str_value = self.__class__.to_unicode(value)
        else:
            self.str_value = str_value
    def value(self):
        return self.__class__.from_unicode(self.str_value)

class OaTypeText(OaType):
    @classmethod
    def name(cls):
        return 'text'
    @classmethod
    def value_type(cls):
        return unicode
 
class OaTypeBoolean(OaType):
    @classmethod
    def name(cls):
        return 'bool'
    @classmethod
    def value_type(cls):
        return bool
    @classmethod
    def _to_unicode(cls, value):
        if value:
            return 'true'
        return 'false'
    @classmethod
    def _from_unicode(cls, value):
        value = value.lower()
        if value == 'true' or value == 'yes' or value == '1':
            return True
        elif value == 'false' or value == 'no' or value == '0':
            return False
        raise ValueError
 
class OaTypeInteger(OaType):
    @classmethod
    def name(cls):
        return 'int'
    @classmethod
    def value_type(cls):
        return int
 
class OaTypeFloat(OaType):
    @classmethod
    def name(cls):
        return 'float'
    @classmethod
    def value_type(cls):
        return float
 
class OaTypeTime(OaType):
    scales = [ '', 'd', 'c', 'm', None, None, u'µ', None, None, 'n' ]
    large = [ (60, 'm'), (60*60, 'h'), (24*60*60, 'd'), (7*24*60*60, 'w') ]
    @classmethod
    def name(cls):
        return 'time'
    @classmethod
    def value_type(cls):
        return timedelta
    @classmethod
    def _to_unicode(cls, value):
        large = OaTypeTime.large
        value = total_seconds(value)
        res = u''
        for mul, suf in reversed(large):
            if value > mul:
                cnt = math.floor(value/mul)
                res += unicode(cnt)+suf
                value -= cnt*mul
        res += unicode(value) + 's'
        return res
    @classmethod
    def _from_unicode(cls, value):
        scales = OaTypeTime.scales
        large = OaTypeTime.large
        value = value.strip().lower()
        parts = []
        for part in value.split():
            found = False
            if not found:
                for s in reversed(range(0, len(scales))):
                    if scales[s] is not None and part.endswith(scales[s] + 's'):
                        parts.append(timedelta(seconds=float(part[:-1*(len(scales[s] + 's'))]) * 0.1**s))
                        found = True
                        break
            if not found:
                for mul, suf in large:
                    if part.endswith(suf):
                        parts.append(timedelta(seconds=float(part[:-1*(len(suf))]) * mul))
                        found = True
                        break
            if not found:
                parts.append(timedelta(seconds=float(value)))
        return sum(parts, timedelta())
    
class OaTypeSize(OaType):
    scales = [ '', 'K', 'M', 'G', 'T' ]
    @classmethod
    def name(cls):
        return 'size'
    @classmethod
    def value_type(cls):
        return int
    @classmethod
    def _to_unicode(cls, value):
        scales = OaTypeSize.scales
        for s in reversed(range(0, len(scales))):
            if scales[s] is not None and value % (1024**s) == 0:
                return unicode(value / (1024**s)) + scales[s] + 'B'
        return unicode(value)
    @classmethod
    def _from_unicode(cls, value):
        scales = OaTypeSize.scales
        value = value.strip().upper()
        for s in reversed(range(0, len(scales))):
            if scales[s] is not None and value.endswith(scales[s] + 'B'):
                return int(value[:-1*(len(scales[s] + 'B'))]) * 1024**s
        return int(value)

class OaTypeDatetime(OaType):
    @classmethod
    def name(cls):
        return 'datetime'
    @classmethod
    def value_type(cls):
        return datetime
    @classmethod
    def _to_unicode(cls, value):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    @classmethod
    def _from_unicode(cls, value):
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')

oa_types = {}
for item in globals().values():
    if isinstance(item, type) and issubclass(item, OaType) and (item != OaType):
        oa_types[item.name()] = item

class OaParam(object):
    def __init__(self, type_, name, description=None, required=False, default=None):
        if not (isinstance(type_, type) and issubclass(type_, OaType)):
            type_ = oa_types[type_]
        self.type_ = type_
        self.name = unicode(name)
        self.description = unicode(description)
        self.required = bool(required)
        if default is None:
            self.default = None
        else:
            self.default = type_.cast(default)
    def to_dom(self, doc):
        ele = doc.createElement('param')
        ele.setAttribute('type', self.type_.name())
        ele.setAttribute('name', self.name)
        if self.description:
            ele.setAttribute('description', self.description)
        if self.required:
            ele.setAttribute('required', 'true')
        if self.default is not None:
            ele.setAttribute('default', self.type_.to_unicode(self.default))
        return ele
    @staticmethod
    def from_dom(ele):
        if ele.tagName != 'param':
            raise ValueError
        type_ = oa_types[ele.getAttribute('type')]
        name = ele.getAttribute('name')
        description = None
        if ele.hasAttribute('description'):
            description = ele.getAttribute('description')
        required = False
        if ele.hasAttribute('required'):
            required = OaTypeBoolean.from_unicode(ele.getAttribute('required'))
        default = None
        if ele.hasAttribute('default'):
            default = type_.from_unicode(ele.getAttribute('default'))
        return OaParam(type_=type_, name=name, description=description, required=required, default=default)
    def to_unicode(self, value):
        return self.type_.to_unicode(value)
    def from_unicode(self, value):
        return self.type_.from_unicode(value)

class OaTypedParser(object):
    def __init__(self, params):
        self.params = params
    @staticmethod
    def from_dom(ele):
        params = []
        for param in ele.getElementsByTagNameNS('*', 'param'):
            params.append(OaParam.from_dom(param))
        return OaTypedParser(params)
    def read_oa_map(self, oa_map):
        result = Namespace()
        for param in self.params:
            value = param.default
            if param.name in oa_map:
                value = param.from_unicode(oa_map[param.name].value)
            if param.required and value is None:
                raise ValueError
            result[param.name] = value
        return result
    def write_oa_map(self, dct):
        result = {}
        for param in self.params:
            if param.name in dct:
                oa = Namespace()
                oa['is_blob'] = False
                os['value'] = param.to_unicode(dct[param.name])
                result[param.name] = oa
            else:
                if param.required and param.default is None:
                    raise ValueError
        return result

def parse_params(description, section, subsection, oa_map):
    result = Namespace()
    if not description:
        return result
    xml = minidom.parseString(u' '.join([line[2:] for line in description.splitlines() if line[0:2] == '#@']))
    if not xml:
        return result
    xml = xml.getElementsByTagNameNS('*', section)
    if not xml:
        return result
    xml = xml[0].getElementsByTagNameNS('*', subsection)
    parser = OaTypedParser.from_dom(xml[0])
    return parser.read_oa_map(oa_map)

def set_params(description, section, subsection, data):
    result = {}
    if not description:
        return result
    xml = minidom.parseString(u' '.join([line[2:] for line in description.splitlines() if line[0:2] == '#@']))
    if not xml:
        return result
    xml = xml.getElementsByTagNameNS('*', section)
    if not xml:
        return result
    xml = xml[0].getElementsByTagNameNS('*', subsection)
    parser = OaTypedParser.from_dom(xml[0])
    return parser.write_oa_map(data)
