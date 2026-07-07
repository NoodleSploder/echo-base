"""FT8 receiver (Costas sync + soft demod + LDPC decode + message
unpack), tested against a real, off-air 15-second recording with
independently-published ground-truth decodes -- not a synthetic
round-trip, since that alone can't catch a systematic sync/demod bug
that a self-consistent encode-then-decode test would never expose
(see `test_ft8_ldpc.py`/`test_ft8_message.py` for the synthetic,
bit-exact cross-checks against ft8_lib's compiled reference; this is
the complementary "does it work on a real signal" check).

See `tests/fixtures/ft8/README.md` for the fixture's provenance.
"""
from __future__ import annotations

import re
import wave
from pathlib import Path

import numpy as np

from app.services.decoders.ft8_decoder import decode_window

_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "ft8"


def _load_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        raw = wav_file.readframes(wav_file.getnframes())
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    return audio, sample_rate


def _parse_ground_truth(path: Path) -> set[tuple[str, str, str]]:
    messages = set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        # HHMMSS SNR dt freq ~ message [trailing annotation, e.g. a country
        # name, column-aligned and separated from the message by a run of
        # 2+ spaces rather than the single spaces between message fields].
        parts = line.split(None, 5)
        message_only = re.split(r" {2,}", parts[5].rstrip())[0]
        # call_to is usually one token, but "CQ 123"/"CQ ABCD" (a
        # directed-CQ modifier) is two -- same "CQ " prefix rule
        # unpack_standard_message itself follows.
        fields = message_only.split()
        if fields[0] == "CQ" and len(fields) > 3:
            call_to, call_de, extra = f"{fields[0]} {fields[1]}", fields[2], fields[3]
        else:
            call_to, call_de, extra = fields[0], fields[1], fields[2]
        messages.add((call_to, call_de, extra))
    return messages


def test_decodes_real_off_air_recording_matching_ground_truth():
    audio, sample_rate = _load_wav(_FIXTURE_DIR / "191111_110615.wav")
    ground_truth = _parse_ground_truth(_FIXTURE_DIR / "191111_110615.txt")

    decodes = decode_window(audio, sample_rate)
    assert len(decodes) >= 5  # tuned defaults currently recover 8 of 21 real signals

    for decode in decodes:
        key = (decode.message.call_to, decode.message.call_de, decode.message.extra)
        assert key in ground_truth, f"decoded {key} which isn't in the published ground truth"
