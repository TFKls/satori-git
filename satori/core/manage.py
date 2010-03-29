#!/usr/bin/env python

"""Script. Manages the Django part of satori.core.
"""


from django.core.management import execute_manager
import satori.core.settings as settings

if __name__ == "__main__":
    execute_manager(settings)
