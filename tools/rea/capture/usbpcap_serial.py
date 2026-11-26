#!/usr/bin/env python3
"""Print the serial bytes in a USBPcap .pcapng (Wireshark on Windows).

    usbpcap_serial.py capture.pcapng [--ftdi]

Lists bulk OUT (host to radio) and IN (radio to host) payloads in order.
--ftdi strips the 2-byte modem-status prefix FTDI adapters put on every
64-byte IN packet. Used for the 5RH Pro captures from CHIRP issue 11669.
"""
import struct
import sys


def packets(path):
    data = open(path, "rb").read()
    pos = 0
    while pos + 12 <= len(data):
        block_type, block_len = struct.unpack_from("<II", data, pos)
        if block_len < 12:
            break
        if block_type == 6:  # Enhanced Packet Block
            captured = struct.unpack_from("<I", data, pos + 20)[0]
            yield data[pos + 28:pos + 28 + captured]
        pos += block_len


def main():
    ftdi = "--ftdi" in sys.argv
    for path in [a for a in sys.argv[1:] if not a.startswith("--")]:
        print("==", path)
        for pkt in packets(path):
            if len(pkt) < 27:
                continue
            header_len = struct.unpack_from("<H", pkt, 0)[0]
            info, transfer = pkt[16], pkt[22]
            payload = pkt[header_len:]
            if transfer != 3 or not payload:  # bulk only
                continue
            if info & 1:
                if ftdi:
                    payload = b"".join(payload[i + 2:i + 64]
                                       for i in range(0, len(payload), 64))
                if payload:
                    print("IN  %4d %s" % (len(payload), payload[:32].hex(" ")))
            else:
                print("OUT %4d %s" % (len(payload), payload[:32].hex(" ")))


if __name__ == "__main__":
    main()
