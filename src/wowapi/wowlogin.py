#!/usr/bin/python
# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import time
import psutil
import base64
import argparse
from prettytable import PrettyTable
from appscript import *
from tempfile import mkstemp
from shutil import move
from os import remove, close
from mach_vm import VirtualMemory
from mmhelper.mmhelper import enum
from battlenet import BattleNet
from gdbhack import GdbHack
from wow import WorldOfWarcraft

CONFIG_FILE = '~/.wowpw'

if not os.path.isfile(os.path.expanduser(CONFIG_FILE)):
    print '''Config File not found!

You need a config-file at '%s' which following contents (don't forget the coding and don't use the wrong one!):
# coding=utf-8
# Path to the World of Warcraft Installation
DEFAULT_WOW_PATH = "/Applications/World of Warcraft/"
# Your account login mail - you can leave this field blank if WorldOfWarcraftLogin is not used
DEFAULT_ACCOUNT_MAIL = ""
# Your account password - base64 encoding is recommended - you can leave this field blank if WorldOfWarcraftLogin is not used
DEFAULT_ACCOUNT_PASSWORD = base64.b64decode("")
# List of account names - you can just use an empty list if WorldOfWarcraftLogin is not used
ACCOUNT_NAMES = ["WoW1","WoW2","WoW3","WoW4"]
# Map of Account Names with Char Name Lists - you can just use an empty list if WorldOfWarcraftLogin is not used
CHAR_NAMES = {
"WoW1":["Deathknight","Imbamage","Terminator"],
"WoW2":["Auctionbot", "Dæthknïght"], # you'll need the right encoding or special chars won't work
"WoW3":[], # use empty lists to mark inactive accounts
"WoW4":["AdmiralAckbar", "Noname"],
}
    ''' % (CONFIG_FILE)
    sys.exit(1)

execfile(os.path.expanduser(CONFIG_FILE))


VALIDATION_ACCOUNT_ID = None


class WorldOfWarcraftLogin(WorldOfWarcraft):
    def __init__(self, accountId, charId, loginName=DEFAULT_ACCOUNT_MAIL, wowPath=DEFAULT_WOW_PATH, startUpDelay=12):
        if accountId >= len(ACCOUNT_NAMES):
            raise Exception( 'has to be between 0 and %d'%(len(ACCOUNT_NAMES)-1) )
        if len(CHAR_NAMES[ACCOUNT_NAMES[accountId]]) == 0:
            raise Exception( '%d is not active!'%accountId )
        maxCharId = len(CHAR_NAMES[ACCOUNT_NAMES[accountId]])-1
        if charId > maxCharId:
            raise Exception( 'has to be between 0 and %d for account %d' %(maxId, accId) )
        self._setLoginData(loginName, accountId, charId, wowPath)
        wowBinary = os.path.join(wowPath, "World of Warcraft.app/Contents/MacOS/World of Warcraft")
        self.wowProcess = subprocess.Popen(wowBinary, stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))
        #self.wowPID = self.wowProcess.pid
        #super( WorldOfWarcraftLogin, self ).__init__(self.wowProcess.pid)
        WorldOfWarcraft.__init__(self, self.wowProcess.pid)
        self.delay("Waiting for WoW Startup", startUpDelay)


    def login(self, password=DEFAULT_ACCOUNT_PASSWORD, hidden=False, charSelectDelay=6, loginDelay=20):
        BattleNet.setActive()
        self.type(password)
        self.key(KEY_ENTER)
        self.delay("Waiting for Char Select", charSelectDelay)
        if hidden:
            BattleNet.setHidden()
        self.key(KEY_ENTER)
        self.delay("Waiting for Login", loginDelay)

    def _setLoginData(self, accountName, accountListIndex, lastCharacterIndex, wowPath):
        accounts = []
        for i in range(len(ACCOUNT_NAMES)):
            if i == accountListIndex:
                accounts.append("!%s" % ACCOUNT_NAMES[i])
            else:
                accounts.append(ACCOUNT_NAMES[i])
        #Create temp file
        fh, absPath = mkstemp()
        wowConfigPath = os.path.join(wowPath, "WTF/Config.wtf")
        newConfig = open(absPath,'w')
        oldConfig = open(wowConfigPath)
        nameSet = False
        listSet = False
        charSet = False
        for line in oldConfig:
            if line.startswith("SET accountName"):
                nameSet = True
                newConfig.write("SET accountName \"%s\"\n" % accountName)
            elif line.startswith("SET accountList"):
                listSet = True
                newConfig.write("SET accountList \"%s|\"\n" % '|'.join(accounts))
            elif line.startswith("SET lastCharacterIndex"):
                charSet = True
                if lastCharacterIndex >= 0:
                    newConfig.write("SET lastCharacterIndex \"%d\"\n" % lastCharacterIndex)
                else:
                    newConfig.write(line)
            else:
                newConfig.write(line)
        if not nameSet:
            newConfig.write("SET accountName \"%s\"\n" % accountName)
        if not listSet:
            newConfig.write("SET accountList \"%s|\"\n" % '|'.join(accounts))
        if not charSet:
            newConfig.write("SET lastCharacterIndex \"%d\"\n" % lastCharacterIndex)
        #close temp file
        newConfig.close()
        close(fh)
        oldConfig.close()
        #Remove original file
        remove(wowConfigPath)
        #Move new file
        move(absPath, wowConfigPath)

    @staticmethod
    def charTable():
        KEY = "CharacterID / AccountID"
        maxChars=1
        for aIdx in range(len(ACCOUNT_NAMES)):
            if len(CHAR_NAMES[ACCOUNT_NAMES[aIdx]]) > maxChars:
                maxChars = len(CHAR_NAMES[ACCOUNT_NAMES[aIdx]])
        header = [KEY]
        for accountId in range(len(ACCOUNT_NAMES)):
            if len(CHAR_NAMES[ACCOUNT_NAMES[accountId]]) > 0:
                header.append(str(accountId) + " = " + ACCOUNT_NAMES[accountId])
        table = PrettyTable(header)
        #table.align[KEY] = "r"
        for charId in range(maxChars):
            row = [str(charId)]
            for accountId in range(len(ACCOUNT_NAMES)):
                account = ACCOUNT_NAMES[accountId]
                if len(CHAR_NAMES[ACCOUNT_NAMES[accountId]]) > 0:
                    if len(CHAR_NAMES[account])>charId:
                        row.append(CHAR_NAMES[account][charId])
                    else:
                        row.append("")
            table.add_row(row)
        return table

    @staticmethod
    def validateCharId(char):
        charId = int(char)
        if not VALIDATION_ACCOUNT_ID:
            if charId < 0 or charId > 10:
                raise argparse.ArgumentTypeError( 'has to be between 0 and 10' )
            return charId
        else:
            maxId = len(CHAR_NAMES[ACCOUNT_NAMES[accId]])-1
            if charId > maxId:
                raise argparse.ArgumentTypeError( 'has to be between 0 and %d for account %d' %(maxId, accId) )
            return charId

    @staticmethod
    def validateAccountId(account):
        accountId = int(account)
        VALIDATION_ACCOUNT_ID = accountId
        if accountId >= len(ACCOUNT_NAMES):
            raise argparse.ArgumentTypeError( 'has to be between 0 and %d'%(len(ACCOUNT_NAMES)-1) )
        if len(CHAR_NAMES[ACCOUNT_NAMES[accountId]]) == 0:
            raise argparse.ArgumentTypeError( '%d is not active!'%accountId )
        return accountId