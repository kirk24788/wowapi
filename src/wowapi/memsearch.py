import wowapi.vmregion as vm
import os

class __Search(object):
    def __init__(self, pid, align, searchFn):
        if os.getuid() != 0:
            raise EnvironmentError("Not running as root.")
  
        self.pid = pid
        self.searchFn = searchFn
        self.lastResult = []
        if align:
            self.align = 1
        else:
            self.align = 0
    
    def search(self, value):
        self.lastResult = self.searchFn(self.pid, value, self.align)
        return self.lastResult

    def searchAgain(self, value):
        oldResult = self.lastResult
        curResult = self.search(value)
        self.lastResult = [val for val in oldResult if val in curResult]
        return self.lastResult

    def lastResult(self):
        return self.lastResult

class SearchInt32(__Search):
    def __init__(self, pid, align=False):
        super(SearchInt32, self).__init__(pid, align, vm.search_int32)
        
class SearchUInt32(__Search):
    def __init__(self, pid, align=False):
        super(SearchUInt32, self).__init__(pid, align, vm.search_uint32)

class SearchInt64(__Search):
    def __init__(self, pid, align=False):
        super(SearchInt64, self).__init__(pid, align, vm.search_int64)
        
class SearchUInt64(__Search):
    def __init__(self, pid, align=False):
        super(SearchUInt64, self).__init__(pid, align, vm.search_uint64)

class SearchFloat(__Search):
    def __init__(self, pid, align=False):
        super(SearchFloat, self).__init__(pid, align, vm.search_float)

class SearchDouble(__Search):
    def __init__(self, pid, align=False):
        super(SearchDouble, self).__init__(pid, align, vm.search_double)

class SearchString(__Search):
    def __init__(self, pid):
        super(SearchString, self).__init__(pid, False, vm.search_string)

    def search(self, value):
        self.lastResult = self.searchFn(self.pid, value)
        return self.lastResult
