// This code is a partial python-c rewrite from "The Cheat" by Charles McGarvey.
//  
// Copyright (c) 2004, Charles McGarvey
// All rights reserved.
// 
// Redistribution and use in source and binary forms, with or without modification, are
// permitted provided that the following conditions are met:
// 
// 1. Redistributions of source code must retain the above copyright notice, this list
// of conditions and the following disclaimer.
// 
// 2. Redistributions in binary form must reproduce the above copyright notice, this
// list of conditions and the following disclaimer in the documentation and/or other
// materials provided with the distribution.
// 
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
// EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
// OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
// SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
// INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
// TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
// BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
// ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
// DAMAGE.
// 



#include <Python.h>
#include <math.h>
#include <time.h>
#include <mach/mach.h>
#include <mach/mach_vm.h>
#include <mach/vm_map.h>
#include <mach/mach_traps.h>
#include <signal.h>


static PyObject *VMRegionError;

enum VMRegionAttributes
{
    VMREGION_READABLE = 1,
    VMREGION_WRITABLE = 2,
    VMREGION_EXECUTABLE = 4
};


typedef struct _VMRegion {
    pid_t pid;
    mach_vm_address_t address;
    mach_vm_size_t size;
    unsigned attributes;
} VMRegion;
const VMRegion VMNullRegion = { 0, 0, 0, 0 };



/****************************************************************
 *** COMPARE FUNCTIONS
 ****************************************************************/

static int compareInt32(void* searchValue, char* buffer) {
    return *((signed int*)searchValue) == *((signed int*)buffer);
}
static int compareUInt32(void* searchValue, char* buffer) {
    return *((unsigned int*)searchValue) == *((unsigned int*)buffer);
}
static int compareInt64(void* searchValue, char* buffer) {
    return *((signed long long*)searchValue) == *((signed long long*)buffer);
}
static int compareUInt64(void* searchValue, char* buffer) {
    return *((unsigned long long*)searchValue) == *((unsigned long long*)buffer);
}
#define EPSILON 0.001
static int compareFloat(void* searchValue, char* buffer) {
    return fabs(*((float*)searchValue) - *((float*)buffer)) < EPSILON;
}
static int compareDouble(void* searchValue, char* buffer) {
    return fabs(*((double*)searchValue) - *((double*)buffer)) < EPSILON;
}
#define ASIZE 256
static void* bmsearch( char *pat, int m, char *text, long n ) {
    int i,j,k,skip[ASIZE];if(m==0)return 0;
    for(k=0;k<ASIZE;k++)skip[k]=m;
    for(k=0;k<m-1;k++)skip[(int)pat[k]]=m-k-1;
    for(k=m-1;k<n;k+=skip[(int)text[k]&(ASIZE-1)]){
    for(j=m-1,i=k;j>=0&&text[i]==pat[j];j--)i--;
    if(j==-1)return(text+i+1);}
    return NULL;
}

/****************************************************************
 *** C FUNCTIONS
 ****************************************************************/
static VMRegion VMNextRegion(pid_t process, VMRegion previous);
static VMRegion VMNextRegionWithAttributes(pid_t process, VMRegion previous, unsigned attribs );
static unsigned VMAttributesFromAddress( pid_t process, mach_vm_address_t address );
static int VMRegionValid(VMRegion region);
static int VMReadBytes(vm_map_t task, mach_vm_address_t address, mach_vm_size_t size, void* buffer);
static int VMGetTask(pid_t pid);


static __inline__ int VMRegionValid(VMRegion region) {
    return region.pid;
}

static VMRegion __inline__ VMMakeRegion( pid_t process, mach_vm_address_t address, mach_vm_size_t size ) {
    VMRegion region;
    region.pid = process;
    region.address = address;
    region.size = size;
    region.attributes = VMAttributesFromAddress( process, address );
    return region;
}

