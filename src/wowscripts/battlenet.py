#!/usr/bin/python
import subprocess
import sys
import os

from wowapi.battlenet import BattleNet


def main():
    cmdname =  os.path.split(sys.argv[0])[-1]
    if len(sys.argv) != 2:
        print "%s: missing argument\nusage: %s on|off" % (cmdname, cmdname)
        sys.exit(1)
    if sys.argv[1].lower() == "on":
        if BattleNet.isActive():
            print "already active"
        else:
            BattleNet.setActive()
            print "activated battle.net chat"
    elif sys.argv[1].lower() == "off":
        if not BattleNet.isActive():
            print "already deactivated"
        else:
            BattleNet.setHidden()
            print "deactivated battle.net chat"
    elif sys.argv[1].lower() == "status":
        if BattleNet.isActive():
            print "battle.net chat activated"
        else:
            print "battle.net chat deactivated"
    else:
        print "%s: ivalid argument %s\nusage: %s on|off" % (cmdname, sys.argv[1], cmdname)
        sys.exit(2)

if __name__ == "__main__":
    main()