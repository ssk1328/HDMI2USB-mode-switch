#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 et sts=4 ai:

from __future__ import print_function

import binascii
import crcmod
import ctypes
import time

from utils import *

from tofe_eeprom import DynamicLengthStructure

class FX2Config(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("format", ctypes.c_uint8),
        ("vid", ctypes.c_uint16),
        ("pid", ctypes.c_uint16),
        ("did", ctypes.c_uint16),
        ("cfg", ctypes.c_uint8),
    ]

    VID_NUMATO = 0x2A19
    PID_OPSIS_UNCONFIG = 0x5440

    def populate(self):
        self.format = 0xC2
        self.vid = self.VID_NUMATO
        self.pid = self.PID_OPSIS_UNCONFIG
        self.cfg = 1 << 6

    def check(self):
        assert_eq(self.vid, self.VID_NUMATO)
        assert_eq(self.pid, self.PID_OPSIS_UNCONFIG)
        for seg in self.segments():
            seg.check()

    def segments(self):
        segs = []
        segment = self.next()
        while segment is not None:
            segs.append(segment)
            segment = segment.next()
        return segs

    def next(self):
        if self.format == 0xC2:
            return FX2DataSegment.from_address(ctypes.addressof(self)+ctypes.sizeof(self))

    def __repr__(self):
        return "FX2Config(0x%X, vid=0x%04X, pid=0x%04X, did=0x%04X, cfg=0x%02X)" % (self.format, self.vid, self.pid, self.did, self.cfg)

    def c_struct(self):
        segs = self.segments()
        s = []
        s.append("""\

union {
    struct {
        struct {
            __u8    format;
            __le16  vid;
            __le16  pid;
            __le16  did;
            __u8    cfg;
        } __attribute__ ((packed)) header;
""")
        for i, seg in enumerate(segs):
            s.append("""\
        struct {
            __be16  len;
            __be16  addr;
            __u8    data[%i];
        } __attribute__ ((packed)) data%i;
""" % (seg._len, i))
        s.append("""\
    };
    __u8 bytes[%i];
} fx2_config = {
    .header = {
        .format     = 0x%02X,
        .vid        = htole16c(0x%04X),
        .pid        = htole16c(0x%04X),
        .did        = htole16c(0x%04X),
        .cfg        = 0x%02X,
    },
""" % (self.totalsize, self.format, self.vid, self.pid, self.did, self.cfg))
        for i, seg in enumerate(segs):
            s.append("""\
    .data%s = {
        .len        = htobe16c(0x%04X),
        .addr       = htobe16c(0x%04X),
        .data       = {
            """ % (i, seg._len, seg.addr))
            for j, b in enumerate(seg.data):
                s.append("0x%02X, " % b)
                if (j+1) % 10 == 0:
                    s.append("""
            """)
            s.append("""
        }
    },
""")
        s.append("""\
};
""")
        return "".join(s)

    @property
    def totalsize(self):
        l = ctypes.sizeof(self.__class__)
        for seg in self.segments():
            l += ctypes.sizeof(seg.__class__)
            l += seg._len
        return l


class FX2DataSegment(ctypes.BigEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("_last", ctypes.c_uint16, 1),
        ("_len", ctypes.c_uint16, 15),
        ("addr", ctypes.c_uint16),
        ("_data", ctypes.c_ubyte * 0),
    ]

    @property
    def last(self):
        return bool(self._last)

    @property
    def data(self):
        addr = ctypes.addressof(self)
        return (ctypes.c_ubyte * self._len).from_address(addr+self.__class__._data.offset)

    def next(self):
        if self.last:
            return None
        addr = ctypes.addressof(self)
        addr += ctypes.sizeof(self)
        addr += self._len
        return self.__class__.from_address(addr)

    def check(self):
        if self.last:
            assert_eq(self._len, 1)
            assert_eq(self.addr, 0xe600)
            assert_eq(self.data[0], 0x00)
        else:
            assert 0 <= self.addr <= 0x3FFF or 0xE00 <= self.addr <= 0xE1FF, self.addr

    def __repr__(self):
        return "FX2DataSegment(0x%04x, {...}[%i])" % (self.addr, self._len)

    def make_last(self):
        self._last = 1
        self.addr = 0xE600
        self._len = 1
        self.data[:] = [0x00]

    def clear(self):
        self._last = 0
        self.addr = 0
        self._len = 0
        assert len(self.data) == 0, len(self.data)


def from_hexfile(filename):
    import hexfile
    hexf = hexfile.load(filename)

    # Work out the number of bytes needed
    totalsize = ctypes.sizeof(FX2Config)
    for segment in hexf.segments:
        totalsize += ctypes.sizeof(FX2DataSegment)
        totalsize += segment.size
    totalsize += ctypes.sizeof(FX2DataSegment) + 1

    backbuffer = bytearray(totalsize)

    # FX2 header
    fx2cfg = FX2Config.from_buffer(backbuffer)
    fx2cfg.buffer = backbuffer
    fx2cfg.populate()

    # FX2 data segments
    fx2seg = fx2cfg.next()
    assert fx2seg
    for i, segment in enumerate(hexf.segments):
        fx2seg.addr = segment.start_address
        fx2seg._len = segment.size
        fx2seg.data[:] = segment.data[:]
        fx2seg = fx2seg.next()
        assert fx2seg

    # Terminal segment
    fx2seg.make_last()

    assert_eq(totalsize, fx2cfg.totalsize)

    return fx2cfg


microboot_cfg = from_hexfile("microboot.hex")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        fx2cfg = from_hexfile(sys.argv[-1])
    else:
        fx2cfg = microboot_cfg

    l = len(fx2cfg.buffer)
    sys.stderr.write("FX2 Config: %s bytes (~%.1fk)\n" % (l, l/1024))
    sys.stderr.write("In 128 EEPROM, leaves %5i bytes\n" % (128-l))
    left_16k = 1024*16-l
    sys.stderr.write("In 16k EEPROM, leaves %i bytes (~%.1fk)\n" % (left_16k, left_16k/1024))
    sys.stderr.write("-"*10+"\n")
    sys.stderr.write("%r\n" % fx2cfg)
    for s in fx2cfg.segments():
        sys.stderr.write("%r\n" % s)
    sys.stdout.write("""\
#include <endian.h>
#include <asm/types.h>

// Constant versions of the htobe functions for use in the structures
#if __BYTE_ORDER == __LITTLE_ENDIAN
# define htobe16c(x) __bswap_constant_16(x)
# define htole16c(x) (x)
#else
# define htobe16c(x) (x)
# define htole16c(x) _bswap_constant_16(x)
#endif

typedef __u16 __le16;
typedef __u16 __be16;

""")
    sys.stdout.write(fx2cfg.c_struct())
    sys.stdout.write("""\
#include <stdio.h>
int main() {
    size_t i = 0;
    printf("000000 ");
    for(i = 0; i < sizeof(fx2_config); i++) {
        printf("%02X ", fx2_config.bytes[i]);
        if ((i+1) % 8 == 0)
            printf("\\n%06zd ", i+1);
    }
    printf("\\n");
    return 0;
}
""")
