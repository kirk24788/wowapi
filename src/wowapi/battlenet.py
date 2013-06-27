#!/usr/bin/python
# -*- coding: utf-8 -*-
import subprocess

class BattleNet:
    @staticmethod
    def isActive():
        out = subprocess.check_output("sudo ipfw show", shell=True)
        return not ("deny tcp from any 1119 to any" in out)

    @staticmethod
    def setActive():
        BattleNet.setStatus(True)

    @staticmethod
    def setHidden():
        BattleNet.setStatus(False)

    @staticmethod
    def setStatus(status):
        if status:
            if not BattleNet.isActive():
                out = subprocess.check_output("sudo ipfw del 1119", shell=True)
        else:
            if BattleNet.isActive():
                out = subprocess.check_output("sudo ipfw add 1119 deny tcp from any to any src-port 1119", shell=True)