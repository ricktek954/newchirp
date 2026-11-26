"""Undo Inno Setup's TransformCallInstructions (decode), 64 KB buffers."""
import sys
data = bytearray(open(sys.argv[1], "rb").read())
BLOCK = 0x10000
for start in range(0, len(data), BLOCK):
    end = min(start + BLOCK, len(data))
    size = end - start
    if size < 5:
        continue
    limit = size - 4
    i = 0
    while i < limit:
        b = data[start + i]
        if b in (0xE8, 0xE9):
            i += 1
            p = start + i
            if data[p + 3] in (0x00, 0xFF):
                addr = (start + i + 4) & 0xFFFFFF
                rel = data[p] | (data[p + 1] << 8) | (data[p + 2] << 16)
                rel = (rel - addr) & 0xFFFFFF
                if rel & 0x800000:
                    data[p + 3] ^= 0xFF
                data[p] = rel & 0xFF; data[p + 1] = (rel >> 8) & 0xFF; data[p + 2] = (rel >> 16) & 0xFF
            i += 4
        else:
            i += 1
open(sys.argv[2], "wb").write(data)
