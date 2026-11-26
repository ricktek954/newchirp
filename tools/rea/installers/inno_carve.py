"""Carve Inno Setup zlb chunks (raw LZMA1) from an installer, without running it."""
import lzma, struct, sys, os
data = open(sys.argv[1], "rb").read(); out = sys.argv[2]
pos = 0; n = 0
while True:
    i = data.find(b"zlb\x1a", pos)
    if i < 0: break
    pos = i + 4
    props = data[i+4:i+9]
    d = props[0]; lc = d % 9; d //= 9; lp = d % 5; pb = d // 5
    dict_size = struct.unpack("<I", props[1:5])[0]
    if lc > 8 or dict_size == 0 or dict_size > 1 << 28: continue
    filt = [{"id": lzma.FILTER_LZMA1, "lc": lc, "lp": lp, "pb": pb, "dict_size": dict_size}]
    dec = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=filt)
    try:
        blob = dec.decompress(data[i+9:], max_length=64 << 20)
    except lzma.LZMAError:
        blob = b""
    if len(blob) < 1024: continue
    p = os.path.join(out, "chunk_%02d_at_%x.bin" % (n, i)); open(p, "wb").write(blob)
    print(p, len(blob), blob.count(b"MZ"), b"BSJB" in blob); n += 1
