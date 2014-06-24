from six import print_
# vim:ts=4:sts=4:sw=4:et
import base64
import glob
import hashlib
import os.path
import re
import sys
import unicodedata
import yaml

from satori.client.common import want_import
want_import(globals(), '*')

from satori.tools.params import parser_from_xml

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


def _calculate_blob_hash(blob_path):
    with open(blob_path) as blob:
        # TODO: use a buffer to avoid unbounded memory usage
        return base64.urlsafe_b64encode(hashlib.sha384(blob.read()).digest())


def upload_blob(blob_path):
    blob_hash = _calculate_blob_hash(blob_path)
    if not Blob.exists(blob_hash):
        with open(blob_path) as local_blob:
            blob_size = os.path.getsize(blob_path)
            remote_blob = Blob.create(blob_size)
            print_('Uploading blob', os.path.basename(blob_path) + ',', end="")
            print_('size =', blob_size, 'bytes' + '...', end="")
            sys.stdout.flush()
            copy_file(local_blob, remote_blob)
            print_('done')
        remote_blob_hash = remote_blob.close()
        assert blob_hash == remote_blob_hash
    blob_name = os.path.basename(blob_path)
    return AnonymousAttribute(is_blob=True, value=blob_hash, filename=blob_name)


def make_oa_map(params_parser, yaml_data, dirs):
    if not params_parser or not params_parser.params:
        return {}
    oa_map = {}
    for param in params_parser.params:
        if param.name in yaml_data:
            if param.type_.name() == 'blob':
                oa_map[param.name] = upload_blob(dirs.parse(yaml_data[param.name]))
            else:
                oa_map[param.name] = AnonymousAttribute(is_blob=False, value=yaml_data[param.name])
        else:
            if param.required and param.default is None:
                raise RuntimeError(
                        'Required param %s not specified' % param.name)
    return oa_map


def open_test(test_yaml_fname):
    with open(test_yaml_fname) as test_yaml_file:
        test_yaml = yaml.safe_load(test_yaml_file)
    if type(test_yaml) != dict:
        raise RuntimeError('Test YAML must be an object')
    test_name = os.path.basename(os.path.dirname(test_yaml_fname))
    if 'name' in test_yaml:
        if test_yaml['name'] != test_name:
            raise RuntimeError('Test name does not match directory name')
    else:
        test_yaml['name'] = test_name
    return test_yaml


def make_test_data(dirs, overrides=[]):
    test_yaml = open_test(dirs.parse('test.yaml'))  # path relative to test dir
    if overrides:    
        for override in overrides:
            k, v = override.split('=', 2)
            test_yaml[k] = v
    test_name = test_yaml['name']
    test_description = test_yaml.get('description', '')

    if 'judge' not in test_yaml:
        raise RuntimeError('No judge specified')

    judge_path = dirs.parse(test_yaml['judge'])
    with open(judge_path) as judge_file:
        judge_content = judge_file.read()

    judge_params = parser_from_xml(judge_content)
    test_data = make_oa_map(judge_params, test_yaml, dirs)
    test_data['name'] = AnonymousAttribute(is_blob=False, value=test_name)
    test_data['description'] = AnonymousAttribute(is_blob=False,
                                                  value=test_description)
    test_data['judge'] = upload_blob(judge_path)

    return test_data


def discover_tests(problem_dir):
    tests = []
    for fname in glob.glob(os.path.join(problem_dir, '*', 'test.yaml')):
        test_yaml = open_test(fname)
        tests.append((test_yaml['name'], os.path.dirname(fname)))
    return dict(tests)

