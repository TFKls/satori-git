# -*- coding: utf-8 -*-
# vim:ts=4:sts=4:sw=4:expandtab

import datetime
import os
import resource
import stat
import sys
import shutil
import tempfile
import time
import subprocess
import traceback
import subprocess


def comper():
#1 - first file, 2 - second file, 3 - block size

    file_1 = str(sys.argv[1])
    file_2 = str(sys.argv[2])
    min_block = int(sys.argv[3])
    if min_block < 10:
        min_block = 10

    cw = os.getcwd()
    tmpc = tempfile.mkdtemp()
    os.chdir(tmpc)
    try:
        inc1cpp = os.path.join(tmpc, 'inc1.cpp')
        inc2cpp = os.path.join(tmpc, 'inc2.cpp')
        inc1pre = os.path.join(tmpc, 'inc1.pre')
        inc2pre = os.path.join(tmpc, 'inc2.pre')
        prex1 = os.path.join(tmpc, 'file_1.prex')
        prex2 = os.path.join(tmpc, 'file_2.prex')
        inc1cpp_file = open(inc1cpp, "w")
        inc2cpp_file = open(inc2cpp, "w")
        inc1pre_file = open(inc1pre, "w")
        inc2pre_file = open(inc2pre, "w")
        prex1_file = open(prex1, "w")
        prex2_file = open(prex2, "w")
        file_1_f = open(file_1, "w")
        file_1_f = open(file_2, "w")


        subprocess.Popen(['grep',' -e \"^[ \\t]*#\"',file_1], stdout = inc1cpp_file)

        subprocess.Popen(['grep',' -e \"^[ \\t]*#\"',file_2], stdout = inc2cpp_file)

        subprocess.Popen(['parseClang', inc1cpp], stdout = inc1pre_file)

        subprocess.Popen(['parseClang', inc2cpp], stdout = inc2pre_file)

        subprocess.Popen(['parseClang', file_1], stdout = file_1_f)

        subprocess.Popen(['parseClang', file_2], stdout = file_2_f)


        subprocess.Popen(['dd', 'if=' + file_1, 'bs=1', 'skip=`stat -c %s' + inc1pre +'`', 'of='+prex1_file], stdout = /dev/null)


        subprocess.Popen(['dd', 'if=' + file_2, 'bs=1', 'skip=`stat -c %s' + inc2pre +'`', 'of='+prex2_file], stdout = /dev/null)




        subprocess.Popen(['compare03', prex1, prex2, str(min_block)])

    finally:
        os.chdir(cw)
        shutil.rmtree(tmpc)
        inc1cpp_file.close()
        inc2cpp_file.close()
        inc1pre_file.close()
        inc2pre_file.close()
        prex1_file.close()
        prex2_file.close()
        file_1_f.close()
        file_1_f.close()

comper()
