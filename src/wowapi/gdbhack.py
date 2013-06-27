#!/usr/bin/python
# -*- coding: utf-8 -*-
import subprocess

class GdbHack:
    @staticmethod
    def overwriteData(pid, address, data):
        command = "echo \"set {char[%d]}%s={" % (len(data),hex(address))
        for byte in data:
            command += hex(byte) + ", "
        command = command[:-2]
        command += "}\" | gdb attach %d > /dev/null 2> /dev/null" % pid
        subprocess.call(command, shell=True)