from setuptools import setup, find_packages
package = "wowapi"
try:
    verstrline = open('src/'+package+'/_version.py', "rt").read()
except EnvironmentError:
    pass # Okay, there is no version file.
else:
    import re
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    mo = re.search(VSRE, verstrline, re.M)
    if mo:
        version = mo.group(1)
    else:
        raise RuntimeError("unable to find version in yourpackage/_version.py")


#version = file('version.txt').read().strip()

setup(
    name = "wowapi",
    package_dir={'': 'src'},
    packages=['wowapi'],
    version = version,
)
