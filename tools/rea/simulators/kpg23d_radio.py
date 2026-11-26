#!/usr/bin/env python3
"""Simulated TK-250/TK-350 for tracing KPG-23D reads and writes in QEMU.

    kpg23d_radio.py IMAGE.U1F [--ident HEX] [--nak-first-write]

Serves IMAGE (0x0E00 bytes = radio 0xF000-0xFDFF) on 127.0.0.1:47350 and
logs every byte to kpg23d_radio.log; writes land in kpg23d_written.bin.

Protocol as traced 2026-11-26 (docs/KPG23_PROTOCOL.md):
  02 -> 6-byte identity (default: the image's model record at 0x0D00)
  06 -> 06
  R hi lo n -> W hi lo n + n bytes
  W hi lo n + n bytes -> 06 (the CPS aborts on anything else)
"""
import argparse
import socket
import time

FIRST = 0xF000


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("--ident", help="identity bytes as hex")
    parser.add_argument("--nak-first-write", action="store_true")
    args = parser.parse_args()
    mem = bytearray(open(args.image, "rb").read())
    writes = [0]
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 47350))
    srv.listen(1)
    log = open("kpg23d_radio.log", "a", buffering=1)
    while True:
        conn, _ = srv.accept()
        start = time.time()
        buf = b""
        log.write("=== connect\n")

        def tx(data):
            conn.sendall(data)
            log.write("%8.3f TX %s\n" % (time.time() - start, data.hex(" ")))

        while True:
            data = conn.recv(4096)
            if not data:
                break
            log.write("%8.3f RX %s\n" % (time.time() - start, data.hex(" ")))
            buf += data
            while buf:
                b = buf[0]
                if b == 0x02:
                    buf = buf[1:]
                    tx(bytes.fromhex(args.ident) if args.ident
                       else bytes(mem[0xD00:0xD06]))
                elif b == 0x06:
                    buf = buf[1:]
                    tx(b"\x06")
                elif b == 0x52:
                    if len(buf) < 4:
                        break
                    address = (buf[1] << 8) | buf[2]
                    n = buf[3]
                    buf = buf[4:]
                    offset = address - FIRST
                    tx(bytes([0x57, address >> 8, address & 0xFF, n])
                       + bytes(mem[offset:offset + n]).ljust(n, b"\xff"))
                elif b == 0x57:
                    if len(buf) < 4 or len(buf) < 4 + buf[3]:
                        break
                    address = (buf[1] << 8) | buf[2]
                    n = buf[3]
                    offset = address - FIRST
                    mem[offset:offset + n] = buf[4:4 + n]
                    buf = buf[4 + n:]
                    writes[0] += 1
                    log.write("        WRITE %04x len %d\n" % (address, n))
                    open("kpg23d_written.bin", "wb").write(mem)
                    nak = args.nak_first_write and writes[0] == 1
                    tx(b"\x15" if nak else b"\x06")
                else:
                    log.write("        ?? %02x\n" % b)
                    buf = buf[1:]


if __name__ == "__main__":
    main()
