#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set ts=4 sw=4 et sts=4 ai:

from __future__ import print_function

import binascii
import crcmod
import ctypes
import time
import re

from utils import *

from tofe_eeprom import DynamicLengthStructure

class _ConfigCommon(ctypes.LittleEndianStructure):

    def segments(self):
        segs = []
        segment = self.next()
        while segment is not None:
            segs.append(segment)
            segment = segment.next()
        return segs

    @property
    def totalsize(self):
        l = ctypes.sizeof(self.__class__)
        for seg in self.segments():
            l += ctypes.sizeof(seg.__class__)
            l += seg._len
        return l


class _DataSegment(ctypes.BigEndianStructure):

    @property
    def data(self):
        addr = ctypes.addressof(self)
        return (ctypes.c_ubyte * self._len).from_address(addr+self.__class__._data.offset)

    @property
    def len_bits(self):
        return int(re.search("bits=([0-9]+)", repr(self.__class__._len)).groups()[0])+1

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
        return "%s(0x%04x, {...}[%i])" % (self.__class__.__name__, self.addr, self._len)

    @property
    def last(self):
        return bool(self._last)

    def make_last(self):
        self._last = 1

    def clear(self):
        self._last = 0
        self.addr = 0
        self._len = 0
        assert len(self.data) == 0, len(self.data)

    def c_struct(self, name):
        return """\
        struct {
            __be%i  len;
            __be16  addr;
            __u8    data[%i];
        } __attribute__ ((packed)) %s""" % (
            self.len_bits, self._len, name)

    def c_fill(self):

        s = []
        s.append("""{
        .len        = htobe%ic(0x%02X)%s,
        .addr       = htobe16c(0x%04X),
        .data       = {
            """ % (self.len_bits, self._len, ['',  ' | (1 << %s)' % (self.len_bits-1)][self.last], self.addr))
        for j, b in enumerate(self.data):
            s.append("0x%02X, " % b)
            if (j+1) % 8 == 0:
                s.append("""
            """)
        s.append("""
        }
    }""")
        return "".join(s)


class FX2DataSegment(_DataSegment):
    _pack_ = 1
    _fields_ = [
        ("_last", ctypes.c_uint16, 1),
        ("_len", ctypes.c_uint16, 15),
        ("addr", ctypes.c_uint16),
        ("_data", ctypes.c_ubyte * 0),
    ]

    def make_last(self):
        _DataSegment.make_last(self)
        self.addr = 0xE600
        self._len = 1
        self.data[:] = [0x00]



class FX2Config(_ConfigCommon):
    _pack_ = 1
    _fields_ = [
        ("format", ctypes.c_uint8),
        ("vid", ctypes.c_uint16),
        ("pid", ctypes.c_uint16),
        ("did", ctypes.c_uint16),
        ("cfg", ctypes.c_uint8),
    ]
    _segment_cls = FX2DataSegment

    VID_NUMATO = 0x2A19
    PID_OPSIS_UNCONFIG = 0x5440

    @property
    def has_segments(self):
        return self.format == 0xC2

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

    def next(self):
        if self.format == 0xC2:
            return FX2DataSegment.from_address(ctypes.addressof(self)+ctypes.sizeof(self))

    def __repr__(self):
        return "FX2Config(0x%X, vid=0x%04X, pid=0x%04X, did=0x%04X, cfg=0x%02X)" % (self.format, self.vid, self.pid, self.did, self.cfg)

    def c_struct(self, name):
        segs = self.segments()
        s = []
        s.append("""\
union %s_t {
    struct {
        struct {
            __u8    format;
            __le16  vid;
            __le16  pid;
            __le16  did;
            __u8    cfg;
        } __attribute__ ((packed)) header;
""" % name)
        for i, seg in enumerate(segs):
            s.append(seg.c_struct("data%i" % i))
            s.append(";\n")
        s.append("""\
    };
    __u8 bytes[%i];
} %s""" % (self.totalsize, name))
        return "".join(s)

    def c_fill(self):
        s = []
        segs = self.segments()
        s.append("""{
    .header = {
        .format     = 0x%02X,
        .vid        = htole16c(0x%04X),
        .pid        = htole16c(0x%04X),
        .did        = htole16c(0x%04X),
        .cfg        = 0x%02X,
    },
""" % (self.format, self.vid, self.pid, self.did, self.cfg))
        for i, seg in enumerate(segs):
            s.append("""\
    .data%s = """ % i)
            s.append(seg.c_fill())
            s.append(",\n")
        s.append("""\
};
""")
        return "".join(s)

    def c_code(self, name="fx2fw"):
        return "".join([
            self.c_struct(name),
            " = ",
            self.c_fill(),
        ])


class MicrobootSegment(_DataSegment):
    _pack_ = 1
    _fields_ = [
        ("_last", ctypes.c_uint8, 1),
        ("_len", ctypes.c_uint8, 7),
        ("addr", ctypes.c_uint16),
        ("_data", ctypes.c_ubyte * 0),
    ]

    MAX_LEN = 2**7-1

    def make_last(self):
        self._last = 1
        self._len = 0
        self.addr = 0
        self._data[:] = []


