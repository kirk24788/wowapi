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
from battlenet import BattleNet
from gdbhack import GdbHack

KEY_ENTER = 36
KEY_ESCAPE = 53

MEMORY_EDITS = {
"LUA_UNLOCK" : (
    0x7f0362,
    [0x74],
    [0xeb],
    "JE -> JMP"
),
"INTERACT_UNIT" : (
    0x7fd950,
    [0xc7,0x44,0x24,0x04,0x00,0x00,0x00,0x00,0xe8,0xa3,0x7b],
    [0x50,0xb8,0x00,0x00,0x00,0x00,0x89,0x01,0x58,0xeb,0x06],
    "PUSH EAX; MOV EAX,0; POP EAX; MOV [ECX],EAX; JMP+6"
),
}


OFFSETS = {
"CHAT_MESSAGES" : 0x1844964
}


VALIDATION_ACCOUNT_ID = None


def enum(**enums):
    return type('Enum', (), enums)
ChatType = enum(SAY=1,GUILD=4,OFFICER=5,YELL=6,WHISPER=7,REPLY=9,CHANNEL=17)

def ChannelName(channelId):
    if channelId == 1:
        return "Say"
    elif channelId == 4:
        return "Guild"
    elif channelId == 5:
        return "Officer"
    elif channelId == 6:
        return "Yell"
    elif channelId == 7:
        return "Whisper"
    elif channelId == 9:
        return "Reply"
    else:
        return "Unknown: %d" % channelId

class ChatMessage:
    def __init__(self,vm,index=0):
        offset = 0x17c8
        messageOffset = OFFSETS["CHAT_MESSAGES"] + (offset * index)
        senderOffset = 0x14
        formattedOffset = 0x45 # 0x003c
        rawOffset = 0x0bfd
        messageTypeOffset = 0x17b8
        channelNumberOffset = 0x17bc
        sequenceNumberOffset = 0x17b4
        timeOffset = 0x17c4
    
        self.GUID = vm.read_long(messageOffset)
        self.sender = vm.read_string(messageOffset+senderOffset)
        self.formattedMessage = vm.read_string(messageOffset+formattedOffset)
        self.rawMessage = vm.read_string(messageOffset+rawOffset)
        self.messageType = vm.read_int(messageOffset+messageTypeOffset)
        self.channelNumber = vm.read_int(messageOffset+channelNumberOffset)
        self.sequenceNumber = vm.read_int(messageOffset+sequenceNumberOffset)
        self.time = vm.read_int(messageOffset+timeOffset)
        if len(self.formattedMessage) > 5:
            fmd = map(lambda x: x.split(": ", 1)[1][1:-1], self.formattedMessage.split(", ", 5))
            self.type = int(fmd[0])
            self.channel = fmd[1]
            self.activePlayerGUID = int(fmd[4],16)
        else:
            self.type = -1
            self.channel = -1
            self.activePlayerGUID = None

class WorldOfWarcraft:
    def __init__(self, wowPID):
        self.wowPID = wowPID
        self._vm = None

    def type(self, text, typeDelay=0.02):
        for c in text:
            app(pid=self.wowPID).activate()
            app('System Events').keystroke(c)
            time.sleep(typeDelay)
            
    @staticmethod
    def getAllPIDs():
        pids = []
        for pid in psutil.get_pid_list():
            proc = psutil.Process(pid)
            if(proc.name=="World of Warcraft"):
                pids.append(pid)
        return pids
        
    def _hack(self, key, revert=False):
        address,originalData,newData,comment = MEMORY_EDITS[key]
        if revert:
            GdbHack.overwriteData(self.wowPID, address, originalData)
        else:
            GdbHack.overwriteData(self.wowPID, address, newData)

    def _initVirtualMemory(self):
        if self._vm == None:
            self._vm = VirtualMemory(self.wowPID)
        return self._vm

    def luaUnlock(self):
        self._hack("LUA_UNLOCK")
        
    def luaLock(self):
        self._hack("LUA_UNLOCK", True)
        
    def interactUnitUnlock(self):
        self._hack("INTERACT_UNIT")
        
    def interactUnitLock(self):
        self._hack("INTERACT_UNIT", True)

    def key(self, keycode, keyDelay=0.02):
        app(pid=self.wowPID).activate()
        time.sleep(keyDelay)
        app('System Events').key_code(keycode)

    def logout(self, logoutDelay=25, shutdownDelay=5):
        self.command("/logout")
        self.delay("Waiting for Logout", logoutDelay)
        self.key(KEY_ESCAPE)
        self.key(KEY_ESCAPE)
        self.delay("Waiting for WoW Shutdown", shutdownDelay)
    
    def delay(self, text,seconds):
        if seconds <= 0:
            return
        for i in range(seconds):
            percent = int(float(i) / float(seconds) * 100)
            chars = percent/5
            sys.stdout.write('\r')
            sys.stdout.write("%s: [%-20s] %d%%" % (text,'='*chars, percent))
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write('\r')
        sys.stdout.write("%s: [%-20s] %d%%\n" % (text,'='*20, 100))
        sys.stdout.flush()
    
    def command(self,command):
        self.key(KEY_ENTER)
        time.sleep(0.5)
        self.type(command)
        time.sleep(0.5)
        self.key(KEY_ENTER)
    
    def craft(self,profession, skillname, itemCount=1, professionWindowDelay=1, craftingDelay=7):
        self.command("/use " + profession)
        self.delay("Waiting for Profession Window", professionWindowDelay)
        self.command("/run for i=1,GetNumTradeSkills()do local skillName,_,nA,_,_,_=GetTradeSkillInfo(i)if skillName==\"" 
        + skillname + "\"then DoTradeSkill(i," + str(itemCount) + ")end end")
        self.delay("Waiting for '" + skillname + "'", craftingDelay)

    def getMessage(self,index=0):
        vm = self._initVirtualMemory()
        return ChatMessage(vm,index)
        
    def getAllMessages(self):
        vm = self._initVirtualMemory()
        messages = []
        for i in range(60):
            msg = ChatMessage(vm,i)
            if len(msg.rawMessage) > 0:
                messages.append(msg)
        messages.sort(key=lambda x: x.time)
        return messages
