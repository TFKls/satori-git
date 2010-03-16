#!/usr/bin/env python

from django.core.management import execute_manager
import satori.core.settings as settings

if __name__ == "__main__":
    execute_manager(settings)