class MicrobootConfig(_ConfigCommon):
    _pack_ = 1
    _fields_ = []

    def next(self):
        return MicrobootSegment.from_address(ctypes.addressof(self))

    def c_struct(self, name):
        segs = self.segments()
        s = []
        s.append("""\
#define FX2_FIRMWARE_END offsetof(union %s_t, data%i)+1
""" % (name, len(segs)-1))
        s.append("""\
union %s_t {
    struct {
""" % name)
        for i, seg in enumerate(segs):
            s.append(seg.c_struct("data%i" % i))
            s.append(";\n")
        s.append("""\
    };
    __u8 bytes[%i];
} %s""" % (self.totalsize, name))
        return "".join(s)

    def c_fill(self):
        s = []
        segs = self.segments()
        s.append("""{
""")
        for i, seg in enumerate(segs):
            s.append("""\
    .data%s = """ % i)
            s.append(seg.c_fill())
            s.append(",\n")
        s.append("""\
};
""")
        return "".join(s)

    def c_code(self, name="fx2fw"):
        return "".join([
            self.c_struct(name),
            " = ",
            self.c_fill(),
        ])


def fx2cfg_from_hexfile(filename):
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


def microboot_from_hexfile(filename):
    import hexfile
    hexf = hexfile.load(filename)

    # Work out the number of bytes needed
    totalsize = ctypes.sizeof(MicrobootConfig)
    for i, segment in enumerate(hexf.segments):
        start = 0
        while True:
            totalsize += ctypes.sizeof(MicrobootSegment)
            partsize = min(MicrobootSegment.MAX_LEN, segment.size - start)
            start += partsize
            if start >= segment.size:
                break
        totalsize += segment.size
    totalsize += ctypes.sizeof(MicrobootSegment)

    backbuffer = bytearray(totalsize+100)

    # FX2 header
    mb2cfg = MicrobootConfig.from_buffer(backbuffer)
    mb2cfg.buffer = backbuffer

    # FX2 data segments
    mb2seg = mb2cfg
    for i, segment in enumerate(hexf.segments):
        start = 0
        while True:
            mb2seg = mb2seg.next()
            partsize = min(mb2seg.MAX_LEN, segment.size - start)
            mb2seg.addr = segment.start_address + start
            mb2seg._len = partsize
            mb2seg.data[:] = segment.data[start:start+partsize]
            start += partsize
            if start >= segment.size:
                break

    mb2seg = mb2seg.next()
    mb2seg.make_last()
    assert_eq(totalsize, mb2cfg.totalsize)

    return mb2cfg


microboot_cfg = fx2cfg_from_hexfile("microboot.hex")

if __name__ == "__main__":
    import os
    import sys
    name = ""
    if len(sys.argv) > 1:
        fx2cfg = fx2cfg_from_hexfile(sys.argv[1])
        mb2cfg = microboot_from_hexfile(sys.argv[1])
        name = "_"+(os.path.splitext(os.path.basename(sys.argv[1]))[0]).lower()
    else:
        fx2cfg = microboot_cfg
        mb2cfg = microboot_from_hexfile("microboot.hex")

    l = len(fx2cfg.buffer)
    sys.stderr.write("FX2 Config: %s bytes (~%.1fk)\n" % (l, l/1024))
    sys.stderr.write("In 128 EEPROM, leaves %5i bytes\n" % (128-l))
    left_16k = 1024*16-l
    sys.stderr.write("In 16k EEPROM, leaves %i bytes (~%.1fk)\n" % (left_16k, left_16k/1024))
    sys.stderr.write("-"*10+"\n")
    sys.stderr.write("%r\n" % fx2cfg)
    for s in fx2cfg.segments():
        sys.stderr.write("%r\n" % s)
    sys.stderr.write("-"*10+"\n")
    for s in mb2cfg.segments():
        sys.stderr.write("%r\n" % s)

    sys.stdout.write("""\
#include <endian.h>
#include <stdint.h>

#ifndef __bswap_constant_16
#define __bswap_constant_16(x) \
    ((unsigned short int) ((((x) >> 8) & 0xff) | (((x) & 0xff) << 8)))
#endif

// Constant versions of the htobe functions for use in the structures
#if __BYTE_ORDER == __LITTLE_ENDIAN
# define htobe16c(x) __bswap_constant_16(x)
# define htole16c(x) (x)
#else
# define htobe16c(x) (x)
# define htole16c(x) __bswap_constant_16(x)
#endif

typedef uint8_t __u8;
typedef uint16_t __le16;
typedef uint16_t __be16;

typedef __u8 __le8;
typedef __u8 __be8;
#define htobe8c(x) (x)
#define htole8c(x) (x)
""")
    #sys.stdout.write(fx2cfg.c_code("fx2fw"))
    sys.stdout.write(mb2cfg.c_code("fx2_mbfw" + name))
    if len(sys.argv) > 2:
        sys.stdout.write(r"""\

#include <stdio.h>

int main() {
    size_t i = 0;
    printf("FX2 Firmware\n");
    printf("------------------------------\n");
    printf("000000 ");
    for(i = 0; i < sizeof(fx2fw); i++) {
        printf("%02X ", fx2fw.bytes[i]);
        if ((i+1) % 8 == 0)
            printf("\n%06zd ", i+1);
    }
    printf("\n\n");
    printf("MB Firmware\n");
    printf("------------------------------\n");
    printf("000000 ");
    for(i = 0; i < sizeof(mb2fw); i++) {
        printf("%02X ", mb2fw.bytes[i]);
        if ((i+1) % 8 == 0)
            printf("\n%06zd ", i+1);
    }
    printf("\n");
    return 0;
}
""")
