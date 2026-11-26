#!/usr/bin/env python3
"""Simulated TK-259/TK-359 for tracing KPG-32D reads and writes in QEMU.

    kpg32d_radio.py IMAGE.FDT [--fill-blank]

Serves IMAGE (0x53FF bytes) on 127.0.0.1:47350 and logs every byte to
kpg32d_radio.log; writes land in kpg32d_written.bin.

Protocol as traced 2026-11-26 (docs/KPG23_PROTOCOL.md). Addresses are
03 <hi+0xAC> <lo> (0x03AC00 + offset, no carry):
  PROGRAM -> 06;  02 -> 8-byte identity (image 0x0500);  06/15/E -> 06
  S addr n -> X addr n + n bytes + sum8, or with --fill-blank, Z addr n +
              one byte for a uniform block (what real radios do)
  Z addr n fill -> 06                       (write, uniform block)
  X addr n + n bytes + sum8 -> 06, then 03 -> 06   (write, data block)
"""
import argparse
import socket
import time


def offset_of(address):
    return (((address[1] - 0xAC) & 0xFF) << 8) | address[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--fill-blank", action="store_true")
    args = parser.parse_args()
    mem = bytearray(open(args.image, "rb").read().ljust(0x5400, b"\xff"))
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 47350))
    srv.listen(1)
    log = open("kpg32d_radio.log", "a", buffering=1)
    while True:
        conn, _ = srv.accept()
        start = time.time()
        buf = b""
        log.write("=== connect\n")

        def tx(data):
            conn.sendall(data)
            log.write("%8.3f TX %s\n" % (time.time() - start, data.hex(" ")))

        def store():
            open("kpg32d_written.bin", "wb").write(mem[:0x53FF])

        while True:
            data = conn.recv(4096)
            if not data:
                break
            log.write("%8.3f RX %s\n" % (time.time() - start, data.hex(" ")))
            buf += data
            while buf:
                if buf.startswith(b"PROGRAM"):
                    buf = buf[7:]
                    tx(b"\x06")
                    continue
                if len(buf) < 7 and b"PROGRAM".startswith(bytes(buf)):
                    break
                b = buf[0]
                if b == 0x02:
                    buf = buf[1:]
                    tx(bytes(mem[0x500:0x508]))
                elif b == 0x03 and len(buf) == 1:
                    buf = buf[1:]
                    log.write("        COMMIT\n")
                    tx(b"\x06")
                elif b in (0x06, 0x15, 0x45):
                    buf = buf[1:]
                    tx(b"\x06")
                elif b == 0x53:
                    if len(buf) < 5:
                        break
                    address, n = bytes(buf[1:4]), buf[4]
                    buf = buf[5:]
                    offset = offset_of(address)
                    block = bytes(mem[offset:offset + n])
                    if args.fill_blank and block == block[:1] * n:
                        tx(b"Z" + address + bytes([n]) + block[:1])
                    else:
                        tx(b"X" + address + bytes([n]) + block
                           + bytes([sum(block) & 0xFF]))
                elif b == 0x5A:
                    if len(buf) < 6:
                        break
                    address, n, fill = bytes(buf[1:4]), buf[4], buf[5]
                    buf = buf[6:]
                    offset = offset_of(address)
                    mem[offset:offset + n] = bytes([fill]) * n
                    log.write("        FILL %04x len %d value %02x\n"
                              % (offset, n, fill))
                    store()
                    tx(b"\x06")
                elif b == 0x58:
                    if len(buf) < 5 or len(buf) < 6 + buf[4]:
                        break
                    address, n = bytes(buf[1:4]), buf[4]
                    block, checksum = buf[5:5 + n], buf[5 + n]
                    buf = buf[6 + n:]
                    offset = offset_of(address)
                    mem[offset:offset + n] = block
                    log.write("        WRITE %04x len %d sum %02x calc %02x\n"
                              % (offset, n, checksum, sum(block) & 0xFF))
                    store()
                    tx(b"\x06")
                else:
                    log.write("        ?? %02x\n" % b)
                    buf = buf[1:]


if __name__ == "__main__":
    main()
