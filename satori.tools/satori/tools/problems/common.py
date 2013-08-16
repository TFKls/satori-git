# vim:ts=4:sts=4:sw=4:et
import os.path
import re
import sys
import unicodedata

from satori.client.common import want_import
want_import(globals(), '*')


def slugify(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    s = re.sub('[^\w\s-]', '', s).strip().lower()
    s = re.sub('[-\s]+', '-', s)
    return s


class Dirs(object):
    def __init__(self, problem_dir, test_dir):
        self._problem_dir = problem_dir
        self._test_dir = test_dir
    def parse(self, path):
        if path[:1] == '/':  # 'absolute' path 
            return os.path.join(self._problem_dir, path[1:])
        else:  # relative path
            return os.path.join(self._test_dir, path)        


def copy_file(src, dst):
    BUF_SIZ = 16 * 1024
    while True:
        buf = src.read(BUF_SIZ)
        if not buf:
            break
        dst.write(buf)


def upload_blob(blob_path):
    with open(blob_path) as local_blob:
        blob_size = os.path.getsize(blob_path)
        remote_blob = Blob.create(blob_size)
        print 'Uploading blob', os.path.basename(blob_path) + ',',
        print 'size =', blob_size, 'bytes' + '...',
        sys.stdout.flush()
        copy_file(local_blob, remote_blob)
        print 'done'
    blob_hash = remote_blob.close()
    blob_name = os.path.basename(blob_path)
    return AnonymousAttribute(is_blob=True, value=blob_hash, filename=blob_name)

