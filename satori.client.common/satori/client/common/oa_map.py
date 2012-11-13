# vim:ts=4:sts=4:sw=4:expandtab

from copy import deepcopy
import os

def get_oa_map(Attribute, AnonymousAttribute, BadAttributeType, Blob):
    class OaMap(object):
        def __init__(self, dct={}):
            self.dct = deepcopy(dct)

        def get(self, name):
            if not name in self.dct:
                return None
            attr = self.dct[name]
            return Attribute(name=name, is_blob=attr.is_blob, value=attr.value, filename=attr.filename)

        def get_str(self, name):
            oa = self.get(name)
            if oa is None:
                return None
            elif oa.is_blob:
                raise BadAttributeType(name=name, required_type='string')
            else:
                return oa.value

        def get_blob(self, name):
            oa = self.get(name)
            if oa is None:
                return None
            elif not oa.is_blob:
                raise BadAttributeType(name=name, required_type='blob')
            return Blob.open(oa.value, oa.filename)

        def get_blob_hash(self, name):
            oa = self.get(name)
            if oa is None:
                return None
            elif not oa.is_blob:
                raise BadAttributeType(name=name, required_type='blob')
            else:
                return oa.value

        def get_blob_filename(self, name):
            oa = self.get(name)
            if oa is None:
                return None
            elif not oa.is_blob:
                raise BadAttributeType(name=name, required_type='blob')
            else:
                return oa.filename

        def get_blob_path(self, name, path):
            return Blob.open_path(self.get_blob_hash(name), path)

        def get_list(self):
            return [self.get(name) for name in self.dct]

        def get_map(self):
            return deepcopy(self.dct)

        def set(self, value):
            attr = self.dct.setdefault(value.name, AnonymousAttribute())
            attr.is_blob = value.is_blob
            attr.value = value.value
            if attr.is_blob and hasattr(value, 'filename') and value.filename is not None:
                attr.filename = value.filename
            else:
                attr.filename = ''

        def set_str(self, name, value):
            self.set(Attribute(name=name, value=value, is_blob=False))

        def set_blob(self, name, length=-1, filename=''):
            # TODO
            def set_hash(hash):
                self.set(Attribute(name=name, value=hash, filename=filename, is_blob=True))
            return Blob.create(length, set_hash)

        def set_blob_hash(self, name, value, filename=''):
            self.set(Attribute(name=name, value=value, filename=filename, is_blob=True))

        def set_blob_path(self, name, path, filename=None):
            if filename is None:
                filename = os.path.basename(path)
            hash = Blob.create_path(path)
            self.set_blob_hash(name, hash, filename=filename)
            return hash

        def add_list(self, attributes):
            for struct in attributes:
                self.set(struct)

        def set_list(self, attributes):
            sel.dct = {}
            self.add_list(attributes)

        def add_map(self, attributes):
            for name, struct in attributes.items():
                struct.name = name
                self.set(struct)

        def set_map(self, attributes):
            sel.dct = {}
            self.add_map(attributes)

        def delete(self, name):
            if name in self.dct:
                del self.dct[name]
    return OaMap