static __inline__ VMRegion VMMakeRegionWithAttributes( pid_t process, mach_vm_address_t address, mach_vm_size_t size, unsigned attribs ) {
    VMRegion region;
    region.pid = process;
    region.address = address;
    region.size = size;
    region.attributes = attribs;
    return region;
}

unsigned VMAttributesFromAddress( pid_t process, mach_vm_address_t address ) {
    vm_map_t task = VMGetTask( process );
    unsigned attribs = 0;

    kern_return_t result;

    mach_vm_size_t size = 0;
    vm_region_basic_info_data_64_t info;
    mach_msg_type_number_t infoCnt = VM_REGION_BASIC_INFO_COUNT_64;
    mach_port_t object_name = 0;

    // get the next region
    result = mach_vm_region( task, &address, &size, VM_REGION_BASIC_INFO_64, (vm_region_info_t)(&info), &infoCnt, &object_name );

    if ( result == KERN_SUCCESS ) {
        // get the attributes
        if ( info.protection & VM_PROT_READ ) {
            attribs |= VMREGION_READABLE;
        }
        if ( info.protection & VM_PROT_WRITE ) {
            attribs |= VMREGION_WRITABLE;
        }
        if ( info.protection & VM_PROT_EXECUTE ) {
            attribs |= VMREGION_EXECUTABLE;
        }
        // return the region attributes
        return attribs;
    }
    return 0;
}

static VMRegion VMNextRegion( pid_t process, VMRegion previous ) {
    vm_map_t task = VMGetTask( process );
    unsigned attribs = 0;

    kern_return_t result;

    mach_vm_address_t address = 0x0;
    mach_vm_size_t size = 0;
    vm_region_basic_info_data_64_t info;
    mach_msg_type_number_t infoCnt = VM_REGION_BASIC_INFO_COUNT_64;
    mach_port_t object_name = 0;

    if ( VMRegionValid( previous ) ) {
        address = previous.address + previous.size;
    }

    // get the next region
    result = mach_vm_region( task, &address, &size, VM_REGION_BASIC_INFO_64, (vm_region_info_t)(&info), &infoCnt, &object_name );

    if ( result == KERN_SUCCESS ) {
        // get the attributes
        if ( info.protection & VM_PROT_READ ) {
            attribs |= VMREGION_READABLE;
        }
        if ( info.protection & VM_PROT_WRITE ) {
            attribs |= VMREGION_WRITABLE;
        }
        if ( info.protection & VM_PROT_EXECUTE ) {
            attribs |= VMREGION_EXECUTABLE;
        }
        // return the region
        return VMMakeRegionWithAttributes( process, address, size, attribs );
    }

    return VMNullRegion;
}


static VMRegion VMNextRegionWithAttributes( pid_t pid, VMRegion previous, unsigned attribs ) {
    VMRegion region;

    while (VMRegionValid(region= VMNextRegion(pid, previous) ) )
    {
        if ( (attribs & region.attributes) == attribs ) {
            // pass back this region if the attributes match
            return region;
        }
        previous = region;
    }

    return VMNullRegion;
}


PyObject * search(pid_t process, void* searchValue, int(*compareFn)(void*,char*), int dataWidth, int step) {
    VMRegion region;
    PyObject* results = PyList_New(0);
    char *ptr, *top;
    mach_vm_address_t offset;
    char *buf = malloc( (size_t)1 );
    size_t bufSize=1;
    
    region = VMNextRegionWithAttributes( process, VMNullRegion, VMREGION_READABLE | VMREGION_WRITABLE );
    vm_map_t task = VMGetTask(process);
    
    while ( VMRegionValid( region ) ) {
        // resize buffer if needed
        if(bufSize < (size_t)region.size) {
            free(buf);
            buf = malloc( (size_t)region.size );
            if ( buf==NULL ) {
                return PyErr_NoMemory();
            }
        }

        if (VMReadBytes(task, region.address, region.size, buf)!=0) {
            return NULL;
        }
        
        ptr = buf;
        top = buf + region.size - dataWidth + 1;
        offset = region.address - (mach_vm_address_t)buf;
        while ( ptr < top ) {
            if(compareFn(searchValue, ptr)) {
                PyList_Append(results, Py_BuildValue("l", (offset+ptr)));
            }
            ptr+=step;
        }

        region = VMNextRegionWithAttributes( process, region, VMREGION_READABLE | VMREGION_WRITABLE );
    }
    free(buf);
    return results;
}


