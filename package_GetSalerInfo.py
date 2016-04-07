from distutils.core import setup
import py2exe,sys,os

# python package_GetSalerInfo.py py2exe

sys.argv.append('py2exe')

setup(
    console=[{'script':"GetSalerInfo.py"}],
    options={
        "py2exe":{
                "skip_archive": True,
                "unbuffered": True,
                "optimize": 2
        },
    }
)