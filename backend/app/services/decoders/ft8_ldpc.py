"""FT8's (174,91) LDPC belief-propagation decoder.

Ported from ft8_lib's `ldpc.c` `bp_decode` (sum-product/tanh-rule
belief propagation using the verified `LDPC_NM`/`LDPC_MN` tables in
`ft8_constants.py`), using real `math.tanh`/`math.atanh` rather than
the source's polynomial fast-approximations (no reason to trade
accuracy for speed here; this only needs to run once per received
15-second window, not per-sample).

**LLR sign convention, verified empirically against the compiled C
reference rather than trusted from its own source comment**: `ldpc.c`
documents its LLR input as `log(P(x=0)/P(x=1))` (positive = bit likely
0), but a compiled round-trip test (encode a known payload, build LLRs
from it, decode, compare) showed the *opposite* is actually true in
this codebase: **positive LLR means the bit is more likely 1**. Using
the documented convention decoded with 156/174 bits wrong even at full
input confidence; the empirically-verified opposite convention decoded
perfectly (0 errors). This module follows the verified convention, not
the comment.
"""
from __future__ import annotations

import math

from app.services.decoders.ft8_constants import LDPC_M, LDPC_MN, LDPC_N, LDPC_NM, LDPC_NUM_ROWS


def _ldpc_errors(bits: list[int]) -> int:
    """Number of the 83 parity checks `bits` (174 hard bit decisions)
    fails -- 0 means a valid codeword."""
    errors = 0
    for row, count in zip(LDPC_NM, LDPC_NUM_ROWS, strict=True):
        parity = 0
        for k in range(count):
            parity ^= bits[row[k] - 1]
        if parity != 0:
            errors += 1
    return errors


def bp_decode(llr: list[float], max_iters: int = 30) -> tuple[list[int], int]:
    """`llr` is 174 log-likelihoods (positive = bit likely 1, see the
    module docstring). Returns (174 hard bits, parity errors remaining
    -- 0 means a fully valid codeword, i.e. real success)."""
    assert len(llr) == LDPC_N
    tov = [[0.0, 0.0, 0.0] for _ in range(LDPC_N)]
    best_bits = [0] * LDPC_N
    min_errors = LDPC_M

    for _iteration in range(max_iters):
        bits = [1 if (llr[n] + sum(tov[n])) > 0 else 0 for n in range(LDPC_N)]
        if sum(bits) == 0:
            break  # converged to all-zeros, which FT8's codewords never legitimately are

        errors = _ldpc_errors(bits)
        if errors < min_errors:
            min_errors = errors
            best_bits = bits
            if errors == 0:
                break

        # Variable-to-check messages (toc[m][n_idx], only for (m,n) edges in LDPC_NM).
        toc: list[list[float]] = [[0.0] * LDPC_NUM_ROWS[m] for m in range(LDPC_M)]
        for m in range(LDPC_M):
            row = LDPC_NM[m]
            count = LDPC_NUM_ROWS[m]
            for n_idx in range(count):
                n = row[n_idx] - 1
                total = llr[n]
                for m_idx in range(3):
                    if (LDPC_MN[n][m_idx] - 1) != m:
                        total += tov[n][m_idx]
                toc[m][n_idx] = math.tanh(-total / 2)

        # Check-to-variable messages.
        for n in range(LDPC_N):
            for m_idx in range(3):
                m = LDPC_MN[n][m_idx] - 1
                row = LDPC_NM[m]
                count = LDPC_NUM_ROWS[m]
                product = 1.0
                for n_idx in range(count):
                    if (row[n_idx] - 1) != n:
                        product *= toc[m][n_idx]
                product = max(min(product, 1 - 1e-9), -1 + 1e-9)  # keep atanh finite
                tov[n][m_idx] = -2 * math.atanh(product)

    return best_bits, min_errors