PyObject * search_string(pid_t process, char* searchValue, int searchValueSize) {
    VMRegion region;
    PyObject* results = PyList_New(0);
    char *ptr, *top;
    mach_vm_address_t offset;
    void *hit;
    char *buf = malloc( (size_t)1 );
    size_t bufSize=1;
    
    region = VMNextRegionWithAttributes( process, VMNullRegion, VMREGION_READABLE | VMREGION_WRITABLE );
    vm_map_t task = VMGetTask(process);
    
    while ( VMRegionValid( region ) ) {
        // resize buffer if needed
        if(bufSize < (size_t)region.size) {
            free(buf);
            buf = malloc( (size_t)region.size );
            if ( buf==NULL ) {
                return PyErr_NoMemory();
            }
        }

        if (VMReadBytes(task, region.address, region.size, buf)!=0) {
            return NULL;
        }
        
        ptr = buf;
        top = buf + region.size;
        offset = region.address - (mach_vm_address_t)buf;

        while ( (hit = bmsearch(searchValue, searchValueSize, ptr, top-ptr))!=0 ) {
            PyList_Append(results, Py_BuildValue("l", (offset+hit)));
            ptr = hit + 1;
        }

        region = VMNextRegionWithAttributes( process, region, VMREGION_READABLE | VMREGION_WRITABLE );
    }
    free(buf);
    return results;
}

static int VMGetTask(pid_t pid) {
    vm_map_t task;
    kern_return_t result;

    result = task_for_pid( mach_task_self(), pid, &task );
    if (result != KERN_SUCCESS) {
        return 0;
    }
    
    return task;
}


static int VMReadBytes(vm_map_t task, mach_vm_address_t address, mach_vm_size_t size, void* buffer) {
    kern_return_t result;
    mach_vm_size_t staticsize = size;

    if (task == 0) {
        PyErr_SetString(VMRegionError, "Can't find PID!");
        return 1;
    }

    result = mach_vm_read_overwrite( task, address, staticsize, (vm_offset_t)buffer, &size );
    if (result != KERN_SUCCESS) {
        PyErr_SetString(VMRegionError, "Can't read memory address!");
        return 2;
    }
    
    return 0;
}

static int VMWriteBytes(vm_map_t task, mach_vm_address_t address, mach_vm_size_t size, void* buffer) {
    kern_return_t result;

    if (task == 0) {
        PyErr_SetString(VMRegionError, "Can't find PID!");
        return 1;
    }
    
    result = mach_vm_write(task, address, (vm_offset_t)buffer, (mach_msg_type_number_t)size );
    if (result != KERN_SUCCESS) {
        PyErr_SetString(VMRegionError, "Can't write memory address!");
        return 2;
    }
    
    return 0;
}






/****************************************************************
 *** PYTHON FUNCTIONS
 ****************************************************************/

/*
static PyObject *py_next_region(PyObject *self, PyObject *args) {
    int pid;
    long address;
    long size;
    unsigned attributes;
    
    if (!PyArg_ParseTuple(args, "illi", &pid, &address, &size, &attributes))
        return NULL;
    
    
    VMRegion region = VMMakeRegion( (pid_t) pid, (mach_vm_address_t) address, (mach_vm_size_t) size );
    region = VMNextRegion((pid_t) pid, region);
    return Py_BuildValue("illi", region.pid, region.address, region.size, region.attributes);
}

static PyObject *py_next_region_with_attributes(PyObject *self, PyObject *args) {
    int pid;
    long address;
    long size;
    unsigned attributes;
    
    if (!PyArg_ParseTuple(args, "illi", &pid, &address, &size, &attributes))
        return NULL;
    
    
    VMRegion region = VMMakeRegionWithAttributes( (pid_t) pid, (mach_vm_address_t) address, (mach_vm_size_t) size, attributes );
    region = VMNextRegionWithAttributes((pid_t) pid, region, attributes);
    return Py_BuildValue("illi", region.pid, region.address, region.size, region.attributes);
}*/


