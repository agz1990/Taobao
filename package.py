from distutils.core import setup
import py2exe,sys,os

# python mysetup.py py2exe

sys.argv.append('py2exe')

setup(
    console=[{'script':"GetProductInfo.py"}],
    options={
        "py2exe":{
                "skip_archive": True,
                "unbuffered": True,
                "optimize": 2
        },
    }
)