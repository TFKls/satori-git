# -*- coding: utf-8 -*-
# vim:ts=4:sts=4:sw=4:expandtab

from satori.client.common import want_import
want_import(globals(), '*')

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

from satori.tools import options, setup, authenticate
options.add_option('--debug', dest='debug', default='', action='store', type='string')

(options, args) = setup()

def cribfinder_compare(comparison, submit_1, submit_2):
    if submit_1.id > submit2.id:
        z = submit_1
        submit_1 = submit_2
        submit_2 = z
    cw = os.getcwd()
    tmpd = tempfile.mkdtemp()
    os.chdir(tmpd)
    try:
        sub1 = os.path.join(tmpd, 'submit1.cpp')
        sub2 = os.path.join(tmpd, 'submit2.cpp')
        with open(sub1, 'w') as s1:
            s1.write(submit_1.data)
        with open(sub2, 'w') as s2:
            s2.write(submit_2.data)
        res = float(subprocess.check_output(['comparation', sub1, sub2, '100']))
        cr = ComparisonResult.filter(ComparisonResultStruct(comparison=comparison, submit_1 = submit_1, submit_2 = submit_2))
        if len(cr) > 0:
            cr = cr[0]
            cr.result = res
        else:
            ComparisonResult.create(ComparisonResultStruct(comparison=comparison, submit_1 = submit_1, submit_2 = submit_2, result = res))
    finally:
        os.chdir(cw)
        shutil.rmtree(tmpd)

def cribfinder_loop():
    while True:
        authenticate()
        print "Start"
        comparisons = Comparison.filter()
        for comp in comparisons:
            if Comparison.isExecute(comp):
                ts = datetime.datetime.fromtimestamp(0)
                test_suite_res = TestSuiteResult.filter(TestSuiteResultStruct(test_suite=comp.test_suite, status=comp.result_filter))
                submits = []
                for tsr in test_suite_res:
                    submit = Web.get_result_details(submit=tsr.submit)
                    if submit.time > ts:
                        ts = submit.time
                    submits.append(submit.submit)
               for i in range(0,len(submits)): 
                    for j in range(i+1,len(submits)):
                        cribfinder_compare(comp, submits[i], submits[j])
                comp.date_last_execute = ts
            else:
                ts = datetime.datetime.fromtimestamp(0)
                test_suite_res = TestSuiteResult.filter(TestSuiteResultStruct(test_suite=comp.test_suite, status=comp.result_filter))
                submits = []
                old_submits = []
                for tsr in test_suite_res:
                    submit = Web.get_result_details(submit=tsr.submit)
                    if submit.time > ts:
                        ts = submit.time
                    if submit.submit.time < comp.execution_date:
                        submits.append(submit)
                    else:
                        old_submits.append(submit)
                for i in submits: 
                    for j in old_submits:
                        cribfinder_compare(comp, i, j)
                for i in range(0,len(submits):    
                    for j in range(i+1,len(submits)):
                        cribfinder_compare(comp, submits[i], submits[j])
                comp.date_last_execute = ts
        time.sleep(10)

def cribfinder_initialize():
    pass

def cribfinder_finalize():
    pass

def cribfinder_init():
    try:
        cribfinder_initialize()
        while True:
            try:
                cribfinder_loop()
            except:
                traceback.print_exc()
            time.sleep(10)
    except:
        traceback.print_exc()
    finally:
        cribfinder_finalize()
