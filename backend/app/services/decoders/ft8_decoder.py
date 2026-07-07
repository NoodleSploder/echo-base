"""FT8 receiver: Costas-sync search + 8-FSK soft-symbol extraction +
LDPC decode + standard-message unpack, over one ~15-second window of
real-valued (already downconverted/demodulated to baseband) audio.

Architecturally different from every other decoder in this project:
FT8 is a *batch*, not a *streaming*, protocol -- transmissions are
exactly 79 symbols (12.64s) long, sent in a fixed 15-second slot
aligned to UTC, and correctly decoding one requires seeing the whole
slot at once (the Costas sync search and LDPC decode both need the
complete signal, not an incremental stream). So this module exposes
`decode_window(audio, sample_rate_hz) -> list[Ft8Decode]`, called by
`stream_service.py` once per ~15s of accumulated audio, rather than a
stateful `.feed()` per small chunk the way every audio decoder in this
project works.

Algorithm ported from ft8_lib's `decode.c` (Costas sync scoring,
per-symbol soft-bit extraction via per-bit max-log-likelihood, and the
LLR variance normalization before LDPC decoding) -- verified end-to-end
against a real, off-air 15-second FT8 recording with independently
published ground-truth decodes (see `test_ft8_decoder.py`), not just a
synthetic round-trip.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.services.decoders.ft8_constants import (
    COSTAS_PATTERN,
    GRAY_MAP,
    LDPC_K,
    NUM_SYNC,
    SYMBOL_PERIOD_S,
    SYNC_OFFSETS,
)
from app.services.decoders.ft8_crc import verify_crc
from app.services.decoders.ft8_ldpc import bp_decode
from app.services.decoders.ft8_message import Ft8StandardMessage, unpack_standard_message

TIME_OVERSAMPLE = 4
FREQ_OVERSAMPLE = 2
MIN_FREQ_HZ = 100.0
MAX_FREQ_HZ = 3000.0
_LLR_TARGET_VARIANCE = 24.0


@dataclass(frozen=True)
class Ft8Decode:
    frequency_hz: float
    message: Ft8StandardMessage


def _build_waterfall(
    audio: np.ndarray, sample_rate_hz: int
) -> tuple[np.ndarray, int, int, int]:
    """Returns (log-magnitude waterfall [blocks, freq_bins], hop_samples,
    fft_len, symbol_samples). Frequency bin spacing is
    `sample_rate_hz / fft_len`; consecutive tone bins for one FSK
    symbol are `FREQ_OVERSAMPLE` bins apart."""
    symbol_samples = round(SYMBOL_PERIOD_S * sample_rate_hz)
    fft_len = symbol_samples * FREQ_OVERSAMPLE
    hop = symbol_samples // TIME_OVERSAMPLE
    window = np.hanning(symbol_samples).astype(np.float32)

    n_blocks = max(0, (len(audio) - symbol_samples) // hop + 1)
    waterfall = np.zeros((n_blocks, fft_len // 2 + 1), dtype=np.float32)
    for i in range(n_blocks):
        start = i * hop
        segment = audio[start : start + symbol_samples] * window
        spectrum = np.fft.rfft(segment, n=fft_len)
        waterfall[i] = np.log(np.abs(spectrum) + 1e-12)
    return waterfall, hop, fft_len, symbol_samples


def _sync_score(waterfall: np.ndarray, block_offset: int, bin_offset: int) -> float:
    """Contrastive Costas sync score: how much stronger the expected
    sync tone is than its immediate frequency/time neighbors, averaged
    over all 21 sync symbols (3 blocks x 7 symbols) -- the same
    approach as ft8_lib's `ft8_sync_score`, which specifically found
    this contrastive form works better than raw sync-tone energy."""
    n_blocks, n_bins = waterfall.shape
    total = 0.0
    count = 0
    for m in range(NUM_SYNC):
        for k in range(len(COSTAS_PATTERN)):
            symbol_index = SYNC_OFFSETS[m] + k
            block = block_offset + symbol_index * TIME_OVERSAMPLE
            if block < 0 or block >= n_blocks:
                continue
            tone = COSTAS_PATTERN[k]
            bin_idx = bin_offset + tone * FREQ_OVERSAMPLE
            value = waterfall[block, bin_idx]
            if tone > 0:
                total += value - waterfall[block, bin_idx - FREQ_OVERSAMPLE]
                count += 1
            if tone < 7:
                total += value - waterfall[block, bin_idx + FREQ_OVERSAMPLE]
                count += 1
            if k > 0 and block - TIME_OVERSAMPLE >= 0:
                total += value - waterfall[block - TIME_OVERSAMPLE, bin_idx]
                count += 1
            if k < len(COSTAS_PATTERN) - 1 and block + TIME_OVERSAMPLE < n_blocks:
                total += value - waterfall[block + TIME_OVERSAMPLE, bin_idx]
                count += 1
    return total / count if count else -1e9


def _find_candidates(
    waterfall: np.ndarray, bin_hz: float, max_candidates: int, min_score: float
) -> list[tuple[int, int, float]]:
    """Returns (block_offset, bin_offset, score) triples, best first."""
    n_blocks, n_bins = waterfall.shape
    candidates: list[tuple[int, int, float]] = []
    max_time_offset_symbols = 4  # generous slack for imperfect slot alignment
    min_bin = max(0, round(MIN_FREQ_HZ / bin_hz))
    max_bin = min(n_bins - 7 * FREQ_OVERSAMPLE, round(MAX_FREQ_HZ / bin_hz))
    for block_offset in range(
        -max_time_offset_symbols * TIME_OVERSAMPLE,
        n_blocks + max_time_offset_symbols * TIME_OVERSAMPLE,
    ):
        for bin_offset in range(min_bin, max_bin):
            score = _sync_score(waterfall, block_offset, bin_offset)
            if score >= min_score:
                candidates.append((block_offset, bin_offset, score))
    candidates.sort(key=lambda c: c[2], reverse=True)
    return candidates[:max_candidates]


def _extract_symbol_llr(tone_log_mag: np.ndarray) -> tuple[float, float, float]:
    """`tone_log_mag` is the 8 tones' log-magnitude for one symbol.
    Returns the 3 bits' LLRs via max-log-likelihood over the 4 tones
    consistent with each bit being 1 vs. being 0 (ft8_lib's
    `ft8_extract_symbol`) -- cheaper and, per that reference, about as
    accurate as a full log-sum-exp combination."""
    s = [tone_log_mag[GRAY_MAP[j]] for j in range(8)]
    bit0 = max(s[4], s[5], s[6], s[7]) - max(s[0], s[1], s[2], s[3])
    bit1 = max(s[2], s[3], s[6], s[7]) - max(s[0], s[1], s[4], s[5])
    bit2 = max(s[1], s[3], s[5], s[7]) - max(s[0], s[2], s[4], s[6])
    return bit0, bit1, bit2


def _extract_llr(waterfall: np.ndarray, block_offset: int, bin_offset: int) -> list[float]:
    from app.services.decoders.ft8_constants import ND, NN

    n_blocks = waterfall.shape[0]
    llr = [0.0] * (3 * ND)
    data_symbol = 0
    for i_tone in range(NN):
        is_sync = any(offset <= i_tone < offset + 7 for offset in SYNC_OFFSETS)
        if is_sync:
            continue
        block = block_offset + i_tone * TIME_OVERSAMPLE
        bit_idx = 3 * data_symbol
        if 0 <= block < n_blocks:
            tones = waterfall[block, bin_offset :: FREQ_OVERSAMPLE][:8]
            b0, b1, b2 = _extract_symbol_llr(tones)
            llr[bit_idx], llr[bit_idx + 1], llr[bit_idx + 2] = b0, b1, b2
        data_symbol += 1
    return llr


def _normalize_llr(llr: list[float]) -> list[float]:
    arr = np.array(llr, dtype=np.float64)
    variance = arr.var()
    if variance <= 1e-12:
        return llr
    factor = np.sqrt(_LLR_TARGET_VARIANCE / variance)
    return (arr * factor).tolist()


def decode_window(
    audio: np.ndarray, sample_rate_hz: int, max_candidates: int = 200, min_sync_score: float = 0.5
) -> list[Ft8Decode]:
    """Decodes every standard-message FT8 transmission found in one
    ~15-second window of real-valued audio. Defaults tuned against a
    real off-air recording (see `test_ft8_decoder.py`): 13 of 21
    independently-published ground-truth decodes recovered, all
    correct -- WSJT-X's own decoder does meaningfully better (multiple
    decode passes, subtracting already-decoded signals to reveal ones
    they were masking, a priori decoding using known callsigns), which
    is out of scope here."""
    waterfall, hop, fft_len, symbol_samples = _build_waterfall(audio, sample_rate_hz)
    if waterfall.shape[0] == 0:
        return []

    bin_hz = sample_rate_hz / fft_len
    candidates = _find_candidates(waterfall, bin_hz, max_candidates, min_sync_score)

    decodes: list[Ft8Decode] = []
    seen_messages: set[tuple[str, str, str]] = set()
    for block_offset, bin_offset, _score in candidates:
        llr = _extract_llr(waterfall, block_offset, bin_offset)
        llr = _normalize_llr(llr)
        bits, errors = bp_decode(llr, max_iters=30)
        if errors != 0:
            continue

        payload_with_crc = bits[:LDPC_K]
        if not verify_crc(payload_with_crc):
            continue

        message = unpack_standard_message(payload_with_crc[:77])
        if message is None:
            continue

        # The same real transmission is routinely found by more than
        # one nearby (block_offset, bin_offset) candidate -- dedupe on
        # decoded content (a real distinct signal essentially never
        # produces the same three fields by chance) rather than
        # frequency proximity, which would incorrectly merge two
        # genuinely different simultaneous transmissions that happen
        # to land close in frequency.
        key = (message.call_to, message.call_de, message.extra)
        if key in seen_messages:
            continue
        seen_messages.add(key)

        frequency_hz = bin_offset * bin_hz
        decodes.append(Ft8Decode(frequency_hz=frequency_hz, message=message))

    return decodes
