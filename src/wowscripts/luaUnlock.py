#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import psutil
from datetime import datetime
from wowapi.helper import elevateSudo
from wowapi.wow import WorldOfWarcraft

PIDS = WorldOfWarcraft.getAllPIDs()

def getDescription():
    description = "World of Warcraft LUA Unlocker:\n\n"
    if len(PIDS) > 0:
        key = 0
        now = datetime.now()
        for pid in PIDS:
            p = psutil.Process(pid)
            created = datetime.fromtimestamp(p.create_time)
            ageInMinutes = (now-created).seconds % 60
            description += ("%d (PID:%d) - Age: %d Minutes\n" % (key, pid,ageInMinutes))
            key = key + 1
    else:
        description += "NO ACTIVE WOW INSTANCES FOUND!"
    return description

def validateID(key):
    key = int(key)
    if len(PIDS) == 0:
        raise argparse.ArgumentTypeError( 'No WoW Instances found!' )
    if key >= 0 and key < len(PIDS):
        return PIDS[key]
    if len(PIDS)==1:
        raise argparse.ArgumentTypeError( 'can only be 0' )
    else:
        raise argparse.ArgumentTypeError( 'has to be between 0 and %d' % (len(PIDS)-1) )

def main():
    parser = argparse.ArgumentParser(description=getDescription(), formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('pid', metavar='INSTANCE KEY', type=validateID,  help='WoW Instance Key')
    parser.add_argument('--revert', '-r', dest='revert', action='store_true', default=False, help='revert unlock?')
    args = parser.parse_args()
    elevateSudo()
    w = WorldOfWarcraft(args.pid)
    if args.revert:
        print "Locking PID: %d" % args.pid
        w.luaLock()
    else:
        print "Unlocking PID: %d" % args.pid
        w.luaUnlock()

if __name__ == "__main__":
    main()