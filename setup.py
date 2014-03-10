from setuptools import setup, find_packages, Extension
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
    packages= ["wowapi", "wowscripts"], #find_packages('src'),
    version = version,
    install_requires=[
        "appscript",
        "prettytable",
        "pexpect",
    ],
    entry_points={
        'console_scripts': [
            'wow = wowscripts.wow:main',
            'professions = wowscripts.professions:main',
            'combatLog = wowscripts.combatLog:main',
            'chatLog = wowscripts.chatLog:main',
            'luaUnlock = wowscripts.luaUnlock:main',
            'battlenet = wowscripts.battlenet:main',
        ]
    },
    ext_modules=[
        Extension('wowapi.vmregion', ['src/wowapi/vmregion.c']),
    ],
)