static PyObject *py_search_int32(PyObject *self, PyObject *args) {
    int pid;
    int searchValue;
    int align;
    
    if (!PyArg_ParseTuple(args, "iii", &pid, &searchValue, &align))
        return NULL;

    return search( (pid_t) pid, &searchValue, compareInt32, 4, align ? 4 : 1);
}

static PyObject *py_search_uint32(PyObject *self, PyObject *args) {
    int pid;
    unsigned int searchValue;
    int align;
    
    if (!PyArg_ParseTuple(args, "iIi", &pid, &searchValue, &align))
        return NULL;

    return search( (pid_t) pid, &searchValue, compareUInt32, 4, align ? 4 : 1);
}

static PyObject *py_search_int64(PyObject *self, PyObject *args) {
    int pid;
    long long searchValue;
    int align;
    
    if (!PyArg_ParseTuple(args, "iLi", &pid, &searchValue, &align))
        return NULL;

    return search( (pid_t) pid, &searchValue, compareInt64, 8, align ? 4 : 1);
}

static PyObject *py_search_uint64(PyObject *self, PyObject *args) {
    int pid;
    unsigned long long searchValue;
    int align;
    
    if (!PyArg_ParseTuple(args, "iKi", &pid, &searchValue, &align))
        return NULL;

    return search( (pid_t) pid, &searchValue, compareUInt64, 8, align ? 4 : 1);
}

static PyObject *py_search_float(PyObject *self, PyObject *args) {
    int pid;
    float searchValue;
    int align;
    
    if (!PyArg_ParseTuple(args, "ifi", &pid, &searchValue, &align))
        return NULL;

    return search( (pid_t) pid, &searchValue, compareFloat, 8, align ? 4 : 1);
}

static PyObject *py_search_double(PyObject *self, PyObject *args) {
    int pid;
    double searchValue;
    int align;
    
    if (!PyArg_ParseTuple(args, "idi", &pid, &searchValue, &align))
        return NULL;

    return search( (pid_t) pid, &searchValue, compareDouble, 8, align ? 4 : 1);
}

static PyObject *py_search_string(PyObject *self, PyObject *args) {
    int pid;
    char * searchValue;
    int searchValueLength;
    
    if (!PyArg_ParseTuple(args, "is#", &pid, &searchValue, &searchValueLength))
        return NULL;

    return search_string( (pid_t) pid, searchValue, searchValueLength);
}


static PyObject *py_read_bytes(PyObject *self, PyObject *args) {
    pid_t pid;
    mach_vm_address_t address;
    mach_vm_size_t size;
    char *bytes;

    // Arg-Parse: (int) pid, (long) address, (long) sizetoread
    if (!PyArg_ParseTuple(args, "ill", &pid, &address, &size))
        return NULL;

    bytes=PyMem_Malloc((size_t)size);
    
    if(VMReadBytes(VMGetTask(pid),address,size,bytes) != 0) {
        return NULL;
    }

    return Py_BuildValue("s#", bytes, size);
}

static PyObject *py_read_int64(PyObject *self, PyObject *args) {
    pid_t pid;
    mach_vm_address_t address;
    long long value;
    
    // Arg-Parse: (int) pid, (long) address, (long) sizetoread
    if (!PyArg_ParseTuple(args, "il", &pid, &address))
        return NULL;
    
    if(VMReadBytes(VMGetTask(pid),address,8,&value) != 0) {
        return NULL;
    }

    return Py_BuildValue("L", value);
}

