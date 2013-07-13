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
    packages=find_packages('src'),
    version = version,
    install_requires=[
        "appscript",
        "prettytable",
    ],
    entry_points={
        'console_scripts': [
            'wow = wowscripts.wow:main [scripts]',
            'professions = wowscripts.professions:main [scripts]',
            'combatLog = wowscripts.combatLog:main [scripts]',
            'chatLog = wowscripts.chatLog:main [scripts]',
            'luaUnlock = wowscripts.luaUnlock:main [scripts]',
            'battlenet = wowscripts.battlenet:main [scripts]',
        ]
    },
    extras_require = {
        'scripts':  ["mmhelper"],
    },
    dependency_links = [
        "http://basement.local/python-eggs/"
    ],
    ext_modules=[
        Extension('wowapi.vmregion', ['src/wowapi/vmregion.c']),
    ],
)

