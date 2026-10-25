"""Tests for the reusable NewChirp SCSI/RAP transport layer."""

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from newchirp_mass_storage import (  # noqa: E402
    CS750Profile,
    CS750_SCSI_READ,
    CS750_SCSI_WRITE,
    MassStorageError,
    parse_rap_packet,
    rap_packet,
)


class FakeRapTransport:
    def __init__(self, image):
        self.image = image
        self.request = None
        self.writes = 0
        self.reads = 0
        self.closed = False

    def transfer(self, cdb, size, write_data=None):
        if bytes(cdb) == CS750_SCSI_WRITE:
            self.request = write_data
            self.writes += 1
            return b""

        self.reads += 1
        command, payload = parse_rap_packet(self.request)
        if command == 0x0003:
            response = rap_packet(0x8003, b"\x01D4.0.03" + b"\x00" * 249)
            return response.ljust(size, b"\x00")
        if command == 0x0015:
            return rap_packet(0x8015, b"\x00\x00").ljust(size, b"\x00")
        if command == 0x0010:
            block = int.from_bytes(payload[0:2], "big")
            data = self.image[
                block * CS750Profile.BLOCK_SIZE:
                (block + 1) * CS750Profile.BLOCK_SIZE
            ].ljust(CS750Profile.BLOCK_SIZE, b"\x00")
            units = (
                len(self.image) + CS750Profile.PAGE_SIZE - 1
            ) // CS750Profile.PAGE_SIZE
            metadata = (
                b"\x00\x00\x00"
                + units.to_bytes(4, "big")
            )
            return rap_packet(0x8010, metadata + data).ljust(
                size, b"\x00"
            )
        raise AssertionError("Unexpected command 0x%04x" % command)

    def close(self):
        self.closed = True


class RapTransportTest(unittest.TestCase):
    def test_packet_round_trip_and_checksum(self):
        packet = rap_packet(0x8010, b"\x01\x02\x03")
        self.assertEqual(parse_rap_packet(packet), (0x8010, b"\x01\x02\x03"))

        corrupt = bytearray(packet)
        corrupt[5] ^= 0xFF
        with self.assertRaises(MassStorageError):
            parse_rap_packet(bytes(corrupt))

    def test_cs750_read_sequence_reassembles_multiple_blocks(self):
        image = bytes(
            (index * 17) & 0xFF
            for index in range(CS750Profile.IMAGE_SIZE)
        )
        transport = FakeRapTransport(image)
        progress = []

        result = CS750Profile(transport).read_codeplug(
            progress=lambda current, total: progress.append((current, total))
        )

        self.assertEqual(result, image)
        self.assertEqual(progress[0], (1, 137))
        self.assertEqual(progress[-1], (137, 137))
        self.assertEqual(transport.reads, 139)
        self.assertEqual(transport.writes, 139)

    def test_authentication_requirement_fails_closed(self):
        transport = FakeRapTransport(b"\x00" * CS750Profile.IMAGE_SIZE)

        def require_auth(cdb, size, write_data=None):
            if write_data is not None:
                transport.request = write_data
                transport.writes += 1
                return b""
            transport.reads += 1
            command, _payload = parse_rap_packet(transport.request)
            if command == 0x0003:
                response = rap_packet(0x8003, b"\x00" * 257)
            elif command == 0x0015:
                response = rap_packet(0x8015, b"\x00\x01")
            else:
                raise AssertionError("Read continued after auth requirement")
            return response.ljust(size, b"\x00")

        transport.transfer = require_auth
        with self.assertRaisesRegex(
            MassStorageError, "unsupported authentication"
        ):
            CS750Profile(transport).read_codeplug()


if __name__ == "__main__":
    unittest.main()
