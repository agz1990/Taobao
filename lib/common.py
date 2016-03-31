# encoding: utf-8

from __future__ import division
import time
import sys
from lib.ProgressBar import AnimatedProgressBar

def sleepShowProcess(sec, msg, width=40):
    custom_options = {
        'end': 100,
        'width': width,
        'fill': '#',
        'format': (msg + u'[%(fill)s%(blank)s] %(progress)s%% ').encode('gbk')
    }
    first = True
    step = float(sec / 100)
    p = AnimatedProgressBar(**custom_options)
    while True:

        if first:
            first = False
        else:
            sys.stdout.write('\b' * (custom_options['width'] + 4))
        p + 1
        sys.stdout.flush()
        p.show_progress()
        time.sleep(step)
        if p.progress == 100:
            sys.stdout.write('\n')
            break
