#!/bin/bash
# Boot FreeDOS with a DOS CPS folder as drive C: and COM1 wired to a
# simulated radio on 127.0.0.1:47350, tracing every UART register access.
#
#   run_cps.sh <FreeDOS x86BOOT.img> <folder with the CPS> <trace.log>
#
# Then, from the same directory:
#   python3 keys.py @n '#wait=1' @ret '#wait=4' 'C:' @ret '#wait=1' 'KPG23D' @ret '#wait=8' '#shot=s.ppm'
# (the first keys answer the FreeDOS installer prompts).
#
# FreeDOS 1.4 floppy edition: fdos/144m/x86BOOT.img (verify its SHA-256).
# Start the simulator first; QEMU reconnects every second if it restarts,
# and the CPS's first command after a simulator restart can be lost, so
# answer "Retry" once.
#
# BIOS INT 14h caveat: on a real PC the BIOS raises DTR+RTS to send and
# DTR alone to receive. QEMU's SeaBIOS does not drive MCR, so a trace with
# no MCR writes does NOT mean the lines are off (docs/REA_PLAYBOOK.md 5a).
set -euo pipefail
boot=$1; cps=$2; trace=$3
rm -f mon.sock
exec qemu-system-i386 -m 32 \
  -drive "file=$boot,format=raw,if=floppy" \
  -drive "file=fat:rw:$cps,format=raw,if=ide,index=0" \
  -boot a -display none \
  -monitor unix:mon.sock,server,nowait \
  -chardev socket,id=s0,host=127.0.0.1,port=47350,reconnect-ms=1000 \
  -serial chardev:s0 \
  -d trace:serial_write,trace:serial_read,trace:serial_update_parameters \
  -D "$trace" -no-reboot
