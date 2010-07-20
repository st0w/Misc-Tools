#!/usr/bin/env python
# ---*< bitstreamer.py >*-----------------------------------------------------
# Copyright (C) 2010 st0w <st0w@st0w.com>
# 
# This code is released under the MIT License.  Do with it whatever the
# hell you want
#
# PyLint has issues with bitarray methods, so don't error on them
# pylint: disable=E1101
#
"""Allows bit-by-bit streaming iteration over a string

Created on 2010-07-17

I wanted an easy way to move through a sequence of data, getting an
arbitrary number of bits at a time, and couldn't find an easy way to do
this otherwise.  :module:`bitarray` comes close, but doesn't do exactly
what I want - so here it is.

Initialization::
    bitstream = bitstreamer(data)
    bitstream.next()

Now the streamer is setup, so to retrieve an arbitrary number of bits,
call :method:`send()`.

To get 8 bits::
    x = bitstream.send(8)

To get 3 bits::
    x = bitstream.send(3)

Note that the return value can optionally vary slightly.  If the
requested number of bits is byte-width (that is, evenly divisible by
8) and :param:`convert_bytes` is True (the default), the returned data
will be converted to a string of bytes before being returned.
Otherwise, the requested data is returned as a string of 0's and 1's.

Example:::
    # Pretend :variable:`data` contains the byte characters 'AB'
    # followed by the bits '0110' and then the characters 'CD'
    bitstream = bitstreamer(data)
    bitstream.next()
    
    # prints 'AB'
    print bitstream.send(16)
    
    # prints '0110'
    print bitstream.send(4)
    
    # prints 'CD'
    print bitstream.send(16)

Also provided is a bytestreamer function.  It works in the same manner,
however it assumes the data are to be provided as bytes only.  So the
parameter to send to :method:`send` is the number of bytes to return.

"""
# ---*< Standard imports >*---------------------------------------------------

# ---*< Third-party imports >*------------------------------------------------
from bitarray import bitarray

# ---*< Local imports >*------------------------------------------------------

# ---*< Initialization >*-----------------------------------------------------
DEBUG = False

# ---*< Code >*---------------------------------------------------------------
def bitstreamer(_bytes="", convert_bytes=True):
    """Sets up a generator for streaming data as a series of bits"""
    __x = 0
    __a = bitarray(endian='big')
    __a.fromstring(_bytes)
    __bitsread = 0

    while True:
        """Update total num bits read"""
        __bitsread += __x

        """Get the requested bits, returns a list of bools"""
        __ret = [__a.pop(0) for __n in range(__x)]

        """Convert the bools to ints"""
        __ret = [int(__n) for __n in __ret]

        """Now a string of 0's and 1's"""
        __ret = "".join([str(__n) for __n in __ret])

        if convert_bytes and len(__ret) % 8 == 0:
            """It's byte width, convert it to a string of bits"""
            __ret = [__ret[__n:__n + 8] for __n in range(0, len(__ret),
                                                         8)]
            """And now to actual bytes"""
            __ret = "".join([chr(int(__n, 2)) for __n in __ret])

        if DEBUG:
            print "Read %s.%s bytes (%s bits)" % (__bitsread / 8,
                                                  __bitsread % 8,
                                                  __bitsread)
        __x = (yield __ret)

def bytestreamer(_bytes=""):
    """Allows retrieval of an arbitrary number of bytes from a
    string at at time, returning the data as a stream
    
    """
    __i = 0
    __x = 0
    while __i < len(_bytes):
        __i += __x
        __x = (yield _bytes[__i - __x:__i])
