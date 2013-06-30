#!/usr/bin/python
import os
import sys
import time
import datetime
import argparse

from mmhelper.mmhelper import uniq
from mmhelper.mmhelper import normalMessage
from mmhelper.mmhelper import loadingMessage
from mmhelper.mmhelper import BinarySearch

LOG_DIR = "/Applications/World of Warcraft/Logs/"
COMBATLOG_FILENAME = LOG_DIR + "WoWCombatLog.txt"
TARGETLOG_FILENAME = LOG_DIR + "today.txt"
DEFAULT_BUFFER_SIZE = 4 * 1024 * 1024

SOURCE_NAME = 2
SOURCE_GUID = 1
TARGET_NAME = 6
TARGET_GUID = 5
UNKNOWN_STRING = "\"Unknown\""







class CombatLogParser:
    today = datetime.date.today()
    logsize = 0
    bufferSize = 0
    targetLog = None
    linesWritten = 0
    guidMap = {}
    logOffsets=[]
    firstOffset = -1
    lastOffset = -1
    combatlogFilename = ""
    sourceFixed = 0
    sourceUnfixable = 0
    targetFixed = 0
    targetUnfixable = 0

    def __init__(self, targetFilename=TARGETLOG_FILENAME, combatlogFilename=COMBATLOG_FILENAME, bufferSize=DEFAULT_BUFFER_SIZE):
        self.targetLog = open(targetFilename, "w")
        self.combatlogFilename = combatlogFilename
        self.logsize = os.path.getsize(self.combatlogFilename)
        self.bufferSize = bufferSize
        normalMessage("Fetching from file", self.combatlogFilename)
        normalMessage("Log-Size", str(self.logsize/1024/1024) + " MB")
        normalMessage("Streaming into file", targetFilename)
    
    def __del__(self):
        if self.targetLog:
            self.targetLog.close()

    def parse(self, days):
        self._findOffsets(days)
        self._iterateLines("Scanning Progress", self._scanGUID)
        normalMessage("GUID's found", len(self.guidMap.keys()))
        self._iterateLines("Writing Progress",self._writeProgress)
        normalMessage("Lines written", self.linesWritten)
        normalMessage("Characters fixed", (self.sourceFixed + self.targetFixed))
        normalMessage("Unfixable characters", (self.sourceUnfixable + self.targetUnfixable))
        

    def _findOffsets(self, days):
        uniqueOffsets = sorted(uniq(args.offsets))
        logDates=[]
        progress, finish = loadingMessage("Finding Offsets")
        binSearch = BinarySearch(self.combatlogFilename)
        lastPos = 0
        for pos in range(len(uniqueOffsets)):
            offset = uniqueOffsets[pos]
            targetDate = datetime.date.today() + datetime.timedelta(days=offset)
            logDate = "%d/%d " % (targetDate.month,targetDate.day)
            logStartPos = binSearch.findOffset(logDate, lastPos, progress)
            logEndPos = binSearch.findLastOffset("\n"+logDate,logStartPos, progress)
            lastPos = logStartPos
            self.logOffsets.append((logStartPos,logDate, logEndPos))
            logDates.append(logDate[:-1])
        for startOffset, logDate, endOffset in self.logOffsets:
            if self.firstOffset < 0:
                if startOffset > 0:
                    self.firstOffset = startOffset
            if endOffset > 0:
                self.lastOffset = endOffset
        finish()
        normalMessage("Date(s)", logDates)
    
    def _iterateLines(self, message, lineHandler):
        clog = open(self.combatlogFilename, "r", self.bufferSize) 
        progress, finish = loadingMessage(message)
        for startOffset, logDate, endOffset in self.logOffsets:
            if startOffset > 0:
                clog.seek(startOffset)
                for line in clog:
                    progress(clog.tell()-self.firstOffset, self.lastOffset-self.firstOffset)
                    if line.startswith(logDate):
                        lineHandler(line)
                    else:
                        break
        finish()
        clog.close()

    def _scanGUID(self, line):
        lineArray = line.split(',')
        if UNKNOWN_STRING != lineArray[SOURCE_NAME]:
            self.guidMap[lineArray[SOURCE_GUID]] = lineArray[SOURCE_NAME]
        if UNKNOWN_STRING != lineArray[TARGET_NAME]:
            self.guidMap[lineArray[TARGET_GUID]] = lineArray[TARGET_NAME]
            
    def _writeProgress(self, line):
        lineArray = line.split(',')
        if UNKNOWN_STRING == lineArray[SOURCE_NAME]:
            if(self.guidMap.has_key(lineArray[SOURCE_GUID])):
                lineArray[SOURCE_NAME] = self.guidMap[lineArray[SOURCE_GUID]]
                self.sourceFixed = self.sourceFixed + 1
            else:
                self.sourceUnfixable = self.sourceUnfixable + 1
        if UNKNOWN_STRING == lineArray[TARGET_NAME]:
            if(self.guidMap.has_key(lineArray[TARGET_GUID])):
                lineArray[TARGET_NAME] = self.guidMap[lineArray[TARGET_GUID]]
                self.targetFixed = self.targetFixed + 1
            else:
                self.targetUnfixable = self.targetUnfixable + 1
        self.targetLog.write(','.join(lineArray))
        self.linesWritten = self.linesWritten + 1

def main():
    parser = argparse.ArgumentParser(description="World of Warcraft CombatLog Parser")
    parser.add_argument('offsets', metavar='OFFSETS', nargs='*', default=[0], type=int, help='Offset in days')
    args = parser.parse_args()

    clp = CombatLogParser()
    clp.parse(args.offsets)


if __name__ == "__main__":
    main()
