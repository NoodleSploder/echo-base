"""Built-in "starter" receiver profiles for common bands.

Not stored in the database -- unlike user-created `ReceiverProfile`
rows, these are a static, read-only catalog every user sees, one click
away from becoming a real (editable, deletable) profile via the
existing `POST /api/receiver-profiles` endpoint. All frequencies are
within an RTL2832U/R820T's tunable range (~24MHz-1.7GHz) so every entry
here is something a user with just an RTL-SDR can actually tune to and
listen to/decode, not an aspirational placeholder.

`decoder` matches the values already used by `ReceiverCard`'s
Decode APRS/SAME buttons ("aprs"/"same") where applicable, so a future
"apply profile" UI could auto-enable the right decoder -- not wired up
yet, just carried through in case (`ReceiverProfile.decoder` already
exists in the schema for user-created profiles too).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SuggestedProfile:
    id: str
    name: str
    frequency_hz: int
    gain: str | None
    decoder: str | None
    description: str


SUGGESTED_PROFILES: list[SuggestedProfile] = [
    SuggestedProfile(
        id="fm-broadcast",
        name="FM Broadcast",
        frequency_hz=100_300_000,
        gain="auto",
        decoder=None,
        description="Commercial FM radio -- tune to a strong local station.",
    ),
    SuggestedProfile(
        id="noaa-weather-radio",
        name="NOAA Weather Radio",
        frequency_hz=162_400_000,
        gain="auto",
        decoder="same",
        description="US NOAA Weather Radio (channel WX3) -- SAME alert decoding available.",
    ),
    SuggestedProfile(
        id="aprs-2m",
        name="APRS (2m Packet)",
        frequency_hz=144_390_000,
        gain="auto",
        decoder="aprs",
        description="North American APRS frequency -- AFSK1200/AX.25 decoding available.",
    ),
    SuggestedProfile(
        id="marine-vhf-ch16",
        name="Marine VHF Channel 16",
        frequency_hz=156_800_000,
        gain="auto",
        decoder=None,
        description="International marine distress/calling channel (voice, AM/NFM).",
    ),
    SuggestedProfile(
        id="amateur-2m-calling",
        name="2m Amateur Calling Frequency",
        frequency_hz=146_520_000,
        gain="auto",
        decoder=None,
        description="North American 2m FM simplex calling frequency.",
    ),
    SuggestedProfile(
        id="airband-guard",
        name="Airband Guard",
        frequency_hz=121_500_000,
        gain="auto",
        decoder=None,
        description="Civil aviation emergency/guard frequency (AM voice).",
    ),
    SuggestedProfile(
        id="ads-b",
        name="Aircraft ADS-B",
        frequency_hz=1_090_000_000,
        gain="auto",
        decoder=None,
        description="1090MHz Mode S extended squitter -- spectrum/IQ only, no decoder built yet.",
    ),
]
