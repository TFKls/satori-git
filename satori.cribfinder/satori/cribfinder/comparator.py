# -*- coding: utf-8 -*-
# vim:ts=4:sts=4:sw=4:expandtab

from satori.judge.judge import JailBuilder, JailRun
from satori.client.common import want_import
want_import(globals(), '*')

from satori.cribfinder.satori.cribfinder import cribfinder_loop

print "Run Cribfinder"
cribfinder_loop()
print "Cribfinder Crash"
