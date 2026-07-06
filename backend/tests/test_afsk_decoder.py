"""Round-trip test for the AFSK1200/AX.25 decoder: synthesizes a known
packet as an AFSK1200 audio waveform (the same signal a real TNC's
audio input would see) and checks the decoder recovers it exactly.

This is the primary correctness proof for afsk.py/ax25.py -- real
over-the-air APRS reception is inherently non-deterministic (depends on
RF conditions outside this environment's control), so a synthetic
encode-then-decode round trip is what actually pins down behavior.
"""
from __future__ import annotations

import numpy as np

from app.services.decoders.afsk import Afsk1200Decoder
from app.services.decoders.ax25 import compute_fcs, parse_ax25_frame

SAMPLE_RATE_HZ = 48_000
BAUD = 1200


def _encode_address(callsign: str, ssid: int, is_last: bool, has_been_repeated: bool = False) -> bytes:
    padded = callsign.upper().ljust(6)[:6]
    address = bytearray(ord(c) << 1 for c in padded)
    ssid_byte = 0x60 | ((ssid & 0x0F) << 1) | (0x80 if has_been_repeated else 0) | (0x01 if is_last else 0)
    address.append(ssid_byte)
    return bytes(address)


def _bit_stuff(bits: list[int]) -> list[int]:
    stuffed: list[int] = []
    ones_run = 0
    for bit in bits:
        stuffed.append(bit)
        if bit == 1:
            ones_run += 1
            if ones_run == 5:
                stuffed.append(0)
                ones_run = 0
        else:
            ones_run = 0
    return stuffed


def _bytes_to_bits_lsb_first(data: bytes) -> list[int]:
    bits = []
    for byte in data:
        bits.extend((byte >> i) & 1 for i in range(8))
    return bits


def _build_ax25_frame(dest: str, src: str, info: bytes) -> bytes:
    payload = bytearray()
    payload += _encode_address(dest, 0, is_last=False)
    payload += _encode_address(src, 0, is_last=True)
    payload.append(0x03)  # UI frame control
    payload.append(0xF0)  # no layer-3 protocol
    payload += info
    fcs = compute_fcs(bytes(payload))
    payload.append(fcs & 0xFF)
    payload.append((fcs >> 8) & 0xFF)
    return bytes(payload)


def _synthesize_afsk(frame_bits_stuffed: list[int]) -> np.ndarray:
    flag_bits = [0, 1, 1, 1, 1, 1, 1, 0]
    full_bits = flag_bits * 8 + frame_bits_stuffed + flag_bits * 8

    # NRZI encode: 0 = tone change, 1 = no change.
    tones = []
    current_mark = True
    for bit in full_bits:
        if bit == 0:
            current_mark = not current_mark
        tones.append(current_mark)

    samples_per_bit = SAMPLE_RATE_HZ / BAUD
    samples = []
    phase = 0.0
    for is_mark in tones:
        freq = 1200 if is_mark else 2200
        n = int(round(samples_per_bit))
        t = np.arange(n)
        segment = np.sin(2 * np.pi * freq * t / SAMPLE_RATE_HZ + phase)
        samples.append(segment)
        phase = (phase + 2 * np.pi * freq * n / SAMPLE_RATE_HZ) % (2 * np.pi)
    return np.concatenate(samples).astype(np.float32)


def test_afsk_round_trip_recovers_known_packet():
    frame = _build_ax25_frame("APRS", "N0CALL", b">Test packet 12345")
    stuffed_bits = _bit_stuff(_bytes_to_bits_lsb_first(frame))
    audio = _synthesize_afsk(stuffed_bits)

    decoder = Afsk1200Decoder(SAMPLE_RATE_HZ)
    raw_frames = decoder.feed(audio)

    parsed = [parse_ax25_frame(f) for f in raw_frames]
    parsed = [p for p in parsed if p is not None]

    assert len(parsed) >= 1, f"expected at least one valid frame, got {len(raw_frames)} raw candidates"
    packet = parsed[0]
    assert packet.destination.callsign == "APRS"
    assert packet.source.callsign == "N0CALL"
    assert packet.info == b">Test packet 12345"


def test_afsk_decoder_ignores_silence():
    decoder = Afsk1200Decoder(SAMPLE_RATE_HZ)
    silence = np.zeros(SAMPLE_RATE_HZ, dtype=np.float32)
    assert decoder.feed(silence) == []
