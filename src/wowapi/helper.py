import sys
import os

DEFAULT_MESSAGE_PADDING = 25
DEFAULT_BUFFER_SIZE = 4 * 1024 * 1024


def elevateSudo():
    if os.getuid() != 0:
        command = ""
        for part in sys.argv[1:]:
            command = command + " \\\"" + part + "\\\""

        script = """osascript -e 'do shell script "python %s %s" with administrator privileges'""" % (sys.argv[0], command)
        os.system(script)

def uniq(seq):
    """ Uniqifies a List - Source: http://www.peterbe.com/plog/uniqifiers-benchmark """
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if x not in seen and not seen_add(x)]


def normalMessage(message,value,padding=DEFAULT_MESSAGE_PADDING):
    """ Prints a normal padded message """
    print "%s: %s" % (message.rjust(padding,' '), str(value))

def loadingMessage(message,padding=DEFAULT_MESSAGE_PADDING):
    """ Prints a padded message with loading bar
        The method returs two functions: progress and finish
        progress sets the new progress and finish completes the loading bar
    """
    _message = message
    def progress(current=0,max=100):
        percent = int(float(current) / float(max) * 100)
        if percent < 0:
            percent = 0
        elif percent > 100:
            percent = 100
        chars = percent/5
        sys.stdout.write('\r')
        sys.stdout.write("%s: [%-20s] %d%%" % (_message.rjust(padding,' '),'='*chars, percent))
        sys.stdout.flush()
    def finish():
        progress(100,100)
        sys.stdout.write('\n')
        sys.stdout.flush()
    progress(0,100)
    return progress,finish
    
def enum(**enums):
    return type('Enum', (), enums)

class BinarySearch:
    __file = None
    __fileSize = 0
    __bufferSize = 0
    
    def __init__(self,filename,bufferSize=DEFAULT_BUFFER_SIZE):
        self.__file = open(filename, 'rb')
        self.__fileSize = os.path.getsize(filename)
        self.__bufferSize = bufferSize
    
    def findOffset(self, searchString, startPos=0, progressFn=None):
        buffer = None
        if startPos > 0:
            self.__file.seek(startPos)
        overlap = len(searchString) - 1
        while True:
            if progressFn:
                progressFn(self.__file.tell(), self.__fileSize)
            if (self.__file.tell() >= overlap and self.__file.tell() < self.__fileSize):
                self.__file.seek(self.__file.tell() - overlap)
            buffer = self.__file.read(self.__bufferSize)
            beginPos = startPos % self.__bufferSize
            if buffer:
                pos = buffer.find(searchString, beginPos)
                if pos >= 0:
                    return self.__file.tell() - (len(buffer) - pos)
            else:
                return -1

    def findLastOffset(self, searchString, startPos=0,progressFn=None):
        if startPos < 0:
            return -1
        lastPos = self.findOffset(searchString,startPos,progressFn)
        nextPos = lastPos
        while nextPos > 0:
            lastPos = nextPos
            nextPos = self.findOffset(searchString,lastPos+1,progressFn)
        return lastPos
    
    def __del__(self):
        if self.__file:
            self.__file.close()