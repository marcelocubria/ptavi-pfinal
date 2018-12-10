#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import sys

try:
    config = sys.argv[1]
except IndexError:
    sys.exit("Usage: python uaserver.py config")

print("Listening...")