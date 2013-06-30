#!/usr/bin/python
# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import time
from appscript import *
from tempfile import mkstemp
from shutil import move
from os import remove, close
import argparse
from wowapi.wowlogin import WorldOfWarcraftLogin
from wowapi.wowlogin import ACCOUNT_NAMES
from wowapi.wowlogin import CHAR_NAMES


def getDescription():
    description = "World of Warcraft Login:\n\n"
    description += str(WorldOfWarcraftLogin.charTable())
    return description



def main():
    parser = argparse.ArgumentParser(description=getDescription(), formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('account', metavar='ACCOUNT-ID', type=WorldOfWarcraftLogin.validateAccountId, nargs=1, help='Account ID')
    parser.add_argument('char', metavar='CHAR-ID', type=WorldOfWarcraftLogin.validateCharId, nargs=1, default=-1, help='Char ID')
    parser.add_argument('--hidden', '-s', dest='hidden', action='store_true', default=False, help='hide online status?')
    parser.add_argument('--lua-unlock', '-l', dest='luaUnlock', action='store_true', default=False, help='unlock protected lua?')

    #group = parser.add_mutually_exclusive_group(required=True)
    #group.add_argument('account', metavar='ACCOUNT', type=WorldOfWarcraft.validateAccountId, nargs='?', help='Account ID')
    #group.add_argument('charname', metavar='CHARNAME', nargs='?', help='Account ID')

    args = parser.parse_args()
    accId = args.account
    args = parser.parse_args()

    wow = WorldOfWarcraftLogin(args.account, args.char)
    wow.login(hidden=args.hidden, loginDelay=0)
    if args.luaUnlock:
        wow.luaUnlock()

if __name__ == "__main__":
    main()


