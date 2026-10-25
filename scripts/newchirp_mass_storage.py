"""Reusable raw SCSI transport and RAP framing for NewChirp radios.

The CS750 is the first radio profile to use this module. Radio drivers should
keep model-specific command and image knowledge outside the transport layer so
other CPS families using SCSI mass-storage passthrough can reuse it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


CS750_SCSI_READ = bytes.fromhex(
    "ff 28 00 00 00 00 00 00 47 50 00 00 00 00 00 00"
)
CS750_SCSI_WRITE = bytes.fromhex(
    "ff 2a 00 00 00 00 00 00 47 50 00 00 00 00 00 00"
)


class MassStorageError(RuntimeError):
    pass


def _helper_path():
    configured = os.environ.get("NEWCHIRP_SCSI_HELPER")
    if configured:
        path = Path(configured)
        if path.is_file():
            return path
    here = Path(__file__).resolve()
    candidates = (
        here.parent / "newchirp_scsi",
        here.parent.parent / "tools" / "newchirp_scsi_mac",
        here.parent.parent / "build" / "newchirp_scsi_mac",
    )
    return next((path for path in candidates if path.is_file()), None)


class _MacScsiPassthrough:
    """Persistent macOS IOKit SCSITask helper process."""

    def __init__(self, device):
        self.device = device
        self.helper = _helper_path()
        if self.helper is None:
            raise MassStorageError(
                "NewChirp's macOS SCSI helper is not installed"
            )
        disk = device.replace("/dev/rdisk", "/dev/disk")
        if disk != device:
            subprocess.run(
                ["diskutil", "unmountDisk", disk],
                check=False,
                capture_output=True,
                timeout=15,
            )
        self._process = subprocess.Popen(
            [str(self.helper), "--device", device, "--serve"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _read_exact(self, size):
        data = bytearray()
        while len(data) < size:
            chunk = self._process.stdout.read(size - len(data))
            if not chunk:
                details = self._process.stderr.read().decode(
                    "utf-8", errors="replace"
                ).strip()
                raise MassStorageError(
                    details or "The SCSI helper stopped unexpectedly"
                )
            data.extend(chunk)
        return bytes(data)

    def transfer(self, cdb, size, write_data=None):
        if len(cdb) != 16:
            raise ValueError("SCSI CDB must be exactly 16 bytes")
        if write_data is not None and len(write_data) != size:
            raise ValueError("SCSI write size does not match its data")
        direction = 1 if write_data is not None else 0
        header = bytes((direction,)) + int(size).to_bytes(4, "big") + bytes(cdb)
        self._process.stdin.write(header)
        if write_data is not None:
            self._process.stdin.write(bytes(write_data))
        self._process.stdin.flush()

        response = self._read_exact(5)
        response_size = int.from_bytes(response[1:5], "big")
        payload = self._read_exact(response_size) if response_size else b""
        if response[0] != 0:
            raise MassStorageError(
                payload.decode("utf-8", errors="replace")
                or "SCSI pass-through command failed"
            )
        if write_data is None and len(payload) != size:
            raise MassStorageError(
                "SCSI device returned %i bytes; expected %i"
                % (len(payload), size)
            )
        return payload

    def close(self):
        if getattr(self, "_process", None) is None:
            return
        try:
            self._process.stdin.close()
        except Exception:
            pass
        try:
            self._process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self._process.terminate()


class _WindowsScsiPassthrough:
    """Windows SCSI_PASS_THROUGH_DIRECT backend."""

    IOCTL_SCSI_PASS_THROUGH_DIRECT = 0x4D014
    INVALID_HANDLE_VALUE = -1

    def __init__(self, device):
        import ctypes

        self.ctypes = ctypes
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel32.CreateFileW.restype = ctypes.c_void_p
        self.handle = self.kernel32.CreateFileW(
            ctypes.c_wchar_p(device),
            0xC0000000,
            3,
            None,
            3,
            0,
            None,
        )
        if self.handle == ctypes.c_void_p(self.INVALID_HANDLE_VALUE).value:
            raise MassStorageError(
                "Could not open raw CS750 disk: Windows error %i"
                % ctypes.get_last_error()
            )

    def transfer(self, cdb, size, write_data=None):
        import ctypes

        class ScsiPassThroughDirect(ctypes.Structure):
            _pack_ = 4
            _fields_ = (
                ("length", ctypes.c_ushort),
                ("scsi_status", ctypes.c_ubyte),
                ("path_id", ctypes.c_ubyte),
                ("target_id", ctypes.c_ubyte),
                ("lun", ctypes.c_ubyte),
                ("cdb_length", ctypes.c_ubyte),
                ("sense_length", ctypes.c_ubyte),
                ("data_in", ctypes.c_ubyte),
                ("data_length", ctypes.c_ulong),
                ("timeout", ctypes.c_ulong),
                ("data_buffer", ctypes.c_void_p),
                ("sense_offset", ctypes.c_ulong),
                ("cdb", ctypes.c_ubyte * 16),
            )

        buffer = ctypes.create_string_buffer(size)
        if write_data is not None:
            ctypes.memmove(buffer, bytes(write_data), size)
        packet = ScsiPassThroughDirect()
        packet.length = ctypes.sizeof(ScsiPassThroughDirect)
        packet.cdb_length = 16
        packet.sense_length = 32
        packet.data_in = 0 if write_data is not None else 1
        packet.data_length = size
        packet.timeout = 5
        packet.data_buffer = ctypes.cast(buffer, ctypes.c_void_p)
        packet.sense_offset = 0x30
        packet.cdb[:] = cdb

        raw = ctypes.create_string_buffer(ctypes.sizeof(packet) + 32)
        ctypes.memmove(raw, ctypes.byref(packet), ctypes.sizeof(packet))
        returned = ctypes.c_ulong()
        ok = self.kernel32.DeviceIoControl(
            ctypes.c_void_p(self.handle),
            self.IOCTL_SCSI_PASS_THROUGH_DIRECT,
            raw,
            len(raw),
            raw,
            len(raw),
            ctypes.byref(returned),
            None,
        )
        if not ok:
            raise MassStorageError(
                "SCSI pass-through failed: Windows error %i"
                % ctypes.get_last_error()
            )
        result = ctypes.cast(raw, ctypes.POINTER(ScsiPassThroughDirect)).contents
        if result.scsi_status != 0:
            raise MassStorageError(
                "SCSI status 0x%02x" % result.scsi_status
            )
        return b"" if write_data is not None else buffer.raw[:size]

    def close(self):
        if getattr(self, "handle", None):
            self.kernel32.CloseHandle(self.ctypes.c_void_p(self.handle))
            self.handle = None


class _LinuxScsiPassthrough:
    """Linux generic SCSI SG_IO backend."""

    SG_IO = 0x2285
    SG_DXFER_TO_DEV = -2
    SG_DXFER_FROM_DEV = -3

    def __init__(self, device):
        import fcntl

        self.fcntl = fcntl
        self.fd = os.open(device, os.O_RDWR)

    def transfer(self, cdb, size, write_data=None):
        import ctypes

        class SgIoHdr(ctypes.Structure):
            _fields_ = (
                ("interface_id", ctypes.c_int),
                ("dxfer_direction", ctypes.c_int),
                ("cmd_len", ctypes.c_ubyte),
                ("mx_sb_len", ctypes.c_ubyte),
                ("iovec_count", ctypes.c_ushort),
                ("dxfer_len", ctypes.c_uint),
                ("dxferp", ctypes.c_void_p),
                ("cmdp", ctypes.c_void_p),
                ("sbp", ctypes.c_void_p),
                ("timeout", ctypes.c_uint),
                ("flags", ctypes.c_uint),
                ("pack_id", ctypes.c_int),
                ("usr_ptr", ctypes.c_void_p),
                ("status", ctypes.c_ubyte),
                ("masked_status", ctypes.c_ubyte),
                ("msg_status", ctypes.c_ubyte),
                ("sb_len_wr", ctypes.c_ubyte),
                ("host_status", ctypes.c_ushort),
                ("driver_status", ctypes.c_ushort),
                ("resid", ctypes.c_int),
                ("duration", ctypes.c_uint),
                ("info", ctypes.c_uint),
            )

        buffer = ctypes.create_string_buffer(size)
        if write_data is not None:
            ctypes.memmove(buffer, bytes(write_data), size)
        command = (ctypes.c_ubyte * 16).from_buffer_copy(bytes(cdb))
        sense = (ctypes.c_ubyte * 32)()
        header = SgIoHdr()
        header.interface_id = ord("S")
        header.dxfer_direction = (
            self.SG_DXFER_TO_DEV
            if write_data is not None
            else self.SG_DXFER_FROM_DEV
        )
        header.cmd_len = 16
        header.mx_sb_len = 32
        header.dxfer_len = size
        header.dxferp = ctypes.cast(buffer, ctypes.c_void_p)
        header.cmdp = ctypes.cast(command, ctypes.c_void_p)
        header.sbp = ctypes.cast(sense, ctypes.c_void_p)
        header.timeout = 5000
        self.fcntl.ioctl(self.fd, self.SG_IO, header, True)
        if (
            header.status != 0
            or header.host_status != 0
            or header.driver_status != 0
            or header.resid != 0
        ):
            raise MassStorageError(
                "SCSI status=%i host=%i driver=%i resid=%i"
                % (
                    header.status,
                    header.host_status,
                    header.driver_status,
                    header.resid,
                )
            )
        return b"" if write_data is not None else buffer.raw[:size]

    def close(self):
        if getattr(self, "fd", None) is not None:
            os.close(self.fd)
            self.fd = None


class ScsiPassthrough:
    """Reusable factory for platform-specific raw SCSI transport."""

    @classmethod
    def list_devices(cls):
        if sys.platform == "darwin":
            helper = _helper_path()
            if helper is None:
                raise MassStorageError(
                    "NewChirp's macOS SCSI helper is not installed"
                )
            result = subprocess.run(
                [str(helper), "--list"],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise MassStorageError(
                    result.stderr.strip()
                    or "Could not enumerate SCSI devices"
                )
            try:
                return json.loads(result.stdout or "[]")
            except json.JSONDecodeError as exc:
                raise MassStorageError(
                    "The SCSI helper returned invalid device data"
                ) from exc
        if sys.platform == "win32":
            script = (
                "Get-CimInstance Win32_DiskDrive | "
                "Where-Object {$_.Model -match 'STM|microSD Flash'} | "
                "Select-Object DeviceID,Model | ConvertTo-Json -Compress"
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", script],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return []
            try:
                rows = json.loads(result.stdout or "[]")
            except json.JSONDecodeError:
                return []
            if isinstance(rows, dict):
                rows = [rows]
            return [
                {
                    "port": row.get("DeviceID", ""),
                    "deviceName": row.get("Model", "STM microSD Flash"),
                }
                for row in rows
                if row.get("DeviceID")
            ]
        if sys.platform.startswith("linux"):
            devices = []
            for block in sorted(Path("/sys/block").glob("*")):
                try:
                    vendor = (block / "device/vendor").read_text().strip()
                    model = (block / "device/model").read_text().strip()
                except OSError:
                    continue
                if vendor == "STM" or "microSD Flash" in model:
                    devices.append({
                        "port": "/dev/%s" % block.name,
                        "deviceName": "%s %s" % (vendor, model),
                    })
            return devices
        raise MassStorageError(
            "Raw SCSI mass-storage discovery is not supported on this OS"
        )

    def __init__(self, device):
        if sys.platform == "darwin":
            self._backend = _MacScsiPassthrough(device)
        elif sys.platform == "win32":
            self._backend = _WindowsScsiPassthrough(device)
        elif sys.platform.startswith("linux"):
            self._backend = _LinuxScsiPassthrough(device)
        else:
            raise MassStorageError(
                "Raw SCSI mass-storage transport is not supported on this OS"
            )

    def transfer(self, cdb, size, write_data=None):
        return self._backend.transfer(cdb, size, write_data=write_data)

    def close(self):
        self._backend.close()


def rap_packet(command, payload=b""):
    if len(payload) > 0xFFFF:
        raise ValueError("RAP payload is too large")
    checksum = sum(payload) & 0xFFFF
    return (
        b"\xA1"
        + int(command).to_bytes(2, "big")
        + len(payload).to_bytes(2, "big")
        + bytes(payload)
        + checksum.to_bytes(2, "big")
        + b"\xA4"
    )


def parse_rap_packet(data, expected_size=None):
    if len(data) < 8 or data[0] != 0xA1:
        raise MassStorageError("Invalid RAP packet header")
    command = int.from_bytes(data[1:3], "big")
    payload_length = int.from_bytes(data[3:5], "big")
    packet_length = payload_length + 8
    if packet_length > len(data):
        raise MassStorageError(
            "RAP packet declares %i bytes but only %i were returned"
            % (packet_length, len(data))
        )
    if expected_size is not None and packet_length != expected_size:
        raise MassStorageError(
            "RAP packet length is %i bytes; expected %i"
            % (packet_length, expected_size)
        )
    packet = data[:packet_length]
    if packet[-1] != 0xA4:
        raise MassStorageError("Invalid RAP packet terminator")
    payload = packet[5:-3]
    expected_sum = int.from_bytes(packet[-3:-1], "big")
    if (sum(payload) & 0xFFFF) != expected_sum:
        raise MassStorageError("Invalid RAP packet checksum")
    return command, payload


class RapMassStorageRadio:
    """Generic command-response session over a raw SCSI transport."""

    def __init__(self, transport):
        self.transport = transport

    def send(self, command, payload=b""):
        request = rap_packet(command, payload)
        self.transport.transfer(
            CS750_SCSI_WRITE,
            len(request),
            write_data=request,
        )

    def receive(self, expected_command, expected_size):
        data = self.transport.transfer(CS750_SCSI_READ, expected_size)
        command, payload = parse_rap_packet(data, expected_size)
        if command != expected_command:
            raise MassStorageError(
                "Expected RAP response 0x%04x, received 0x%04x"
                % (expected_command, command)
            )
        return payload

    def close(self):
        self.transport.close()


class CS750Profile(RapMassStorageRadio):
    """Read-only CS750 RAP profile and codeplug transfer."""

    IMAGE_SIZE = 0x44010
    PAGE_SIZE = 0x100
    BLOCK_PAGES = 8
    BLOCK_SIZE = PAGE_SIZE * BLOCK_PAGES
    MAX_BLOCKS = 1024

    def _command(self, command, payload=b"", response_command=None,
                 response_size=None):
        # Mass-storage passthrough carries both request and response through
        # the vendor SCSI command. The radio maintains the RAP session state.
        if response_command is None:
            self.transport.transfer(
                CS750_SCSI_WRITE,
                len(rap_packet(command, payload)),
                write_data=rap_packet(command, payload),
            )
            return None
        self.transport.transfer(
            CS750_SCSI_WRITE,
            len(rap_packet(command, payload)),
            write_data=rap_packet(command, payload),
        )
        return self.receive(response_command, response_size)

    def read_codeplug(self, progress=None):
        # The CPS uses request size 0x109 for the 0x8003 response and
        # 0x80F for each 2048-byte codeplug block.
        self.transport.transfer(
            CS750_SCSI_WRITE,
            len(rap_packet(0x0003)),
            write_data=rap_packet(0x0003),
        )
        self.receive(0x8003, 0x109)

        self.transport.transfer(
            CS750_SCSI_WRITE,
            len(rap_packet(0x0015)),
            write_data=rap_packet(0x0015),
        )
        status = self.receive(0x8015, 0x0A)
        if len(status) != 2 or status[1] != 0:
            raise MassStorageError(
                "CS750 requires an unsupported authentication step"
            )

        image = bytearray()
        total_blocks = None
        block = 0
        while total_blocks is None or block < total_blocks:
            if block >= self.MAX_BLOCKS:
                raise MassStorageError("CS750 reported too many data blocks")
            request = bytes((block >> 8, block & 0xFF, 8, 0))
            self.transport.transfer(
                CS750_SCSI_WRITE,
                len(rap_packet(0x0010, request)),
                write_data=rap_packet(0x0010, request),
            )
            payload = self.receive(0x8010, 0x80F)
            if len(payload) != 0x807:
                raise MassStorageError(
                    "CS750 block response has an unexpected payload size"
                )
            if payload[1] != 0:
                raise MassStorageError(
                    "CS750 rejected block %i with status %i"
                    % (block, payload[1])
                )
            if total_blocks is None:
                image_units = int.from_bytes(payload[3:7], "big")
                total_blocks = (
                    image_units // self.BLOCK_PAGES
                    + (1 if image_units % self.BLOCK_PAGES else 0)
                )
                reported_size = image_units * self.PAGE_SIZE
                if self.IMAGE_SIZE != reported_size:
                    # The radio rounds the final page up to 256 bytes.
                    if not (
                        self.IMAGE_SIZE
                        < reported_size
                        < self.IMAGE_SIZE + self.PAGE_SIZE
                    ):
                        raise MassStorageError(
                            "CS750 reported unsupported image size %i"
                            % (image_units * self.PAGE_SIZE)
                        )
            image.extend(payload[7:])
            block += 1
            if progress:
                progress(block, total_blocks)

        if len(image) < self.IMAGE_SIZE:
            image.extend(b"\x00" * (self.IMAGE_SIZE - len(image)))
        return bytes(image[:self.IMAGE_SIZE])


def list_devices():
    return ScsiPassthrough.list_devices()
