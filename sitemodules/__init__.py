# -*- coding: utf-8 -*-

import sys

if (sys.version_info.major < 3) or (sys.version_info.major == 3 and
                                    sys.version_info.minor < 5):
    raise Exception("Requires Python >= 3.5 to run script!")
