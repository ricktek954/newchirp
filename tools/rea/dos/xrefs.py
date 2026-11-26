#!/usr/bin/env python3
"""Find references in a DOS MZ executable's load image.

    xrefs.py PROGRAM.EXE string TEXT     where a byte string sits (e.g. PROGRAM)
    xrefs.py PROGRAM.EXE data 0x32d4     mov al,[x] / mov ax,x / cmp ..,[x] users
    xrefs.py PROGRAM.EXE call 0x16782    near calls (E8) to a linear offset
    xrefs.py PROGRAM.EXE int14           BIOS serial (INT 14h) call sites

KPG-32D example (2026-11-26): the constant table "PROGRAM 00 02 S X 15 06
80 E E7 ... 03 Z" sits at DS:0x32CA; data refs to 0x32d4 ('X') and
0x32df ('Z') led to the read (0x16468) and write (0x168a9) paths.
"""
import re
import struct
import sys


def load_image(path):
    data = open(path, "rb").read()
    return data[struct.unpack_from("<H", data, 8)[0] * 16:]


def main():
    image = load_image(sys.argv[1])
    kind = sys.argv[2]
    if kind == "string":
        text = sys.argv[3].encode()
        for m in re.finditer(re.escape(text), image):
            i = m.start()
            print(hex(i), image[i - 2:i + 32].hex(" "))
    elif kind == "data":
        target = struct.pack("<H", int(sys.argv[3], 16))
        for name, prefix in (("mov al,[x]", b"\xa0"), ("mov ax,x", b"\xb8"),
                             ("mov ax,[x]", b"\xa1"), ("cmp/mov r,[x]", b"\x8a\x1e")):
            hits = [hex(m.start()) for m in
                    re.finditer(re.escape(prefix + target), image)]
            if hits:
                print(name, hits)
    elif kind == "call":
        target = int(sys.argv[3], 16)
        hits = [hex(i) for i in range(len(image) - 3) if image[i] == 0xE8
                and i + 3 + struct.unpack_from("<h", image, i + 1)[0] == target]
        print(hits)
    elif kind == "int14":
        for m in re.finditer(b"\xcd\x14", image):
            print("int 0x14 at", hex(m.start()))
        for m in re.finditer(bytes.fromhex("b8140050") + b"\x9a", image):
            off, seg = struct.unpack_from("<HH", image, m.start() + 5)
            print("int86(0x14) call at", hex(m.start()), "-> %#x" % (seg * 16 + off))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
