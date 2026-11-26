#!/usr/bin/env python3
"""Disassemble a range of a DOS MZ executable (16-bit, needs capstone).

    dis16.py PROGRAM.EXE START END       (hex offsets into the load image)

Offsets are linear offsets into the load image (after the MZ header), the
same numbers xrefs.py prints. Far calls are annotated with their linear
target.
"""
import struct
import sys

import capstone


def load_image(path):
    data = open(path, "rb").read()
    return data[struct.unpack_from("<H", data, 8)[0] * 16:]


def main():
    image = load_image(sys.argv[1])
    start, end = int(sys.argv[2], 16), int(sys.argv[3], 16)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)
    for ins in md.disasm(image[start:end], start):
        op = ins.op_str
        if ins.mnemonic == "lcall":
            seg, off = [int(x, 16) for x in op.split(", ")]
            op += "   ; -> %#x" % (seg * 16 + off)
        print("%05x  %-6s %s" % (ins.address, ins.mnemonic, op))


if __name__ == "__main__":
    main()
