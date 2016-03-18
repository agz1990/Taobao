import commands
import sys
import os
import inspect

import logging
import logging.config
import ConfigParser
import lib.globalVars as g_vars

logger = logging.getLogger("FroductInfo")


def initConfig():
    conf = ConfigParser.ConfigParser()
    conf.optionxform = str
    conf.read(os.path.normpath("conf/conf.ini"))
    g_vars.workingdir = os.path.normpath(conf.get("base", "workingdir"))
    g_vars.forceLogin = bool(int(conf.get("base", "force_login")))
    g_vars.navie_min_sec = int(conf.get('base', 'navie_min_sec'))
    g_vars.navie_max_sec = int(conf.get('base', 'navie_max_sec'))
    g_vars.webdriver = conf.get('base', 'webdriver')


