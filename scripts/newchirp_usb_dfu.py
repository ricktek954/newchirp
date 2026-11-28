# Copyright 2026 NewChirp contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Minimal libusb DFU transport used by experimental STM32 radios.

The desktop bridge normally hands CHIRP a pyserial object.  TYT MD-UV380
radios instead expose ST's DfuSe interface (0483:df11), so this module drives
that interface through the system libusb and exposes a small transport used
by the NewChirp driver.
"""

import ctypes
import ctypes.util
import os
from pathlib import Path
import re
import sys
import time


VID = 0x0483
PID = 0xDF11
DFU_BLOCK = 1024

REQUEST_TO_HOST = 0xA1
REQUEST_TO_DEVICE = 0x21
REQUEST_DETACH = 0
REQUEST_DOWNLOAD = 1
REQUEST_UPLOAD = 2
REQUEST_GET_STATUS = 3
REQUEST_CLEAR_STATUS = 4
REQUEST_GET_STATE = 5
REQUEST_ABORT = 6

APP_IDLE = 0
APP_DETACH = 1
DFU_IDLE = 2
DFU_DNLOAD_SYNC = 3
DFU_DNBUSY = 4
DFU_DNLOAD_IDLE = 5
DFU_MANIFEST_SYNC = 6
DFU_MANIFEST = 7
DFU_MANIFEST_WAIT_RESET = 8
DFU_UPLOAD_IDLE = 9
DFU_ERROR = 10

LIBUSB_ERROR_PIPE = -9
TRANSFER_TIMEOUT_MS = 30000


class DfuError(Exception):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


class _DeviceDescriptor(ctypes.Structure):
    _fields_ = [
        ("bLength", ctypes.c_uint8),
        ("bDescriptorType", ctypes.c_uint8),
        ("bcdUSB", ctypes.c_uint16),
        ("bDeviceClass", ctypes.c_uint8),
        ("bDeviceSubClass", ctypes.c_uint8),
        ("bDeviceProtocol", ctypes.c_uint8),
        ("bMaxPacketSize0", ctypes.c_uint8),
        ("idVendor", ctypes.c_uint16),
        ("idProduct", ctypes.c_uint16),
        ("bcdDevice", ctypes.c_uint16),
        ("iManufacturer", ctypes.c_uint8),
        ("iProduct", ctypes.c_uint8),
        ("iSerialNumber", ctypes.c_uint8),
        ("bNumConfigurations", ctypes.c_uint8),
    ]


def _candidate_libraries():
    configured = os.environ.get("NEWCHIRP_LIBUSB")
    if configured:
        yield configured
    here = Path(__file__).resolve()
    bundle_roots = (
        here.parent,
        here.parent.parent,
        Path(getattr(sys, "_MEIPASS", here.parent)),
    )
    for root in bundle_roots:
        for name in (
                "libusb-1.0.0.dylib",
                "libusb-1.0.dylib",
                "libusb-1.0.so.0",
                "libusb-1.0.dll"):
            for folder in (root, root / "lib", root / "Frameworks"):
                path = folder / name
                if path.is_file():
                    yield str(path)
    found = ctypes.util.find_library("usb-1.0")
    if found:
        yield found
    if sys.platform == "darwin":
        yield "/opt/homebrew/lib/libusb-1.0.dylib"
        yield "/usr/local/lib/libusb-1.0.dylib"


def _load_library():
    failures = []
    for candidate in _candidate_libraries():
        try:
            return ctypes.CDLL(candidate)
        except OSError as exc:
            failures.append(str(exc))
    raise DfuError(
        "The libusb 1.0 runtime was not found; install libusb or set "
        "NEWCHIRP_LIBUSB. %s" % ("; ".join(failures[-2:]) or "")
    )


def _bind_library(lib):
    lib.libusb_init.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
    lib.libusb_init.restype = ctypes.c_int
    lib.libusb_exit.argtypes = [ctypes.c_void_p]
    lib.libusb_get_device_list.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)),
    ]
    lib.libusb_get_device_list.restype = ctypes.c_ssize_t
    lib.libusb_free_device_list.argtypes = [
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_int,
    ]
    lib.libusb_get_device_descriptor.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(_DeviceDescriptor),
    ]
    lib.libusb_get_device_descriptor.restype = ctypes.c_int
    lib.libusb_get_bus_number.argtypes = [ctypes.c_void_p]
    lib.libusb_get_bus_number.restype = ctypes.c_uint8
    lib.libusb_get_device_address.argtypes = [ctypes.c_void_p]
    lib.libusb_get_device_address.restype = ctypes.c_uint8
    lib.libusb_open.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    ]
    lib.libusb_open.restype = ctypes.c_int
    lib.libusb_ref_device.argtypes = [ctypes.c_void_p]
    lib.libusb_ref_device.restype = ctypes.c_void_p
    lib.libusb_unref_device.argtypes = [ctypes.c_void_p]
    lib.libusb_close.argtypes = [ctypes.c_void_p]
    lib.libusb_claim_interface.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.libusb_claim_interface.restype = ctypes.c_int
    lib.libusb_release_interface.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.libusb_kernel_driver_active.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.libusb_kernel_driver_active.restype = ctypes.c_int
    lib.libusb_detach_kernel_driver.argtypes = [ctypes.c_void_p, ctypes.c_int]
    lib.libusb_detach_kernel_driver.restype = ctypes.c_int
    lib.libusb_control_transfer.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint8,
        ctypes.c_uint8,
        ctypes.c_uint16,
        ctypes.c_uint16,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_uint16,
        ctypes.c_uint,
    ]
    lib.libusb_control_transfer.restype = ctypes.c_int
    if hasattr(lib, "libusb_strerror"):
        lib.libusb_strerror.argtypes = [ctypes.c_int]
        lib.libusb_strerror.restype = ctypes.c_char_p


def _error_text(lib, code):
    if hasattr(lib, "libusb_strerror"):
        value = lib.libusb_strerror(code)
        if value:
            return value.decode("utf-8", errors="replace")
    return "libusb error %i" % code


def _devices(lib, context):
    devices = ctypes.POINTER(ctypes.c_void_p)()
    count = lib.libusb_get_device_list(context, ctypes.byref(devices))
    if count < 0:
        raise DfuError(_error_text(lib, count))
    try:
        for index in range(count):
            device = devices[index]
            descriptor = _DeviceDescriptor()
            result = lib.libusb_get_device_descriptor(
                device, ctypes.byref(descriptor)
            )
            if result < 0:
                continue
            yield (
                device,
                descriptor,
                lib.libusb_get_bus_number(device),
                lib.libusb_get_device_address(device),
            )
    finally:
        lib.libusb_free_device_list(devices, 1)


def list_devices():
    """Return DfuSe radio interfaces as bridge pseudo-port records."""
    try:
        lib = _load_library()
        _bind_library(lib)
        context = ctypes.c_void_p()
        result = lib.libusb_init(ctypes.byref(context))
        if result < 0:
            return []
        try:
            found = []
            for _device, descriptor, bus, address in _devices(lib, context):
                if descriptor.idVendor != VID or descriptor.idProduct != PID:
                    continue
                found.append({
                    "port": "usb-dfu:%i:%i" % (bus, address),
                    "deviceName": (
                        "TYT/STM32 USB DFU programming interface "
                        "(0483:df11)"
                    ),
                })
            return found
        finally:
            lib.libusb_exit(context)
    except (DfuError, OSError, AttributeError):
        return []


class DfuTransport:
    """ST DfuSe control-transfer transport for the MD-UV380 family."""

    def __init__(self, port):
        self.lib = _load_library()
        _bind_library(self.lib)
        self.context = ctypes.c_void_p()
        self.handle = ctypes.c_void_p()
        self._claimed = False
        result = self.lib.libusb_init(ctypes.byref(self.context))
        if result < 0:
            raise DfuError(_error_text(self.lib, result))

        match = re.fullmatch(r"usb-dfu:(\d+):(\d+)", str(port))
        wanted = (
            (int(match.group(1)), int(match.group(2)))
            if match else None
        )
        selected = None
        for device, descriptor, bus, address in _devices(
                self.lib, self.context):
            if descriptor.idVendor != VID or descriptor.idProduct != PID:
                continue
            if wanted and wanted != (bus, address):
                continue
            selected = self.lib.libusb_ref_device(device)
            break
        if selected is None:
            self.libusb_exit()
            raise DfuError(
                "The TYT USB DFU interface (0483:df11) was not found"
            )

        result = self.lib.libusb_open(
            selected, ctypes.byref(self.handle)
        )
        self.lib.libusb_unref_device(selected)
        if result < 0:
            self.libusb_exit()
            raise DfuError(
                "Cannot open the TYT USB DFU interface: %s"
                % _error_text(self.lib, result)
            )

        if self.lib.libusb_kernel_driver_active(self.handle, 0):
            self.lib.libusb_detach_kernel_driver(self.handle, 0)
        result = self.lib.libusb_claim_interface(self.handle, 0)
        if result < 0:
            self.close(reboot=False)
            raise DfuError(
                "Cannot claim the TYT USB DFU interface: %s"
                % _error_text(self.lib, result)
            )
        self._claimed = True

    def libusb_exit(self):
        if getattr(self, "context", None):
            self.lib.libusb_exit(self.context)
            self.context = ctypes.c_void_p()

    def _transfer(self, request_type, request, value, data_or_length,
                  timeout=TRANSFER_TIMEOUT_MS, allow_short=False):
        if isinstance(data_or_length, int):
            length = data_or_length
            buffer = (ctypes.c_ubyte * length)()
        else:
            payload = bytes(data_or_length)
            length = len(payload)
            buffer = (ctypes.c_ubyte * max(length, 1))()
            if payload:
                ctypes.memmove(buffer, payload, length)
        result = self.lib.libusb_control_transfer(
            self.handle,
            request_type,
            request,
            value,
            0,
            buffer,
            length,
            timeout,
        )
        if result < 0:
            raise DfuError(_error_text(self.lib, result), result)
        if result != length and not (allow_short and result > 0):
            raise DfuError(
                "USB DFU transfer returned %i of %i bytes" % (result, length)
            )
        return bytes(buffer[:result]) if isinstance(
            data_or_length, int
        ) else b""

    def _status(self):
        value = self._transfer(
            REQUEST_TO_HOST, REQUEST_GET_STATUS, 0, 6
        )
        return {
            "status": value[0],
            "poll_ms": int.from_bytes(value[1:4], "little"),
            "state": value[4],
        }

    def _wait_idle(self, timeout=10):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            state = self._transfer(
                REQUEST_TO_HOST, REQUEST_GET_STATE, 0, 1
            )[0]
            if state == DFU_IDLE:
                return
            if state == APP_IDLE:
                self._transfer(
                    REQUEST_TO_DEVICE, REQUEST_DETACH, 1000, b""
                )
            elif state == DFU_ERROR:
                self._transfer(
                    REQUEST_TO_DEVICE, REQUEST_CLEAR_STATUS, 0, b""
                )
            elif state in (
                    APP_DETACH,
                    DFU_DNBUSY,
                    DFU_MANIFEST_WAIT_RESET):
                time.sleep(0.1)
            else:
                self._transfer(
                    REQUEST_TO_DEVICE, REQUEST_ABORT, 0, b""
                )
        raise DfuError("The radio did not return to DFU idle state")

    def _download(self, block, data):
        self._transfer(
            REQUEST_TO_DEVICE, REQUEST_DOWNLOAD, block, bytes(data)
        )
        self._status()

    def _upload(self, block, length, allow_short=False):
        data = self._transfer(
            REQUEST_TO_HOST, REQUEST_UPLOAD, block, length,
            allow_short=allow_short,
        )
        self._status()
        return data

    def command(self, command):
        self._download(0, command)
        time.sleep(0.1)
        self._wait_idle()

    def program_mode(self):
        try:
            self._wait_idle()
            self.command(b"\x91\x01")
            identity = self.identity()
            self.set_address(0)
        except DfuError as exc:
            raise DfuError(
                "USB DFU programming mode failed: %s" % exc, exc.code
            ) from exc
        return identity

    def identity(self):
        # The radio may answer with fewer than 64 bytes: a 2026-11-25 macOS
        # report (INBOX:986) got 32. dmrconfig's identify() also requests 64
        # and accepts any length; the model name sits in the first 32 bytes.
        self.command(b"\xA2\x01")
        return self._upload(0, 64, allow_short=True)

    def set_address(self, address):
        self.command(
            b"\x21"
            + int(address).to_bytes(4, "little")
        )

    def erase(self, start, size):
        first = int(start) & ~0xFFFF
        end = (int(start) + int(size) + 0xFFFF) & ~0xFFFF
        try:
            self._status()
            self._wait_idle()
            self.command(b"\x91\x01")
            time.sleep(0.1)
        except DfuError as exc:
            raise DfuError(
                "USB DFU programming mode before erase failed: %s" % exc,
                exc.code,
            ) from exc
        for address in range(first, end, 0x10000):
            self._erase_page(address)
        try:
            self.set_address(0)
        except DfuError as exc:
            raise DfuError(
                "USB DFU address reset after erase failed: %s" % exc,
                exc.code,
            ) from exc

    def _erase_page(self, address):
        command = b"\x41" + int(address).to_bytes(4, "little")
        try:
            self._transfer(REQUEST_TO_DEVICE, REQUEST_DOWNLOAD, 0, command)
        except DfuError as exc:
            raise DfuError(
                "USB DFU erase at 0x%06X failed: %s" % (address, exc),
                exc.code,
            ) from exc
        try:
            self._status()
            self._wait_idle()
        except DfuError as exc:
            if exc.code != LIBUSB_ERROR_PIPE:
                raise DfuError(
                    "USB DFU erase at 0x%06X failed: %s" % (address, exc),
                    exc.code,
                ) from exc
            time.sleep(1.0)
            try:
                self._wait_idle()
            except DfuError as again:
                raise DfuError(
                    "USB DFU erase at 0x%06X did not finish: %s"
                    % (address, again),
                    again.code,
                ) from again

    def read(self, address, length):
        data = bytearray()
        for offset in range(0, length, DFU_BLOCK):
            chunk_size = min(DFU_BLOCK, length - offset)
            block = (address + offset) // DFU_BLOCK
            chunk = self._upload(block + 2, chunk_size)
            data.extend(chunk)
        return bytes(data)

    def write(self, address, data):
        data = bytes(data)
        for offset in range(0, len(data), DFU_BLOCK):
            chunk = data[offset:offset + DFU_BLOCK]
            if len(chunk) != DFU_BLOCK:
                raise DfuError("DFU writes must be 1024-byte aligned")
            block = (address + offset) // DFU_BLOCK
            try:
                self._download(block + 2, chunk)
                self._wait_idle()
            except DfuError as exc:
                raise DfuError(
                    "USB DFU write at 0x%06X failed: %s"
                    % (address + offset, exc),
                    exc.code,
                ) from exc

    def reboot(self):
        if self.handle:
            try:
                self._download(0, b"\x91\x05")
            except DfuError:
                pass

    def close(self, reboot=True):
        if reboot:
            self.reboot()
        if getattr(self, "_claimed", False) and self.handle:
            self.lib.libusb_release_interface(self.handle, 0)
            self._claimed = False
        if getattr(self, "handle", None):
            self.lib.libusb_close(self.handle)
            self.handle = ctypes.c_void_p()
        self.libusb_exit()
