import time
import os
import sys
import psutil
try:
    import pexpect
except:
    print "ERROR: Missing Python Library 'pexpect' - Please Install with 'sudo easy_install pexpect'"
    sys.exit(3)
import logging as LOG
from subprocess import Popen, PIPE


TRIPWIRE = "0x0118bda8"
LUA_UNLOCK_BP = "0x0080a0b0"
LUA_UNLOCK_OFFSET = "0x159808c"
CHARNAME_OFFSET = "0x0192fce4"

LLDB_BINARY = "/usr/bin/lldb"

def get_all_wow_apps():
    output = Popen(["mdfind", "kMDItemCFBundleIdentifier == 'com.blizzard.worldofwarcraft'"], stdout=PIPE).communicate()[0]
    return map(lambda x: "%s/Contents/MacOS/World of Warcraft" % x, filter(lambda x: x.endswith("Warcraft.app"), output.split("\n")))

def get_all_wow_pids():
    x86_binaries = get_all_wow_apps()
    pids = []
    for pid in psutil.get_pid_list():
        try:
            proc = psutil.Process(pid)
            if(proc.exe in x86_binaries):
                pids.append(pid)
        except:
            pass
        #if(proc.exe in x86_binaries):
        #    pids.append(pid)
    return pids


class LLDB():
    def __init__(self,pid):
        self.pid = pid
        self.lldb = pexpect.spawn(LLDB_BINARY)
        #self.lldb.logfile = sys.stdout
        self._cmd("attach %d" % pid)
        self._prepare_tripwire()
        self._prepare_lua_unlock()
        self._cmd("continue")
       # self._cmd("script", expect=">>>")
       # self._cmd("print 'OK OK OK!'; exit()", expect="print 'OK OK OK!'; exit\\(\\)")
    
    def _prepare_tripwire(self):
        self._cmd("breakpoint set -a %s" % TRIPWIRE)
        self._cmd("breakpoint command add -s python 1", expect="Type 'DONE' to end.")
        self._cmd("""thread = frame.GetThread()
process = thread.GetProcess()
process.Detach()
import sys
print "IPC>>>WARNING: Tripwire activated - thread_get_state called - deactivating..."
sys.exit(2)
return False
DONE""")

    def _prepare_lua_unlock(self):
        self._cmd("breakpoint set -a %s" % LUA_UNLOCK_BP)
        self._cmd("breakpoint command add -s python 2", expect="Type 'DONE' to end.")
        self._cmd("""thread = frame.GetThread()
process = thread.GetProcess()
error = lldb.SBError()
addr = process.ReadUnsignedFromMemory(%s, 4, error)
import sys
if error.Success():
    result = process.WriteMemory(addr,"\\x00\\x00\\x00\\x00", error)
    if not error.Success() or result != 4:
        process.Detach()
        print 'IPC>>>ERROR: SBProcess.WriteMemory() failed!'
        sys.exit(1)
else:
    process.Detach()
    print "IPC>>>ERROR: Couldn't read LUA Unlock Address!"
    sys.exit(1)
return False
DONE""" % LUA_UNLOCK_OFFSET)


    def _cmd(self, cmd, expect="(lldb)"):
        self.lldb.sendline(cmd)
        if expect != None:
            self.lldb.expect(expect)

    def wait_for_exit(self):
        is_running = True
        while is_running:
            try:
                try:
                    inp = self.lldb.read_nonblocking(100,1)
                    if inp.startswith("IPC>>>"):
                        print inp[6:]
                    is_runnning = self.lldb.isalive()
                except pexpect.EOF:
                    self.lldb.close()
                    is_running = False
            except pexpect.TIMEOUT:
                pass
        return self.lldb.exitstatus

    def detach(self):
        self._cmd("detach")

def print_usage():
    print "Usage: %s <WOW_PID>" % sys.argv[0]
    wow_pids = get_all_wow_pids()
    if len(wow_pids)==0:
        print "World of Warcraft not found - Please start it first! (64bit NOT supported)"
    else:
        print "Available World of Warcraft PIDs:"
        for pid in wow_pids:
            print " * %d" % pid

def main():
    print "World of Warcraft LUA Unlocker (x86)"
    osx_version = Popen(["sw_vers", "-productVersion"], stdout=PIPE).communicate()[0]
    if not osx_version.startswith("10.9"):
        print "ERROR: OSX Mavericks is required!"
        sys.exit(1)
    if not os.path.exists(LLDB_BINARY):
        print "ERROR: Missing LLDB - Please Install Xcode Command Line Tools via 'xcode-select --install'"
        sys.exit(1)
    if len(sys.argv) != 2:
        print_usage()
        sys.exit(2)
    try:
        pid = int(sys.argv[1])
    except ValueError:
        print "ERROR: Invalid PID '%s' - must be a number!" % sys.argv[1]
        print_usage()
        sys.exit(2)
    if pid not in get_all_wow_pids():
        print "ERROR: %d is not a valid PID of a World of Warcraft Process!" % pid
        print_usage()
        sys.exit(2)
    
    try:
        print "Unlocking %d..." % pid
        lldb = LLDB(pid)
        print "...LUA unlocked!"
        lldb.wait_for_exit()
    except KeyboardInterrupt:
        print "\nExiting LUA Unlocker..."
        lldb.detach()


if __name__ == "__main__":
    main()