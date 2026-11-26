#!/usr/bin/env python3
"""Drive a QEMU guest through its monitor socket: keystrokes and screenshots.

    keys.py [--sock mon.sock] TEXT @KEY #wait=SECONDS #shot=FILE.ppm ...

TEXT is typed character by character; @KEY sends a QEMU key name (@ret,
@esc, @alt-f, @down, @f4, ...); #wait pauses; #shot saves a screendump
(convert with: sips -s format png FILE.ppm --out FILE.png).

DOS programs drop keys sent too fast after opening a menu. Send menu
openers (@alt-f) and arrow keys in separate invocations, and take a
screenshot before acting on what you assume is on screen.
"""
import socket
import sys
import time

KEYS = {" ": "spc", "\n": "ret", ":": "shift-semicolon", "\\": "backslash",
        ".": "dot", "-": "minus", "/": "slash", "*": "shift-8"}


def main(argv):
    path = "mon.sock"
    if argv[:1] == ["--sock"]:
        path, argv = argv[1], argv[2:]
    sock = socket.socket(socket.AF_UNIX)
    sock.connect(path)  # keep the path short: macOS limits it to 104 bytes
    time.sleep(0.2)
    sock.recv(65536)

    def send(command):
        sock.sendall((command + "\n").encode())
        time.sleep(0.12)

    for arg in argv:
        if arg.startswith("@"):
            send("sendkey " + arg[1:])
        elif arg.startswith("#shot="):
            send("screendump " + arg[6:])
            time.sleep(0.5)
        elif arg.startswith("#wait="):
            time.sleep(float(arg[6:]))
        else:
            for ch in arg:
                key = KEYS.get(ch)
                if key is None:
                    key = ("shift-" + ch.lower()) if ch.isupper() else ch
                send("sendkey " + key)


if __name__ == "__main__":
    main(sys.argv[1:])