static PyObject *py_read_uint32(PyObject *self, PyObject *args) {
    pid_t pid;
    mach_vm_address_t address;
    unsigned int value;
    
    // Arg-Parse: (int) pid, (long) address, (long) sizetoread
    if (!PyArg_ParseTuple(args, "il", &pid, &address))
        return NULL;
    
    if(VMReadBytes(VMGetTask(pid),address,4,&value) != 0) {
        return NULL;
    }

    return Py_BuildValue("I", value);
}

static PyObject *py_read_int32(PyObject *self, PyObject *args) {
    pid_t pid;
    mach_vm_address_t address;
    int value;
    
    // Arg-Parse: (int) pid, (long) address, (long) sizetoread
    if (!PyArg_ParseTuple(args, "il", &pid, &address))
        return NULL;
    
    if(VMReadBytes(VMGetTask(pid),address,4,&value) != 0) {
        return NULL;
    }

    return Py_BuildValue("i", value);
}

static PyObject *py_read_uint64(PyObject *self, PyObject *args) {
    pid_t pid;
    mach_vm_address_t address;
    unsigned long long value;
    
    // Arg-Parse: (int) pid, (long) address, (long) sizetoread
    if (!PyArg_ParseTuple(args, "il", &pid, &address))
        return NULL;
    
    if(VMReadBytes(VMGetTask(pid),address,8,&value) != 0) {
        return NULL;
    }

    return Py_BuildValue("K", value);
}



static PyObject *py_write_bytes(PyObject *self, PyObject *args) {
    pid_t pid;
    mach_vm_address_t address;
    mach_vm_size_t size;
    char *bytes;
    kern_return_t result;
    vm_map_t task;
    
    // Arg-Parse: (int) pid, (long) address, (char*) bytes
    if (!PyArg_ParseTuple(args, "ils#", &pid, &address, &bytes, &size))
        return NULL;


    if(VMWriteBytes(VMGetTask(pid),address,size,bytes) != 0) {
        return NULL;
    }

    result = task_for_pid( mach_task_self(), pid, &task );
    if (result != KERN_SUCCESS) {
        PyErr_SetString(VMRegionError, "Can't find PID!");
        return NULL;
    }

    return Py_BuildValue("");
}


/****************************************************************
 *** PYTHON INIT
 ****************************************************************/

static PyMethodDef MyMethods[] = {

    {"search_int32",  py_search_int32, METH_VARARGS, "Searches an 32-bit integer value"},
    {"search_uint32",  py_search_uint32, METH_VARARGS, "Searches an unsigned 32-bit integer value"},
    {"search_int64",  py_search_int64, METH_VARARGS, "Searches an 64-bit integer value"},
    {"search_uint64",  py_search_uint64, METH_VARARGS, "Searches an unsigned 64-bit integer value"},
    {"search_float",  py_search_float, METH_VARARGS, "Searches a float value"},
    {"search_double",  py_search_double, METH_VARARGS, "Searches a double value"},
    {"search_string",  py_search_string, METH_VARARGS, "Searches an string value"},
    {"read_bytes",  py_read_bytes, METH_VARARGS, "Reads the number of bytes fro the given process id at the given address."},
    {"read_int32",  py_read_int32, METH_VARARGS, "Reads an 32-bit integer value from the given address."},
    {"read_uint32",  py_read_uint32, METH_VARARGS, "Reads an unsigned 32-bit integer value from the given address."},
    {"read_int64",  py_read_int64, METH_VARARGS, "Reads an 64-bit integer value from the given address."},
    {"read_uint64",  py_read_uint64, METH_VARARGS, "Reads an unsigned 64-bit integer value from the given address."},
    {"write_bytes",  py_write_bytes, METH_VARARGS, "Writes the given bytes at the prid's given address"},

    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC initvmregion(void) {
    PyObject *m;

    m = Py_InitModule("vmregion", MyMethods);
    if (m == NULL)
        return;
    
    VMRegionError = PyErr_NewException("vmregion.error", NULL, NULL);
    Py_INCREF(VMRegionError);
    PyModule_AddObject(m, "error", VMRegionError);
}




