import struct, sys, os, re
blob = open(sys.argv[1], "rb").read(); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
for m in re.finditer(b"MZ", blob):
    i = m.start()
    try:
        pe = struct.unpack_from("<I", blob, i + 0x3C)[0]
        if blob[i+pe:i+pe+4] != b"PE\0\0": continue
        nsec = struct.unpack_from("<H", blob, i+pe+6)[0]; opt = struct.unpack_from("<H", blob, i+pe+20)[0]
        sec = i + pe + 24 + opt; end = 0
        for k in range(nsec):
            raw_size, raw_ptr = struct.unpack_from("<II", blob, sec + 40*k + 16)
            end = max(end, raw_ptr + raw_size)
        img = blob[i:i+end]
        name = re.search(rb"([A-Za-z0-9_. -]{3,60}\.(?:exe|dll))\x00", img[-0x4000:] if len(img) > 0x4000 else img)
        dotnet = b"BSJB" in img
        asm = re.findall(rb"\x00([A-Za-z][A-Za-z0-9_.]{2,40})\x00(?:v[0-9])", img[:0])
        p = os.path.join(out, "pe_%x.bin" % i); open(p, "wb").write(img)
        print(hex(i), end, "dotnet" if dotnet else "native", p)
    except struct.error:
        pass
