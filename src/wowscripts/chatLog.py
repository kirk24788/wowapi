#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import psutil
from datetime import datetime
import time

from wowapi.wow import WorldOfWarcraft
from wowapi.wow import ChatType
from wowapi.wow import ChannelName


PIDS = WorldOfWarcraft.getAllPIDs()

def getDescription():
    description = "World of Warcraft Chat Log:\n\n"
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
    parser.add_argument('--update', '-u', default=2, type=int, metavar='UPDATE INTERVAL', help='update interval in seconds')
    args = parser.parse_args()

    wow = WorldOfWarcraft(args.pid)
    lastMessageTime = 0

    while True:
        try:
            messages = wow.getAllMessages()
            for msg in messages:
                if msg.time > lastMessageTime:
                    if not msg.formattedMessage.startswith("Type: [17], Channel: [Crb"):
                        if msg.type == ChatType.CHANNEL:
                            channel = msg.channel
                        else:
                            channel = ChannelName(msg.type)
                        print "[%s] [%s] %s: %s" % (datetime.fromtimestamp(msg.time).strftime('%H:%M:%S'), channel, msg.sender, msg.rawMessage) # '%Y-%m-%d %H:%M:%S'
                    lastMessageTime = msg.time
            time.sleep(args.update)
        except KeyboardInterrupt:
            exit(0)

if __name__ == "__main__":
    main()
